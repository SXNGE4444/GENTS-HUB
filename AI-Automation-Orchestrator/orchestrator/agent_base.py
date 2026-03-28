"""Core agent system for AI Automation Orchestrator"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Callable
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
import logging
import json
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgentType(Enum):
    """Supported agent types"""
    OPENHANDS = "openhands"
    CREWAI = "crewai"
    AUTOGPT = "autogpt"
    STRIX = "strix"
    MONEYPRINTER = "moneyprinter"
    
    @classmethod
    def from_string(cls, name: str):
        for agent in cls:
            if agent.value == name.lower():
                return agent
        raise ValueError(f"Unknown agent type: {name}")

@dataclass
class AgentConfig:
    """Configuration for any agent"""
    agent_type: AgentType
    api_key: Optional[str] = None
    model: str = "gpt-4"
    max_iterations: int = 10
    timeout: int = 300
    verbose: bool = False
    temperature: float = 0.7
    custom_params: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_type": self.agent_type.value,
            "model": self.model,
            "max_iterations": self.max_iterations,
            "timeout": self.timeout,
            "temperature": self.temperature,
            **self.custom_params
        }

@dataclass
class AgentResult:
    """Standardized result from any agent"""
    success: bool
    output: Any
    error: Optional[str] = None
    execution_time: float = 0.0
    agent_type: Optional[AgentType] = None
    task: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "execution_time": self.execution_time,
            "agent_type": self.agent_type.value if self.agent_type else None,
            "task": self.task,
            "metadata": self.metadata
        }
    
    def __str__(self) -> str:
        if self.success:
            return f"✅ Success ({self.execution_time:.2f}s): {str(self.output)[:200]}"
        else:
            return f"❌ Failed: {self.error}"

class BaseAgent(ABC):
    """Abstract base class for all agents"""
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self._start_time: Optional[datetime] = None
        self._initialized = False
        self._current_task: Optional[str] = None
        
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
        self._current_task = task
        start = datetime.now()
        try:
            logger.info(f"Executing {self.config.agent_type.value}: {task[:100]}...")
            result = await self.execute(task, **kwargs)
            result.execution_time = (datetime.now() - start).total_seconds()
            result.agent_type = self.config.agent_type
            result.task = task
            logger.info(f"Completed in {result.execution_time:.2f}s")
            return result
        except Exception as e:
            logger.error(f"Error executing {self.config.agent_type.value}: {e}")
            return AgentResult(
                success=False,
                output=None,
                error=str(e),
                execution_time=(datetime.now() - start).total_seconds(),
                agent_type=self.config.agent_type,
                task=task
            )
        finally:
            self._current_task = None
    
    @property
    def is_initialized(self) -> bool:
        return self._initialized
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} type={self.config.agent_type.value} initialized={self._initialized}>"
