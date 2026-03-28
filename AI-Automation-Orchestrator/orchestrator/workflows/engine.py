"""Unified workflow engine that combines multiple agents"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
import yaml
from pathlib import Path
import asyncio
import logging
from datetime import datetime

from orchestrator.agent_base import BaseAgent, AgentConfig, AgentType, AgentResult
from orchestrator.agents.openhands.adapter import OpenHandsAdapter
from orchestrator.agents.crewai.adapter import CrewAIAdapter
from orchestrator.agents.autogpt.adapter import AutoGPTAdapter
from orchestrator.agents.strix.adapter import StrixAdapter
from orchestrator.agents.moneyprinter.adapter import MoneyPrinterAdapter

logger = logging.getLogger(__name__)

@dataclass
class WorkflowStep:
    """Single step in a workflow"""
    name: str
    agent_type: AgentType
    task: str
    depends_on: List[str] = field(default_factory=list)
    config: Dict[str, Any] = field(default_factory=dict)
    retry_count: int = 0
    max_retries: int = 3

class WorkflowEngine:
    """Orchestrates multi-agent workflows"""
    
    def __init__(self, verbose: bool = False):
        self.agents: Dict[AgentType, BaseAgent] = {}
        self.results: Dict[str, AgentResult] = {}
        self.verbose = verbose
        self.workflow_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def register_agent(self, agent_type: AgentType, config: AgentConfig) -> BaseAgent:
        """Register an agent with the engine"""
        if agent_type == AgentType.OPENHANDS:
            agent = OpenHandsAdapter(config)
        elif agent_type == AgentType.CREWAI:
            agent = CrewAIAdapter(config)
        elif agent_type == AgentType.AUTOGPT:
            agent = AutoGPTAdapter(config)
        elif agent_type == AgentType.STRIX:
            agent = StrixAdapter(config)
        elif agent_type == AgentType.MONEYPRINTER:
            agent = MoneyPrinterAdapter(config)
        else:
            raise ValueError(f"Unsupported agent type: {agent_type}")
        
        self.agents[agent_type] = agent
        if self.verbose:
            print(f"✅ Registered {agent_type.value} agent")
        return agent
    
    async def initialize_all(self) -> bool:
        """Initialize all registered agents"""
        for agent_type, agent in self.agents.items():
            if self.verbose:
                print(f"🔧 Initializing {agent_type.value}...")
            if not await agent.initialize():
                logger.error(f"Failed to initialize {agent_type.value}")
                return False
        return True
    
    async def run_workflow(self, workflow_steps: List[WorkflowStep]) -> Dict[str, AgentResult]:
        """Execute a workflow with dependencies"""
        self.results = {}
        
        # Create execution plan
        steps_to_execute = list(workflow_steps)
        executed = set()
        
        while steps_to_execute:
            progress = False
            
            for step in steps_to_execute[:]:
                # Check if all dependencies are satisfied
                deps_met = all(dep in self.results for dep in step.depends_on)
                
                if deps_met:
                    # Execute this step
                    if self.verbose:
                        print(f"🚀 Executing step: {step.name} ({step.agent_type.value})")
                    
                    result = await self._execute_step(step)
                    self.results[step.name] = result
                    
                    if result.success:
                        if self.verbose:
                            print(f"   ✅ Completed in {result.execution_time:.2f}s")
                    else:
                        if self.verbose:
                            print(f"   ❌ Failed: {result.error}")
                        
                        # Retry logic
                        if step.retry_count < step.max_retries:
                            step.retry_count += 1
                            if self.verbose:
                                print(f"   🔄 Retrying ({step.retry_count}/{step.max_retries})...")
                            continue
                    
                    steps_to_execute.remove(step)
                    executed.add(step.name)
                    progress = True
            
            if not progress:
                # Circular dependency or missing dependencies
                for step in steps_to_execute:
                    missing_deps = [d for d in step.depends_on if d not in self.results]
                    self.results[step.name] = AgentResult(
                        success=False,
                        output=None,
                        error=f"Circular dependency or missing dependencies: {missing_deps}"
                    )
                    steps_to_execute.remove(step)
        
        return self.results
    
    async def _execute_step(self, step: WorkflowStep) -> AgentResult:
        """Execute a single workflow step"""
        agent = self.agents.get(step.agent_type)
        if not agent:
            return AgentResult(
                success=False,
                output=None,
                error=f"Agent {step.agent_type.value} not registered"
            )
        
        return await agent._execute_with_timing(step.task, **step.config)
    
    async def shutdown_all(self) -> None:
        """Shutdown all agents"""
        for agent in self.agents.values():
            await agent.shutdown()
        if self.verbose:
            print("✅ All agents shutdown")
    
    @staticmethod
    def load_workflow_from_yaml(path: Path) -> List[WorkflowStep]:
        """Load workflow definition from YAML"""
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        steps = []
        for step_data in data.get("steps", []):
            steps.append(WorkflowStep(
                name=step_data["name"],
                agent_type=AgentType.from_string(step_data["agent_type"]),
                task=step_data["task"],
                depends_on=step_data.get("depends_on", []),
                config=step_data.get("config", {}),
                max_retries=step_data.get("max_retries", 3)
            ))
        
        return steps
    
    def export_results(self, filename: Optional[str] = None) -> str:
        """Export workflow results to JSON"""
        import json
        
        export = {
            "workflow_id": self.workflow_id,
            "timestamp": datetime.now().isoformat(),
            "results": {}
        }
        
        for name, result in self.results.items():
            export["results"][name] = result.to_dict()
        
        if filename:
            with open(filename, 'w') as f:
                json.dump(export, f, indent=2)
        
        return json.dumps(export, indent=2)
