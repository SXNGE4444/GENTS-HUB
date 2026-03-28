"""crewAI adapter for the unified platform"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add crewAI submodule to path
CREWAI_PATH = Path(__file__).parent.parent.parent / "crewAI"
sys.path.insert(0, str(CREWAI_PATH))

from orchestrator.agent_base import BaseAgent, AgentConfig, AgentResult

class CrewAIAdapter(BaseAgent):
    """Adapter for crewAI framework"""
    
    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self.initialized = False
        
    async def initialize(self) -> bool:
        """Initialize crewAI"""
        try:
            print("Initializing crewAI...")
            self.initialized = True
            return True
        except Exception as e:
            print(f"crewAI initialization error: {e}")
            return False
    
    async def execute(self, task: str, **kwargs) -> AgentResult:
        """Create and run a crew based on the task"""
        if not self.initialized:
            return AgentResult(success=False, output=None, error="Agent not initialized")
        
        try:
            print(f"Executing with crewAI: {task[:100]}...")
            
            return AgentResult(
                success=True,
                output={
                    "message": f"crewAI would execute: {task}",
                    "agents_used": kwargs.get("agents", ["researcher", "writer"]),
                    "status": "simulated"
                }
            )
        except Exception as e:
            return AgentResult(success=False, output=None, error=str(e))
    
    async def shutdown(self) -> bool:
        """Clean shutdown"""
        self.initialized = False
        return True
