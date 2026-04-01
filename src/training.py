import os
import json
import torch
from typing import Dict, List, Optional, Any
from datasets import Dataset, load_dataset
from transformers import (
    AutoTokenizer, 
    AutoModelForCausalLM, 
    TrainingArguments, 
    Trainer,
    DataCollatorForLanguageModeling
)
from peft import LoraConfig, get_peft_model, TaskType
from src.config import settings


class DataProcessor:
    """Process and prepare training data"""
    
    def __init__(self):
        self.tokenizer = None
    
    def set_tokenizer(self, tokenizer):
        """Set the tokenizer for data processing"""
        self.tokenizer = tokenizer
    
    def load_conversation_data(self, data_path: str) -> Dataset:
        """Load conversation data from JSON file"""
        with open(data_path, 'r', encoding='utf-8') as f:
            conversations = json.load(f)
        
        # Convert to dataset format
        formatted_data = []
        for conv in conversations:
            if isinstance(conv, dict) and 'messages' in conv:
                # OpenAI chat format
                formatted_text = self._format_conversation(conv['messages'])
            elif isinstance(conv, list):
                # Simple message list
                formatted_text = self._format_conversation(conv)
            else:
                continue
            
            formatted_data.append({"text": formatted_text})
        
        return Dataset.from_list(formatted_data)
    
    def load_dataset_from_huggingface(self, dataset_name: str, split: str = "train") -> Dataset:
        """Load dataset from Hugging Face"""
        try:
            dataset = load_dataset(dataset_name, split=split)
            return dataset
        except Exception as e:
            print(f"Error loading dataset {dataset_name}: {e}")
            return None
    
    def _format_conversation(self, messages: List[Dict[str, str]]) -> str:
        """Format conversation messages into training text"""
        formatted_text = ""
        
        for message in messages:
            role = message.get("role", "")
            content = message.get("content", "")
            
            if role == "system":
                formatted_text += f"System: {content}\n"
            elif role == "user":
                formatted_text += f"Human: {content}\n"
            elif role == "assistant":
                formatted_text += f"Assistant: {content}\n"
        
        return formatted_text
    
    def tokenize_dataset(self, dataset: Dataset, max_length: int = 512) -> Dataset:
        """Tokenize the dataset"""
        def tokenize_function(examples):
            return self.tokenizer(
                examples["text"],
                truncation=True,
                padding=False,
                max_length=max_length,
                return_overflowing_tokens=False,
            )
        
        tokenized_dataset = dataset.map(tokenize_function, batched=True)
        return tokenized_dataset


class ModelTrainer:
    """Handle model training and fine-tuning"""
    
    def __init__(self, model_name: str = "microsoft/DialoGPT-medium"):
        self.model_name = model_name
        self.model = None
        self.tokenizer = None
        self.data_processor = DataProcessor()
        self._load_model()
    
    def _load_model(self):
        """Load the base model and tokenizer"""
        print(f"Loading model: {self.model_name}")
        
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            torch_dtype=torch.float16 if settings.use_gpu else torch.float32,
            device_map="auto" if settings.use_gpu else None
        )
        
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        
        self.data_processor.set_tokenizer(self.tokenizer)
    
    def prepare_for_training(self, use_lora: bool = True):
        """Prepare model for training with LoRA if specified"""
        if use_lora:
            lora_config = LoraConfig(
                task_type=TaskType.CAUSAL_LM,
                r=16,  # rank
                lora_alpha=32,
                lora_dropout=0.1,
                target_modules=["q_proj", "v_proj", "k_proj", "o_proj"]
            )
            
            self.model = get_peft_model(self.model, lora_config)
            self.model.print_trainable_parameters()
    
    def train_model(
        self,
        train_dataset: Dataset,
        eval_dataset: Optional[Dataset] = None,
        output_dir: str = None,
        num_epochs: int = 3,
        batch_size: int = 4,
        learning_rate: float = 5e-5,
        save_steps: int = 500
    ):
        """Train the model"""
        if output_dir is None:
            output_dir = settings.model_output_path
        
        os.makedirs(output_dir, exist_ok=True)
        
        training_args = TrainingArguments(
            output_dir=output_dir,
            num_train_epochs=num_epochs,
            per_device_train_batch_size=batch_size,
            per_device_eval_batch_size=batch_size,
            learning_rate=learning_rate,
            weight_decay=0.01,
            logging_dir=f"{output_dir}/logs",
            logging_steps=10,
            save_steps=save_steps,
            save_total_limit=3,
            evaluation_strategy="steps" if eval_dataset else "no",
            eval_steps=save_steps if eval_dataset else None,
            load_best_model_at_end=True if eval_dataset else False,
            fp16=settings.use_gpu,
            dataloader_pin_memory=False,
            remove_unused_columns=False,
        )
        
        data_collator = DataCollatorForLanguageModeling(
            tokenizer=self.tokenizer,
            mlm=False,
        )
        
        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=eval_dataset,
            data_collator=data_collator,
        )
        
        print("Starting training...")
        trainer.train()
        
        # Save the final model
        trainer.save_model()
        self.tokenizer.save_pretrained(output_dir)
        
        print(f"Model saved to {output_dir}")
        return trainer
    
    def fine_tune_from_conversations(
        self,
        conversations_path: str,
        output_dir: str = None,
        **training_kwargs
    ):
        """Fine-tune model from conversation data"""
        # Load and process data
        dataset = self.data_processor.load_conversation_data(conversations_path)
        tokenized_dataset = self.data_processor.tokenize_dataset(dataset)
        
        # Split dataset
        train_test_split = tokenized_dataset.train_test_split(test_size=0.1)
        train_dataset = train_test_split["train"]
        eval_dataset = train_test_split["test"]
        
        # Prepare model for training
        self.prepare_for_training(use_lora=True)
        
        # Train model
        return self.train_model(
            train_dataset=train_dataset,
            eval_dataset=eval_dataset,
            output_dir=output_dir,
            **training_kwargs
        )
    
    def fine_tune_from_dataset(
        self,
        dataset_name: str,
        output_dir: str = None,
        **training_kwargs
    ):
        """Fine-tune model from Hugging Face dataset"""
        # Load dataset
        dataset = self.data_processor.load_dataset_from_huggingface(dataset_name)
        if dataset is None:
            raise ValueError(f"Could not load dataset: {dataset_name}")
        
        # Process dataset
        if "text" not in dataset.column_names:
            # Try to format as conversations
            if "messages" in dataset.column_names:
                dataset = dataset.map(lambda x: {"text": self.data_processor._format_conversation(x["messages"])})
            else:
                raise ValueError("Dataset must have 'text' or 'messages' column")
        
        tokenized_dataset = self.data_processor.tokenize_dataset(dataset)
        
        # Split dataset
        train_test_split = tokenized_dataset.train_test_split(test_size=0.1)
        train_dataset = train_test_split["train"]
        eval_dataset = train_test_split["test"]
        
        # Prepare model for training
        self.prepare_for_training(use_lora=True)
        
        # Train model
        return self.train_model(
            train_dataset=train_dataset,
            eval_dataset=eval_dataset,
            output_dir=output_dir,
            **training_kwargs
        )


class TrainingManager:
    """Manage training operations and configuration"""
    
    def __init__(self):
        self.trainers = {}
    
    def create_trainer(self, model_name: str, trainer_id: str = None) -> ModelTrainer:
        """Create a new trainer instance"""
        if trainer_id is None:
            trainer_id = f"trainer_{len(self.trainers)}"
        
        trainer = ModelTrainer(model_name)
        self.trainers[trainer_id] = trainer
        return trainer, trainer_id
    
    def get_trainer(self, trainer_id: str) -> ModelTrainer:
        """Get existing trainer instance"""
        if trainer_id not in self.trainers:
            raise ValueError(f"Trainer {trainer_id} not found")
        return self.trainers[trainer_id]
    
    def list_available_datasets(self) -> Dict[str, List[str]]:
        """List available training datasets"""
        return {
            "conversation_datasets": [
                "Anthropic/hh-rlhf",
                "OpenAI/webgpt_comparisons",
                "Dahoas/full-hh-rlhf-dataset"
            ],
            "instruction_datasets": [
                "databricks/databricks-dolly-15k",
                "tatsu-lab/alpaca",
                "openai/summarize_from_feedback"
            ],
            "custom_data": [
                "Provide your own JSON file with conversation data"
            ]
        }
    
    def create_sample_training_data(self, output_path: str):
        """Create sample training data for testing"""
        sample_conversations = [
            {
                "messages": [
                    {"role": "system", "content": "You are a helpful AI assistant."},
                    {"role": "user", "content": "Hello! How are you?"},
                    {"role": "assistant", "content": "Hello! I'm doing well, thank you for asking. How can I help you today?"}
                ]
            },
            {
                "messages": [
                    {"role": "system", "content": "You are a helpful AI assistant."},
                    {"role": "user", "content": "What is the capital of France?"},
                    {"role": "assistant", "content": "The capital of France is Paris. It's known for its beautiful architecture, art museums, and the Eiffel Tower."}
                ]
            },
            {
                "messages": [
                    {"role": "system", "content": "You are a helpful AI assistant."},
                    {"role": "user", "content": "Can you help me understand Python programming?"},
                    {"role": "assistant", "content": "I'd be happy to help you with Python programming! Python is a versatile, high-level programming language known for its simple syntax and readability. What specific aspect of Python would you like to learn about?"}
                ]
            }
        ]
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(sample_conversations, f, indent=2, ensure_ascii=False)
        
        print(f"Sample training data created at {output_path}")


# Example usage functions
def quick_fine_tune_example():
    """Example of how to use the training system"""
    training_manager = TrainingManager()
    
    # Create sample data
    training_manager.create_sample_training_data(
        "./data/training/sample_conversations.json"
    )
    
    # Create trainer
    trainer, trainer_id = training_manager.create_trainer("microsoft/DialoGPT-medium")
    
    # Fine-tune with sample data
    trainer.fine_tune_from_conversations(
        conversations_path="./data/training/sample_conversations.json",
        output_dir="./models/fine_tuned_model",
        num_epochs=1,
        batch_size=2
    )
    
    print("Training completed!")


if __name__ == "__main__":
    quick_fine_tune_example()
