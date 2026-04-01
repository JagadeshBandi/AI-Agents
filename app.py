#!/usr/bin/env python3
"""
AI Agents - Web Application with Advanced Automation
No command line interface - fully automated GUI system
"""

import sys
import os
import asyncio
from pathlib import Path

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.advanced_api import app
from src.config import settings
from src.automation import AutomationEngine
import uvicorn


class AutomatedWebApp:
    """Web application with integrated automation"""
    
    def __init__(self):
        self.automation_engine = AutomationEngine()
    
    async def initialize_and_start(self):
        """Initialize system and start web server"""
        print("Initializing AI Agents Web Application...")
        
        # Create directories
        self._create_directories()
        
        # Setup environment
        self._setup_environment()
        
        # Start automation engine
        await self.automation_engine.start_automation()
        
        # Start web server
        print(f"Starting web server on {settings.host}:{settings.port}")
        print(f"Access the application at: http://{settings.host}:{settings.port}")
        
        config = uvicorn.Config(
            app,
            host=settings.host,
            port=settings.port,
            log_level="info",
            access_log=True
        )
        
        server = uvicorn.Server(config)
        await server.serve()
    
    def _create_directories(self):
        """Create necessary directories"""
        directories = [
            "data/training",
            "data/conversations", 
            "models",
            "logs",
            "cache"
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
        print("Directories created successfully")
    
    def _setup_environment(self):
        """Setup environment configuration"""
        # Check for .env file
        env_file = Path(".env")
        env_example = Path(".env.example")
        
        if not env_file.exists() and env_example.exists():
            import shutil
            shutil.copy(env_example, env_file)
            print("Environment file created from template")
        
        print("Environment setup complete")


async def main():
    """Main application entry point"""
    web_app = AutomatedWebApp()
    await web_app.initialize_and_start()


if __name__ == "__main__":
    asyncio.run(main())
