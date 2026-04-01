"""
Advanced API with integrated automation capabilities
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import asyncio
from datetime import datetime

from src.automation import AutomationEngine, IntelligentConversationRouter
from src.agent import AIAgent
from src.config import settings


class AdvancedAPI:
    """Advanced API with automation features"""
    
    def __init__(self):
        self.app = FastAPI(title="AI Agents Advanced API", version="2.0.0")
        self.automation_engine = AutomationEngine()
        self.router = IntelligentConversationRouter()
        self.agents = {}
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup API routes"""
        
        @self.app.get("/", response_class=HTMLResponse)
        async def get_dashboard():
            """Advanced automation dashboard"""
            return self._generate_dashboard_html()
        
        @self.app.post("/api/intelligent-chat")
        async def intelligent_chat(request: Dict[str, Any]):
            """Intelligent chat with automatic routing"""
            message = request.get("message")
            if not message:
                raise HTTPException(status_code=400, detail="Message is required")
            
            # Analyze message for optimal routing
            analysis = self.router.analyze_conversation(message)
            recommended_provider = analysis["recommended_provider"]
            
            # Get or create agent
            if recommended_provider not in self.agents:
                self.agents[recommended_provider] = AIAgent(provider_type=recommended_provider)
            
            agent = self.agents[recommended_provider]
            
            # Start conversation
            conversation_id = await agent.start_conversation()
            
            # Get response
            response = await agent.chat(
                conversation_id, 
                message,
                temperature=request.get("temperature", 0.7),
                max_tokens=request.get("max_tokens", 1000)
            )
            
            # Add routing analysis to response
            response["routing_analysis"] = analysis
            response["provider_used"] = recommended_provider
            
            return response
        
        @self.app.get("/api/automation/status")
        async def get_automation_status():
            """Get automation system status"""
            return self.automation_engine.get_automation_status()
        
        @self.app.post("/api/automation/optimize")
        async def trigger_optimization(background_tasks: BackgroundTasks):
            """Trigger immediate optimization"""
            background_tasks.add_task(
                self.automation_engine.model_manager.auto_optimize_models
            )
            return {"message": "Optimization started"}
        
        @self.app.get("/api/models/performance")
        async def get_model_performance():
            """Get model performance metrics"""
            return await self.automation_engine.model_manager._analyze_model_performance()
        
        @self.app.post("/api/conversations/analyze")
        async def analyze_conversations(request: Dict[str, Any]):
            """Analyze conversation data"""
            conversations = request.get("conversations", [])
            analysis = await self.automation_engine.conversation_analyzer.analyze_conversations(
                conversations
            )
            return analysis
        
        @self.app.get("/api/system/health")
        async def system_health():
            """Comprehensive system health check"""
            health = {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "automation": self.automation_engine.get_automation_status(),
                "agents": list(self.agents.keys()),
                "services": {
                    "api": "running",
                    "automation": "running" if self.automation_engine.running else "stopped"
                }
            }
            return health
        
        @self.app.post("/api/auto-train")
        async def auto_train(background_tasks: BackgroundTasks):
            """Trigger automatic training"""
            background_tasks.add_task(
                self.automation_engine.training_manager.create_sample_training_data,
                "./data/training/auto_generated.json"
            )
            return {"message": "Auto-training initiated"}
    
    def _generate_dashboard_html(self) -> str:
        """Generate advanced dashboard HTML"""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Agents - Advanced Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body class="bg-gray-50">
    <div class="min-h-screen">
        <!-- Header -->
        <header class="bg-white shadow-sm border-b">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div class="flex justify-between items-center py-4">
                    <h1 class="text-2xl font-bold text-gray-900">AI Agents Dashboard</h1>
                    <div class="flex items-center space-x-4">
                        <span id="status" class="px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800">
                            System Active
                        </span>
                    </div>
                </div>
            </div>
        </header>

        <!-- Main Content -->
        <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <!-- Stats Grid -->
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                <div class="bg-white rounded-lg shadow p-6">
                    <div class="flex items-center">
                        <div class="flex-shrink-0">
                            <div class="w-8 h-8 bg-blue-500 rounded-md flex items-center justify-center">
                                <span class="text-white font-medium">AI</span>
                            </div>
                        </div>
                        <div class="ml-4">
                            <p class="text-sm font-medium text-gray-600">Active Agents</p>
                            <p id="active-agents" class="text-2xl font-bold text-gray-900">3</p>
                        </div>
                    </div>
                </div>

                <div class="bg-white rounded-lg shadow p-6">
                    <div class="flex items-center">
                        <div class="flex-shrink-0">
                            <div class="w-8 h-8 bg-green-500 rounded-md flex items-center justify-center">
                                <span class="text-white font-medium">AT</span>
                            </div>
                        </div>
                        <div class="ml-4">
                            <p class="text-sm font-medium text-gray-600">Automation Tasks</p>
                            <p id="automation-tasks" class="text-2xl font-bold text-gray-900">0</p>
                        </div>
                    </div>
                </div>

                <div class="bg-white rounded-lg shadow p-6">
                    <div class="flex items-center">
                        <div class="flex-shrink-0">
                            <div class="w-8 h-8 bg-purple-500 rounded-md flex items-center justify-center">
                                <span class="text-white font-medium">PR</span>
                            </div>
                        </div>
                        <div class="ml-4">
                            <p class="text-sm font-medium text-gray-600">Performance Score</p>
                            <p id="performance-score" class="text-2xl font-bold text-gray-900">95%</p>
                        </div>
                    </div>
                </div>

                <div class="bg-white rounded-lg shadow p-6">
                    <div class="flex items-center">
                        <div class="flex-shrink-0">
                            <div class="w-8 h-8 bg-orange-500 rounded-md flex items-center justify-center">
                                <span class="text-white font-medium">CH</span>
                            </div>
                        </div>
                        <div class="ml-4">
                            <p class="text-sm font-medium text-gray-600">Conversations</p>
                            <p id="conversation-count" class="text-2xl font-bold text-gray-900">0</p>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Chat Interface -->
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
                <div class="bg-white rounded-lg shadow">
                    <div class="px-6 py-4 border-b">
                        <h2 class="text-lg font-medium text-gray-900">Intelligent Chat</h2>
                        <p class="text-sm text-gray-600">AI automatically routes to optimal model</p>
                    </div>
                    <div class="p-6">
                        <div id="chat-messages" class="h-64 overflow-y-auto mb-4 p-4 bg-gray-50 rounded-lg">
                            <div class="text-center text-gray-500">
                                Start a conversation to see intelligent routing in action
                            </div>
                        </div>
                        <div class="flex space-x-2">
                            <input 
                                type="text" 
                                id="chat-input" 
                                placeholder="Type your message..."
                                class="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                            >
                            <button 
                                onclick="sendMessage()"
                                class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                            >
                                Send
                            </button>
                        </div>
                        <div id="routing-info" class="mt-2 text-sm text-gray-600"></div>
                    </div>
                </div>

                <!-- Automation Controls -->
                <div class="bg-white rounded-lg shadow">
                    <div class="px-6 py-4 border-b">
                        <h2 class="text-lg font-medium text-gray-900">Automation Controls</h2>
                        <p class="text-sm text-gray-600">Manage automated tasks and optimization</p>
                    </div>
                    <div class="p-6">
                        <div class="space-y-4">
                            <button 
                                onclick="triggerOptimization()"
                                class="w-full px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
                            >
                                Trigger Optimization
                            </button>
                            <button 
                                onclick="triggerAutoTrain()"
                                class="w-full px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
                            >
                                Start Auto-Training
                            </button>
                            <button 
                                onclick="refreshStatus()"
                                class="w-full px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
                            >
                                Refresh Status
                            </button>
                        </div>
                        
                        <div class="mt-6">
                            <h3 class="text-sm font-medium text-gray-900 mb-2">System Status</h3>
                            <div id="system-status" class="text-sm text-gray-600">
                                Loading...
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Performance Charts -->
            <div class="bg-white rounded-lg shadow">
                <div class="px-6 py-4 border-b">
                    <h2 class="text-lg font-medium text-gray-900">Performance Analytics</h2>
                </div>
                <div class="p-6">
                    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        <div>
                            <h3 class="text-sm font-medium text-gray-900 mb-2">Model Performance</h3>
                            <canvas id="performance-chart"></canvas>
                        </div>
                        <div>
                            <h3 class="text-sm font-medium text-gray-900 mb-2">Automation Activity</h3>
                            <canvas id="automation-chart"></canvas>
                        </div>
                    </div>
                </div>
            </div>
        </main>
    </div>

    <script>
        // Initialize dashboard
        async function initDashboard() {
            await refreshStatus();
            setInterval(refreshStatus, 30000); // Refresh every 30 seconds
            initCharts();
        }

        // Send intelligent chat message
        async function sendMessage() {
            const input = document.getElementById('chat-input');
            const message = input.value.trim();
            
            if (!message) return;
            
            // Add user message
            addChatMessage('user', message);
            input.value = '';
            
            try {
                const response = await fetch('/api/intelligent-chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({message: message})
                });
                
                const data = await response.json();
                
                // Add AI response
                addChatMessage('assistant', data.response);
                
                // Show routing info
                const routingInfo = document.getElementById('routing-info');
                routingInfo.innerHTML = `
                    Routed to <strong>${data.provider_used}</strong> 
                    (Complexity: ${data.routing_analysis.complexity}, 
                    Domain: ${data.routing_analysis.domain})
                `;
                
            } catch (error) {
                console.error('Chat error:', error);
                addChatMessage('assistant', 'Sorry, there was an error processing your message.');
            }
        }

        // Add chat message to interface
        function addChatMessage(role, content) {
            const messagesDiv = document.getElementById('chat-messages');
            const messageDiv = document.createElement('div');
            messageDiv.className = `mb-2 ${role === 'user' ? 'text-right' : 'text-left'}`;
            
            const bubble = document.createElement('div');
            bubble.className = `inline-block px-4 py-2 rounded-lg ${
                role === 'user' 
                    ? 'bg-blue-600 text-white' 
                    : 'bg-gray-200 text-gray-900'
            }`;
            bubble.textContent = content;
            
            messageDiv.appendChild(bubble);
            messagesDiv.appendChild(messageDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }

        // Trigger optimization
        async function triggerOptimization() {
            try {
                await fetch('/api/automation/optimize', {method: 'POST'});
                alert('Optimization triggered successfully');
            } catch (error) {
                alert('Error triggering optimization');
            }
        }

        // Trigger auto-training
        async function triggerAutoTrain() {
            try {
                await fetch('/api/auto-train', {method: 'POST'});
                alert('Auto-training initiated');
            } catch (error) {
                alert('Error starting auto-training');
            }
        }

        // Refresh system status
        async function refreshStatus() {
            try {
                const response = await fetch('/api/system/health');
                const status = await response.json();
                
                // Update status elements
                document.getElementById('active-agents').textContent = status.agents.length;
                document.getElementById('system-status').innerHTML = `
                    <div>Status: ${status.status}</div>
                    <div>Automation: ${status.services.automation}</div>
                    <div>Last updated: ${new Date(status.timestamp).toLocaleTimeString()}</div>
                `;
                
            } catch (error) {
                console.error('Status refresh error:', error);
            }
        }

        // Initialize charts
        function initCharts() {
            // Performance chart
            const perfCtx = document.getElementById('performance-chart').getContext('2d');
            new Chart(perfCtx, {
                type: 'bar',
                data: {
                    labels: ['OpenAI', 'Anthropic', 'HuggingFace'],
                    datasets: [{
                        label: 'Performance Score',
                        data: [85, 92, 78],
                        backgroundColor: ['blue', 'green', 'orange']
                    }]
                },
                options: {
                    responsive: true,
                    scales: {y: {beginAtZero: true, max: 100}}
                }
            });

            // Automation chart
            const autoCtx = document.getElementById('automation-chart').getContext('2d');
            new Chart(autoCtx, {
                type: 'line',
                data: {
                    labels: ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00'],
                    datasets: [{
                        label: 'Tasks Completed',
                        data: [5, 8, 12, 15, 18, 22],
                        borderColor: 'purple',
                        fill: false
                    }]
                },
                options: {
                    responsive: true,
                    scales: {y: {beginAtZero: true}}
                }
            });
        }

        // Initialize on load
        document.addEventListener('DOMContentLoaded', initDashboard);

        // Handle enter key in chat
        document.getElementById('chat-input').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
    </script>
</body>
</html>
        """


# Create advanced API instance
advanced_api = AdvancedAPI()
app = advanced_api.app
