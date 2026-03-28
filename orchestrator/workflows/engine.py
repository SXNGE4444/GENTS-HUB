"""Unified workflow engine that combines multiple agents"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
import yaml
from pathlib import Path

from orchestrator.agent_base import BaseAgent, AgentConfig, AgentType, AgentResult
from orchestrator.agents.openhands.adapter import OpenHandsAdapter
from orchestrator.agents.crewai.adapter import CrewAIAdapter

@dataclass
class WorkflowStep:
    """Single step in a workflow"""
    name: str
    agent_type: AgentType
    task: str
    depends_on: List[str] = field(default_factory=list)
    config: Dict[str, Any] = field(default_factory=dict)

class WorkflowEngine:
    """Orchestrates multi-agent workflows"""
    
    def __init__(self):
        self.agents: Dict[AgentType, BaseAgent] = {}
        self.results: Dict[str, AgentResult] = {}
        
    def register_agent(self, agent_type: AgentType, config: AgentConfig) -> BaseAgent:
        """Register an agent with the engine"""
        if agent_type == AgentType.OPENHANDS:
            agent = OpenHandsAdapter(config)
        elif agent_type == AgentType.CREWAI:
            agent = CrewAIAdapter(config)
        else:
            raise ValueError(f"Unsupported agent type: {agent_type}")
        
        self.agents[agent_type] = agent
        return agent
    
    async def initialize_all(self) -> bool:
        """Initialize all registered agents"""
        for agent_type, agent in self.agents.items():
            if not await agent.initialize():
                print(f"Failed to initialize {agent_type.value}")
                return False
        return True
    
    async def run_workflow(self, workflow_steps: List[WorkflowStep]) -> Dict[str, AgentResult]:
        """Execute a workflow with dependencies"""
        self.results = {}
        
        # Simple dependency resolution (topological order)
        remaining = list(workflow_steps)
        while remaining:
            progress = False
            for step in remaining[:]:
                # Check if dependencies are satisfied
                deps_met = all(dep in self.results for dep in step.depends_on)
                
                if deps_met:
                    # Execute this step
                    agent = self.agents.get(step.agent_type)
                    if not agent:
                        self.results[step.name] = AgentResult(
                            success=False,
                            output=None,
                            error=f"Agent {step.agent_type} not registered"
                        )
                    else:
                        self.results[step.name] = await agent._execute_with_timing(
                            step.task, **step.config
                        )
                    
                    remaining.remove(step)
                    progress = True
            
            if not progress:
                # Circular dependency
                for step in remaining:
                    self.results[step.name] = AgentResult(
                        success=False,
                        output=None,
                        error="Circular dependency or missing dependencies"
                    )
                break
        
        return self.results
    
    async def shutdown_all(self) -> None:
        """Shutdown all agents"""
        for agent in self.agents.values():
            await agent.shutdown()
    
    @staticmethod
    def load_workflow_from_yaml(path: Path) -> List[WorkflowStep]:
        """Load workflow definition from YAML"""
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        steps = []
        for step_data in data.get("steps", []):
            steps.append(WorkflowStep(
                name=step_data["name"],
                agent_type=AgentType(step_data["agent_type"]),
                task=step_data["task"],
                depends_on=step_data.get("depends_on", []),
                config=step_data.get("config", {})
            ))
        
        return steps
