"""Base classes for all agent types"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from enum import Enum
from dataclasses import dataclass, field
import asyncio
from datetime import datetime

class AgentType(Enum):
    """Supported agent types"""
    OPENHANDS = "openhands"
    CREWAI = "crewai"
    AUTOGPT = "autogpt"
    STRIX = "strix"
    MONEYPRINTER = "moneyprinter"

@dataclass
class AgentConfig:
    """Configuration for any agent"""
    agent_type: AgentType
    api_key: Optional[str] = None
    model: str = "gpt-4"
    max_iterations: int = 10
    verbose: bool = False
    custom_params: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AgentResult:
    """Standardized result from any agent"""
    success: bool
    output: Any
    error: Optional[str] = None
    execution_time: float = 0.0
    agent_type: Optional[AgentType] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

class BaseAgent(ABC):
    """Abstract base class for all agents"""
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self._start_time: Optional[datetime] = None
        
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the agent with its dependencies"""
        pass
    
    @abstractmethod
    async def execute(self, task: str, **kwargs) -> AgentResult:
        """Execute a task with this agent"""
        pass
    
    @abstractmethod
    async def shutdown(self) -> bool:
        """Clean shutdown of the agent"""
        pass
    
    async def _execute_with_timing(self, task: str, **kwargs) -> AgentResult:
        """Wrapper to time execution"""
        start = datetime.now()
        try:
            result = await self.execute(task, **kwargs)
            result.execution_time = (datetime.now() - start).total_seconds()
            result.agent_type = self.config.agent_type
            return result
        except Exception as e:
            return AgentResult(
                success=False,
                output=None,
                error=str(e),
                execution_time=(datetime.now() - start).total_seconds(),
                agent_type=self.config.agent_type
            )
