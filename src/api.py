from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional
import json
import asyncio
from src.agent import AIAgent, MultiModalAgent, ToolUsingAgent
from src.config import settings

app = FastAPI(title="AI Agents API", version="0.1.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Pydantic models
class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    provider: str = "openai"
    model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None

class ChatResponse(BaseModel):
    conversation_id: str
    message: str
    response: str
    timestamp: str

class ConversationResponse(BaseModel):
    conversation_id: str
    messages: list

# Global agent instances
agents = {}
active_connections = {}

@app.get("/", response_class=HTMLResponse)
async def get_chat_interface():
    """Serve the chat interface"""
    with open("templates/chat.html", "r") as f:
        return HTMLResponse(content=f.read())

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Handle chat requests"""
    try:
        # Get or create agent
        agent_key = f"{request.provider}_{request.model or 'default'}"
        if agent_key not in agents:
            agents[agent_key] = AIAgent(provider_type=request.provider)
        
        agent = agents[agent_key]
        
        # Start new conversation if needed
        if not request.conversation_id:
            conversation_id = await agent.start_conversation()
        else:
            conversation_id = request.conversation_id
        
        # Generate response
        kwargs = {}
        if request.model:
            kwargs["model"] = request.model
        if request.temperature is not None:
            kwargs["temperature"] = request.temperature
        if request.max_tokens is not None:
            kwargs["max_tokens"] = request.max_tokens
        
        response = await agent.chat(conversation_id, request.message, **kwargs)
        
        return ChatResponse(**response)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/conversation/{conversation_id}")
async def get_conversation(conversation_id: str):
    """Get conversation history"""
    try:
        # Find the agent that has this conversation
        for agent in agents.values():
            history = await agent.get_conversation_history(conversation_id)
            if history:
                return ConversationResponse(
                    conversation_id=conversation_id,
                    messages=history
                )
        
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/conversation/{conversation_id}")
async def clear_conversation(conversation_id: str):
    """Clear conversation history"""
    try:
        # Find and clear the conversation
        for agent in agents.values():
            await agent.clear_conversation(conversation_id)
        
        return {"message": "Conversation cleared"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws/{conversation_id}")
async def websocket_endpoint(websocket: WebSocket, conversation_id: str):
    """WebSocket endpoint for streaming chat"""
    await websocket.accept()
    
    try:
        # Store connection
        active_connections[conversation_id] = websocket
        
        while True:
            # Receive message
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Get agent
            provider = message_data.get("provider", "openai")
            agent_key = f"{provider}_{message_data.get('model', 'default')}"
            
            if agent_key not in agents:
                agents[agent_key] = AIAgent(provider_type=provider)
            
            agent = agents[agent_key]
            
            # Start conversation if needed
            history = await agent.get_conversation_history(conversation_id)
            if not history:
                await agent.start_conversation()
                # Update conversation ID
                new_conv_id = await agent.start_conversation()
                del active_connections[conversation_id]
                active_connections[new_conv_id] = websocket
                conversation_id = new_conv_id
            
            # Stream response
            kwargs = {}
            if message_data.get("model"):
                kwargs["model"] = message_data["model"]
            if message_data.get("temperature") is not None:
                kwargs["temperature"] = message_data["temperature"]
            if message_data.get("max_tokens") is not None:
                kwargs["max_tokens"] = message_data["max_tokens"]
            
            async for chunk in agent.stream_chat(conversation_id, message_data["message"], **kwargs):
                await websocket.send_text(json.dumps({
                    "type": "chunk",
                    "content": chunk
                }))
            
            # Send completion signal
            await websocket.send_text(json.dumps({
                "type": "complete"
            }))
    
    except WebSocketDisconnect:
        # Remove connection
        if conversation_id in active_connections:
            del active_connections[conversation_id]
    
    except Exception as e:
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": str(e)
        }))

@app.get("/api/models")
async def get_available_models():
    """Get list of available models"""
    return {
        "providers": {
            "openai": ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo-preview"],
            "anthropic": ["claude-3-sonnet-20240229", "claude-3-opus-20240229"],
            "huggingface": ["microsoft/DialoGPT-medium", "microsoft/DialoGPT-large"]
        }
    }

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": "0.1.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.host, port=settings.port)
