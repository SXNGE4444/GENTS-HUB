"""Unified CLI for AI Automation Orchestrator"""

import click
import asyncio
from pathlib import Path
import os
from dotenv import load_dotenv

from orchestrator.agent_base import AgentConfig, AgentType
from orchestrator.workflows.engine import WorkflowEngine, WorkflowStep

load_dotenv()

@click.group()
def cli():
    """AI Automation Orchestrator - Unified Platform"""
    pass

@cli.command()
@click.option('--agent', type=click.Choice(['openhands', 'crewai', 'autogpt', 'strix', 'moneyprinter']), required=True)
@click.option('--task', required=True, help='Task to execute')
@click.option('--model', default='gpt-4', help='Model to use')
def run(agent, task, model):
    """Run a single agent with a task"""
    async def _run():
        engine = WorkflowEngine()
        
        agent_config = AgentConfig(
            agent_type=AgentType(agent),
            api_key=os.getenv(f"{agent.upper()}_API_KEY"),
            model=model,
            verbose=True
        )
        
        engine.register_agent(AgentType(agent), agent_config)
        
        print(f"Initializing {agent}...")
        if not await engine.initialize_all():
            print(f"Failed to initialize {agent}")
            return
        
        print(f"Running task: {task[:50]}...")
        steps = [WorkflowStep(name="single", agent_type=AgentType(agent), task=task)]
        results = await engine.run_workflow(steps)
        
        result = results.get("single")
        if result and result.success:
            print(f"✓ Task completed in {result.execution_time:.2f}s")
            print(f"Output: {result.output}")
        else:
            print(f"✗ Task failed: {result.error if result else 'Unknown error'}")
        
        await engine.shutdown_all()
    
    asyncio.run(_run())

@cli.command()
@click.option('--workflow', required=True, type=click.Path(exists=True), help='Path to workflow YAML file')
def run_workflow(workflow):
    """Run a multi-agent workflow from YAML"""
    async def _run_workflow():
        engine = WorkflowEngine()
        
        # Load workflow
        steps = WorkflowEngine.load_workflow_from_yaml(Path(workflow))
        
        # Register agents needed
        agent_types = {step.agent_type for step in steps}
        for agent_type in agent_types:
            config = AgentConfig(
                agent_type=agent_type,
                api_key=os.getenv(f"{agent_type.value.upper()}_API_KEY"),
                verbose=True
            )
            engine.register_agent(agent_type, config)
        
        # Initialize all
        if not await engine.initialize_all():
            print("Failed to initialize agents")
            return
        
        # Run workflow
        print(f"Running workflow with {len(steps)} steps...")
        results = await engine.run_workflow(steps)
        
        # Display results
        print("\n" + "="*50)
        print("Workflow Results:")
        print("="*50)
        
        for step in steps:
            result = results.get(step.name)
            if result:
                status = "✓" if result.success else "✗"
                time_str = f"{result.execution_time:.2f}s"
                output = str(result.output)[:100] if result.output else result.error
                print(f"{status} {step.name} - {time_str}")
                print(f"   Output: {output}\n")
        
        await engine.shutdown_all()
    
    asyncio.run(_run_workflow())

@cli.command()
def list_agents():
    """List available agents"""
    print("\nAvailable Agents:")
    print("-" * 40)
    agents = [
        ("openhands", "AI-driven code development", "✅ Available"),
        ("crewai", "Multi-agent orchestration", "✅ Available"),
        ("autogpt", "Autonomous agent building", "🔄 Coming soon"),
        ("strix", "Security testing", "🔄 Coming soon"),
        ("moneyprinter", "Monetization automation", "🔄 Coming soon"),
    ]
    
    for name, desc, status in agents:
        print(f"{status} {name:15} - {desc}")

@cli.command()
def version():
    """Show version"""
    from orchestrator import __version__
    print(f"AI Automation Orchestrator version {__version__}")

if __name__ == "__main__":
    cli()
