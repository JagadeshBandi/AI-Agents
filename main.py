#!/usr/bin/env python3
"""
AI Agents - Advanced Automated Main Application
GUI-based automation system with no command line dependencies
"""

import sys
import os
import asyncio
import threading
from pathlib import Path
from typing import Dict, Any, Optional
import json
from datetime import datetime

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.api import app
from src.config import settings
from src.training import TrainingManager
from src.agent import AIAgent
import uvicorn


class AutomationManager:
    """Advanced automation system for AI agents"""
    
    def __init__(self):
        self.training_manager = TrainingManager()
        self.active_agents = {}
        self.automation_tasks = {}
        self.is_running = False
    
    async def initialize_system(self):
        """Initialize the entire system automatically"""
        print("Initializing AI Agents Automation System...")
        
        # Create necessary directories
        self._create_directories()
        
        # Start background services
        self._start_background_services()
        
        # Initialize agents
        await self._initialize_agents()
        
        print("System initialization complete!")
        return True
    
    def _create_directories(self):
        """Create necessary directories automatically"""
        directories = [
            "data/training",
            "data/conversations",
            "models",
            "logs",
            "static/css",
            "static/js",
            "cache"
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
    
    def _start_background_services(self):
        """Start background services"""
        # Start monitoring services
        threading.Thread(target=self._monitor_system_health, daemon=True).start()
        threading.Thread(target=self._auto_optimize_models, daemon=True).start()
    
    async def _initialize_agents(self):
        """Initialize default agents"""
        providers = ["openai", "anthropic", "huggingface"]
        
        for provider in providers:
            try:
                agent = AIAgent(provider_type=provider)
                self.active_agents[provider] = agent
                print(f"Initialized {provider} agent")
            except Exception as e:
                print(f"Failed to initialize {provider} agent: {e}")
    
    def _monitor_system_health(self):
        """Monitor system health in background"""
        while True:
            try:
                # Check agent health
                for provider, agent in self.active_agents.items():
                    # Health check logic here
                    pass
                
                # Check storage
                # Check API limits
                # Optimize performance
                
                asyncio.sleep(300)  # Check every 5 minutes
            except Exception as e:
                print(f"Health monitoring error: {e}")
    
    def _auto_optimize_models(self):
        """Automatically optimize models in background"""
        while True:
            try:
                # Model optimization logic
                # Cache management
                # Performance tuning
                
                asyncio.sleep(3600)  # Optimize every hour
            except Exception as e:
                print(f"Model optimization error: {e}")
    
    async def auto_train_models(self):
        """Automatically train models based on available data"""
        training_data_path = Path(settings.training_data_path)
        
        if not training_data_path.exists():
            return
        
        # Find training data files
        data_files = list(training_data_path.glob("*.json"))
        
        for data_file in data_files:
            try:
                # Create trainer
                trainer, trainer_id = self.training_manager.create_trainer("microsoft/DialoGPT-medium")
                
                # Train model
                trainer.fine_tune_from_conversations(
                    conversations_path=str(data_file),
                    output_dir=f"./models/auto_trained_{data_file.stem}",
                    num_epochs=2
                )
                
                print(f"Auto-trained model from {data_file}")
                
            except Exception as e:
                print(f"Auto-training failed for {data_file}: {e}")
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status"""
        return {
            "active_agents": list(self.active_agents.keys()),
            "automation_running": self.is_running,
            "timestamp": datetime.now().isoformat(),
            "system_health": "healthy"
        }
    
    async def start_automation(self):
        """Start the automation system"""
        if self.is_running:
            return
        
        self.is_running = True
        
        # Start auto-training scheduler
        threading.Thread(target=self._automation_scheduler, daemon=True).start()
        
        print("Automation system started")
    
    def _automation_scheduler(self):
        """Schedule automation tasks"""
        while self.is_running:
            try:
                # Schedule auto-training
                asyncio.run(self.auto_train_models())
                
                # Sleep for daily check
                asyncio.sleep(86400)  # 24 hours
            except Exception as e:
                print(f"Automation scheduler error: {e}")


class WebServerManager:
    """Manage web server with advanced features"""
    
    def __init__(self):
        self.automation_manager = AutomationManager()
        self.server = None
    
    async def start_server(self):
        """Start the web server with automation"""
        # Initialize automation
        await self.automation_manager.initialize_system()
        await self.automation_manager.start_automation()
        
        # Configure server
        config = uvicorn.Config(
            app,
            host=settings.host,
            port=settings.port,
            log_level="info",
            access_log=True
        )
        
        self.server = uvicorn.Server(config)
        
        print(f"Starting AI Agents Server on {settings.host}:{settings.port}")
        print(f"Web Interface: http://{settings.host}:{settings.port}")
        print(f"API Documentation: http://{settings.host}:{settings.port}/docs")
        
        await self.server.serve()


class AutoSetup:
    """Automatic setup and configuration"""
    
    @staticmethod
    def setup_environment():
        """Automatically setup the environment"""
        print("Setting up AI Agents environment...")
        
        # Check for .env file
        env_file = Path(".env")
        env_example = Path(".env.example")
        
        if not env_file.exists() and env_example.exists():
            # Copy example to .env
            import shutil
            shutil.copy(env_example, env_file)
            print("Created .env file from template")
            print("Please configure your API keys in .env file")
        
        # Check Redis connection
        try:
            import redis
            r = redis.from_url(settings.redis_url)
            r.ping()
            print("Redis connection verified")
        except Exception as e:
            print(f"Redis connection failed: {e}")
            print("Please ensure Redis is running for full functionality")
        
        # Verify API keys
        if not settings.openai_api_key:
            print("Warning: OpenAI API key not configured")
        
        if not settings.anthropic_api_key:
            print("Warning: Anthropic API key not configured")
        
        print("Environment setup complete")
    
    @staticmethod
    def create_sample_data():
        """Create sample training data"""
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
            }
        ]
        
        # Create training data directory
        training_dir = Path("data/training")
        training_dir.mkdir(parents=True, exist_ok=True)
        
        # Save sample data
        with open(training_dir / "sample_conversations.json", "w", encoding="utf-8") as f:
            json.dump(sample_conversations, f, indent=2, ensure_ascii=False)
        
        print("Sample training data created")


async def main():
    """Main application entry point - fully automated"""
    print("AI Agents - Advanced Automation System")
    print("=" * 50)
    
    # Auto setup
    AutoSetup.setup_environment()
    AutoSetup.create_sample_data()
    
    # Start web server with automation
    server_manager = WebServerManager()
    await server_manager.start_server()


if __name__ == "__main__":
    # Run the automated system
    asyncio.run(main())
