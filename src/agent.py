import json
import uuid
from typing import Dict, List, Optional, Any, AsyncGenerator
from datetime import datetime
import redis.asyncio as redis
from src.llm_providers import LLMFactory, BaseLLMProvider
from src.config import settings


class ConversationManager:
    """Manages conversation history and context"""
    
    def __init__(self):
        self.redis_client = None
    
    async def _get_redis_client(self):
        if self.redis_client is None:
            self.redis_client = redis.from_url(settings.redis_url)
        return self.redis_client
    
    async def save_conversation(self, conversation_id: str, messages: List[Dict[str, str]]):
        """Save conversation to Redis"""
        client = await self._get_redis_client()
        await client.setex(
            f"conversation:{conversation_id}",
            86400,  # 24 hours expiry
            json.dumps(messages)
        )
    
    async def load_conversation(self, conversation_id: str) -> List[Dict[str, str]]:
        """Load conversation from Redis"""
        client = await self._get_redis_client()
        data = await client.get(f"conversation:{conversation_id}")
        if data:
            return json.loads(data)
        return []
    
    async def add_message(self, conversation_id: str, role: str, content: str):
        """Add a message to conversation"""
        messages = await self.load_conversation(conversation_id)
        messages.append({"role": role, "content": content})
        await self.save_conversation(conversation_id, messages)
        return messages


class AIAgent:
    """Main AI Agent class that handles conversations and LLM interactions"""
    
    def __init__(self, provider_type: str = "openai", **kwargs):
        self.provider = LLMFactory.create_provider(provider_type, **kwargs)
        self.conversation_manager = ConversationManager()
        self.system_prompt = """You are a helpful AI assistant. You are knowledgeable, friendly, and professional.
        You should provide accurate and helpful information while being conversational and engaging.
        If you don't know something, admit it honestly rather than making up information."""
    
    def set_system_prompt(self, prompt: str):
        """Set custom system prompt"""
        self.system_prompt = prompt
    
    async def start_conversation(self) -> str:
        """Start a new conversation and return conversation ID"""
        conversation_id = str(uuid.uuid4())
        # Initialize with system message
        await self.conversation_manager.add_message(
            conversation_id, "system", self.system_prompt
        )
        return conversation_id
    
    async def chat(self, conversation_id: str, message: str, **kwargs) -> Dict[str, Any]:
        """Send a message and get response"""
        # Add user message to conversation
        messages = await self.conversation_manager.add_message(
            conversation_id, "user", message
        )
        
        # Generate response
        response = await self.provider.generate_response(messages, **kwargs)
        
        # Add assistant response to conversation
        await self.conversation_manager.add_message(
            conversation_id, "assistant", response
        )
        
        return {
            "conversation_id": conversation_id,
            "message": message,
            "response": response,
            "timestamp": datetime.now().isoformat()
        }
    
    async def stream_chat(self, conversation_id: str, message: str, **kwargs) -> AsyncGenerator[str, None]:
        """Stream chat response"""
        # Add user message to conversation
        messages = await self.conversation_manager.add_message(
            conversation_id, "user", message
        )
        
        # Stream response
        full_response = ""
        async for chunk in self.provider.stream_response(messages, **kwargs):
            full_response += chunk
            yield chunk
        
        # Add complete assistant response to conversation
        await self.conversation_manager.add_message(
            conversation_id, "assistant", full_response
        )
    
    async def get_conversation_history(self, conversation_id: str) -> List[Dict[str, str]]:
        """Get conversation history"""
        return await self.conversation_manager.load_conversation(conversation_id)
    
    async def clear_conversation(self, conversation_id: str):
        """Clear conversation history"""
        client = await self.conversation_manager._get_redis_client()
        await client.delete(f"conversation:{conversation_id}")


class MultiModalAgent(AIAgent):
    """Extended AI Agent with multimodal capabilities"""
    
    def __init__(self, provider_type: str = "openai", **kwargs):
        super().__init__(provider_type, **kwargs)
        self.vision_models = {}
    
    async def analyze_image(self, conversation_id: str, image_path: str, question: str) -> str:
        """Analyze an image with the AI"""
        # This would integrate with vision models like GPT-4V
        # For now, return a placeholder
        return f"I can see an image at {image_path}. You asked: {question}. Image analysis not yet implemented."
    
    async def transcribe_audio(self, audio_path: str) -> str:
        """Transcribe audio to text"""
        # This would integrate with speech-to-text models
        return "Audio transcription not yet implemented."
    
    async def generate_speech(self, text: str) -> bytes:
        """Convert text to speech"""
        # This would integrate with text-to-speech models
        return b"Speech generation not yet implemented."


class ToolUsingAgent(AIAgent):
    """AI Agent with tool-using capabilities"""
    
    def __init__(self, provider_type: str = "openai", **kwargs):
        super().__init__(provider_type, **kwargs)
        self.tools = {}
        self.tool_prompt = """You are an AI assistant with access to various tools.
        When you need to use a tool, format your response with the tool name and parameters.
        Available tools: {}"""
    
    def register_tool(self, name: str, func, description: str):
        """Register a tool that the agent can use"""
        self.tools[name] = {
            "func": func,
            "description": description
        }
    
    async def chat_with_tools(self, conversation_id: str, message: str, **kwargs) -> Dict[str, Any]:
        """Chat with tool-using capabilities"""
        # Update system prompt with available tools
        tool_list = "\n".join([f"- {name}: {info['description']}" for name, info in self.tools.items()])
        self.set_system_prompt(self.tool_prompt.format(tool_list))
        
        # Get initial response
        response = await self.chat(conversation_id, message, **kwargs)
        
        # Check if response contains tool calls (simplified)
        # In a real implementation, you'd parse structured tool calls
        for tool_name in self.tools:
            if f"use {tool_name}" in response["response"].lower():
                # Execute tool
                tool_result = await self.tools[tool_name]["func"]()
                # Send tool result back to AI
                follow_up = await self.chat(
                    conversation_id, 
                    f"Tool {tool_name} returned: {tool_result}. Please provide a response to the user.",
                    **kwargs
                )
                response["response"] = follow_up["response"]
                break
        
        return response
