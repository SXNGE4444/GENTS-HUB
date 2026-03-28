"""Complete CLI for AI Automation Orchestrator"""

import click
import asyncio
from pathlib import Path
import os
import sys
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.syntax import Syntax
from rich import print as rprint

from orchestrator.agent_base import AgentConfig, AgentType
from orchestrator.workflows.engine import WorkflowEngine, WorkflowStep

load_dotenv()
console = Console()

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_banner():
    banner = f"""
{Colors.CYAN}{Colors.BOLD}
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   █████╗ ██╗      █████╗ ██╗   ██╗████████╗ ██████╗ ███╗   ███╗
║  ██╔══██╗██║     ██╔══██╗██║   ██║╚══██╔══╝██╔═══██╗████╗ ████║
║  ███████║██║     ███████║██║   ██║   ██║   ██║   ██║██╔████╔██║
║  ██╔══██║██║     ██╔══██║██║   ██║   ██║   ██║   ██║██║╚██╔╝██║
║  ██║  ██║███████╗██║  ██║╚██████╔╝   ██║   ╚██████╔╝██║ ╚═╝ ██║
║  ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝ ╚═════╝    ╚═╝    ╚═════╝ ╚═╝     ╚═╝
║                                                               ║
║           Unified AI Automation Platform v1.0.0               ║
║     Combining OpenHands • crewAI • AutoGPT • Strix • MPV2     ║
╚═══════════════════════════════════════════════════════════════╝
{Colors.ENDC}
"""
    console.print(banner)

@click.group()
def cli():
    """AI Automation Orchestrator - Unified Platform"""
    pass

@cli.command()
def version():
    """Show version"""
    from orchestrator import __version__
    print_banner()
    console.print(f"[bold green]Version:[/bold green] {__version__}")
    console.print(f"[bold green]Python:[/bold green] {sys.version.split()[0]}")
    console.print(f"[bold green]Status:[/bold green] ✅ Ready to use")

@cli.command()
def list_agents():
    """List available agents"""
    print_banner()
    
    table = Table(title="🤖 Available AI Agents", show_header=True, header_style="bold cyan")
    table.add_column("Agent", style="cyan", width=15)
    table.add_column("Description", style="green", width=40)
    table.add_column("Status", style="yellow", width=15)
    table.add_column("Features", style="white", width=30)
    
    agents = [
        ("openhands", "AI-driven code development", "✅ Ready", "Code generation, Execution"),
        ("crewai", "Multi-agent orchestration", "✅ Ready", "Collaboration, Workflows"),
        ("autogpt", "Autonomous agent building", "✅ Ready", "Self-improving, Goals"),
        ("strix", "Security testing", "✅ Ready", "Vulnerability scanning, PoC"),
        ("moneyprinter", "Monetization automation", "✅ Ready", "Content creation, Social media"),
    ]
    
    for name, desc, status, features in agents:
        table.add_row(name, desc, status, features)
    
    console.print(table)
    console.print("\n[italic]Run 'aiauto run --agent <name> --task \"your task\"' to use an agent[/italic]")

@cli.command()
@click.option('--agent', type=click.Choice(['openhands', 'crewai', 'autogpt', 'strix', 'moneyprinter']), required=True)
@click.option('--task', required=True, help='Task to execute')
@click.option('--model', default='gpt-4', help='Model to use')
@click.option('--verbose', is_flag=True, help='Show detailed output')
def run(agent, task, model, verbose):
    """Run a single agent with a task"""
    async def _run():
        engine = WorkflowEngine(verbose=verbose)
        
        agent_config = AgentConfig(
            agent_type=AgentType.from_string(agent),
            api_key=os.getenv(f"{agent.upper()}_API_KEY", "demo-key"),
            model=model,
            max_iterations=10,
            verbose=verbose,
            temperature=0.7
        )
        
        console.print(f"\n[cyan]🚀 Initializing {agent}...[/cyan]")
        engine.register_agent(AgentType.from_string(agent), agent_config)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            progress.add_task(description="Initializing...", total=None)
            
            if not await engine.initialize_all():
                console.print(f"[red]❌ Failed to initialize {agent}[/red]")
                return
            
            progress.add_task(description=f"Executing: {task[:50]}...", total=None)
            steps = [WorkflowStep(name="single", agent_type=AgentType.from_string(agent), task=task)]
            results = await engine.run_workflow(steps)
            
            result = results.get("single")
            if result and result.success:
                console.print(f"\n[green]✅ Task completed in {result.execution_time:.2f}s[/green]")
                console.print("\n[bold cyan]📊 Output:[/bold cyan]")
                
                if isinstance(result.output, dict):
                    for key, value in result.output.items():
                        console.print(f"  [yellow]{key}:[/yellow] {str(value)[:200]}")
                else:
                    console.print(f"  {result.output}")
            else:
                console.print(f"\n[red]❌ Task failed: {result.error if result else 'Unknown error'}[/red]")
        
        await engine.shutdown_all()
    
    asyncio.run(_run())

@cli.command()
@click.option('--workflow', required=True, type=click.Path(exists=True), help='Path to workflow YAML file')
@click.option('--verbose', is_flag=True, help='Show detailed output')
@click.option('--export', type=click.Path(), help='Export results to JSON file')
def run_workflow(workflow, verbose, export):
    """Run a multi-agent workflow from YAML"""
    async def _run_workflow():
        engine = WorkflowEngine(verbose=verbose)
        
        # Load workflow
        console.print(f"\n[cyan]📋 Loading workflow: {workflow}[/cyan]")
        steps = WorkflowEngine.load_workflow_from_yaml(Path(workflow))
        console.print(f"[green]   ✓ Loaded {len(steps)} steps[/green]")
        
        # Register agents needed
        agent_types = {step.agent_type for step in steps}
        console.print(f"[cyan]🔧 Registering agents: {', '.join([a.value for a in agent_types])}[/cyan]")
        
        for agent_type in agent_types:
            config = AgentConfig(
                agent_type=agent_type,
                api_key=os.getenv(f"{agent_type.value.upper()}_API_KEY", "demo-key"),
                verbose=verbose
            )
            engine.register_agent(agent_type, config)
        
        # Initialize all
        console.print(f"[cyan]⚙️  Initializing agents...[/cyan]")
        if not await engine.initialize_all():
            console.print("[red]❌ Failed to initialize agents[/red]")
            return
        
        # Run workflow
        console.print(f"\n[bold cyan]🚀 Running workflow...[/bold cyan]")
        console.print("─" * 50)
        
        results = await engine.run_workflow(steps)
        
        # Display results
        console.print("\n[bold green]📊 Workflow Results:[/bold green]")
        console.print("─" * 50)
        
        for step in steps:
            result = results.get(step.name)
            if result:
                status = "✅" if result.success else "❌"
                time_str = f"{result.execution_time:.2f}s"
                
                if result.success:
                    console.print(f"\n[green]{status} {step.name}[/green] [dim]({time_str})[/dim]")
                    if verbose and result.output:
                        output_str = str(result.output)[:200]
                        console.print(f"   [dim]Output: {output_str}[/dim]")
                else:
                    console.print(f"\n[red]{status} {step.name}[/red] [dim]({time_str})[/dim]")
                    console.print(f"   [red]Error: {result.error}[/red]")
        
        # Export results if requested
        if export:
            export_path = Path(export)
            engine.export_results(str(export_path))
            console.print(f"\n[green]📁 Results exported to: {export_path}[/green]")
        
        await engine.shutdown_all()
        console.print("\n[bold green]✅ Workflow completed![/bold green]")
    
    asyncio.run(_run_workflow())

@cli.command()
def demo():
    """Run a complete demo workflow"""
    console.print("[cyan]🎯 Running complete demo...[/cyan]")
    
    # Create a demo workflow on the fly
    demo_steps = [
        WorkflowStep(
            name="generate_code",
            agent_type=AgentType.OPENHANDS,
            task="Create a Python function that calculates fibonacci numbers",
            config={"language": "python"}
        ),
        WorkflowStep(
            name="security_scan",
            agent_type=AgentType.STRIX,
            task="Scan the generated code for security issues",
            depends_on=["generate_code"],
            config={"scan_mode": "quick"}
        ),
        WorkflowStep(
            name="review_output",
            agent_type=AgentType.CREWAI,
            task="Review the code and security findings",
            depends_on=["security_scan"],
            config={"agents": ["code_reviewer", "security_expert"]}
        )
    ]
    
    async def _run_demo():
        engine = WorkflowEngine(verbose=True)
        
        # Register all agents
        agents_to_register = [AgentType.OPENHANDS, AgentType.STRIX, AgentType.CREWAI]
        for agent_type in agents_to_register:
            config = AgentConfig(agent_type=agent_type, verbose=True)
            engine.register_agent(agent_type, config)
        
        if not await engine.initialize_all():
            console.print("[red]Failed to initialize agents[/red]")
            return
        
        results = await engine.run_workflow(demo_steps)
        
        console.print("\n[bold green]✨ Demo Results:[/bold green]")
        for step in demo_steps:
            result = results.get(step.name)
            if result and result.success:
                console.print(f"  ✅ {step.name}: Completed in {result.execution_time:.2f}s")
        
        await engine.shutdown_all()
    
    asyncio.run(_run_demo())

@cli.command()
def interactive():
    """Start interactive mode"""
    print_banner()
    console.print("[cyan]🎮 Interactive Mode - Type 'exit' to quit[/cyan]\n")
    
    while True:
        try:
            command = console.input("[bold yellow]aiauto> [/bold yellow]").strip()
            if command.lower() in ['exit', 'quit', 'q']:
                break
            elif command:
                # Parse simple commands
                if command.startswith('run '):
                    parts = command.split(' ', 2)
                    if len(parts) >= 3:
                        agent = parts[1]
                        task = parts[2]
                        # Call run command
                        import sys
                        sys.argv = ['aiauto', 'run', '--agent', agent, '--task', task]
                        cli()
                else:
                    console.print("[red]Unknown command. Try: run <agent> <task>[/red]")
        except KeyboardInterrupt:
            break
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
    
    console.print("\n[green]👋 Goodbye![/green]")

if __name__ == "__main__":
    cli()
