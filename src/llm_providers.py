from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
import openai
import anthropic
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import torch
from src.config import settings


class BaseLLMProvider(ABC):
    """Base class for all LLM providers"""
    
    @abstractmethod
    async def generate_response(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Generate a response from the LLM"""
        pass
    
    @abstractmethod
    async def stream_response(self, messages: List[Dict[str, str]], **kwargs):
        """Stream a response from the LLM"""
        pass


class OpenAIProvider(BaseLLMProvider):
    """OpenAI GPT provider"""
    
    def __init__(self):
        self.client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
    
    async def generate_response(self, messages: List[Dict[str, str]], **kwargs) -> str:
        response = await self.client.chat.completions.create(
            model=kwargs.get("model", settings.default_model),
            messages=messages,
            max_tokens=kwargs.get("max_tokens", settings.max_tokens),
            temperature=kwargs.get("temperature", settings.temperature)
        )
        return response.choices[0].message.content
    
    async def stream_response(self, messages: List[Dict[str, str]], **kwargs):
        stream = await self.client.chat.completions.create(
            model=kwargs.get("model", settings.default_model),
            messages=messages,
            max_tokens=kwargs.get("max_tokens", settings.max_tokens),
            temperature=kwargs.get("temperature", settings.temperature),
            stream=True
        )
        
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude provider"""
    
    def __init__(self):
        self.client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    
    async def generate_response(self, messages: List[Dict[str, str]], **kwargs) -> str:
        # Convert OpenAI format to Anthropic format
        system_message = ""
        formatted_messages = []
        
        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            elif msg["role"] == "user":
                formatted_messages.append({"role": "user", "content": msg["content"]})
            elif msg["role"] == "assistant":
                formatted_messages.append({"role": "assistant", "content": msg["content"]})
        
        response = await self.client.messages.create(
            model=kwargs.get("model", "claude-3-sonnet-20240229"),
            max_tokens=kwargs.get("max_tokens", settings.max_tokens),
            temperature=kwargs.get("temperature", settings.temperature),
            system=system_message,
            messages=formatted_messages
        )
        return response.content[0].text
    
    async def stream_response(self, messages: List[Dict[str, str]], **kwargs):
        # Convert OpenAI format to Anthropic format
        system_message = ""
        formatted_messages = []
        
        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            elif msg["role"] == "user":
                formatted_messages.append({"role": "user", "content": msg["content"]})
            elif msg["role"] == "assistant":
                formatted_messages.append({"role": "assistant", "content": msg["content"]})
        
        async with self.client.messages.stream(
            model=kwargs.get("model", "claude-3-sonnet-20240229"),
            max_tokens=kwargs.get("max_tokens", settings.max_tokens),
            temperature=kwargs.get("temperature", settings.temperature),
            system=system_message,
            messages=formatted_messages
        ) as stream:
            async for text in stream.text_stream:
                yield text


class HuggingFaceProvider(BaseLLMProvider):
    """Hugging Face local model provider"""
    
    def __init__(self, model_name: str = "microsoft/DialoGPT-medium"):
        self.model_name = model_name
        self.tokenizer = None
        self.model = None
        self.pipeline = None
        self._load_model()
    
    def _load_model(self):
        """Load the model and tokenizer"""
        device = "cuda" if settings.use_gpu and torch.cuda.is_available() else "cpu"
        
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForCausalLM.from_pretrained(self.model_name).to(device)
        
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        
        self.pipeline = pipeline(
            "text-generation",
            model=self.model,
            tokenizer=self.tokenizer,
            device=0 if device == "cuda" else -1,
            max_length=settings.max_tokens
        )
    
    async def generate_response(self, messages: List[Dict[str, str]], **kwargs) -> str:
        # Convert messages to a single prompt
        prompt = self._messages_to_prompt(messages)
        
        # Generate response
        response = self.pipeline(
            prompt,
            max_new_tokens=kwargs.get("max_tokens", 500),
            temperature=kwargs.get("temperature", settings.temperature),
            do_sample=True,
            pad_token_id=self.tokenizer.eos_token_id
        )
        
        # Extract only the new part of the response
        generated_text = response[0]["generated_text"]
        return generated_text[len(prompt):].strip()
    
    async def stream_response(self, messages: List[Dict[str, str]], **kwargs):
        # For simplicity, return the full response at once
        # In a real implementation, you'd implement proper streaming
        response = await self.generate_response(messages, **kwargs)
        for word in response.split():
            yield word + " "
    
    def _messages_to_prompt(self, messages: List[Dict[str, str]]) -> str:
        """Convert message list to a single prompt string"""
        prompt = ""
        for msg in messages:
            if msg["role"] == "system":
                prompt += f"System: {msg['content']}\n"
            elif msg["role"] == "user":
                prompt += f"Human: {msg['content']}\n"
            elif msg["role"] == "assistant":
                prompt += f"Assistant: {msg['content']}\n"
        
        prompt += "Assistant: "
        return prompt


class LLMFactory:
    """Factory class to create LLM providers"""
    
    @staticmethod
    def create_provider(provider_type: str, **kwargs) -> BaseLLMProvider:
        """Create an LLM provider based on type"""
        if provider_type.lower() == "openai":
            return OpenAIProvider()
        elif provider_type.lower() == "anthropic":
            return AnthropicProvider()
        elif provider_type.lower() == "huggingface":
            return HuggingFaceProvider(**kwargs)
        else:
            raise ValueError(f"Unsupported provider type: {provider_type}")
