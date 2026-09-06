import typer
import structlog
import subprocess
import os
from pathlib import Path
from job_agent.core.runner import AgentRunner
from job_agent.config import get_settings

app = typer.Typer(
    name="job-agent",
    help="🔍 Autonomous LinkedIn Job Discovery Agent",
    add_completion=False,
)

@app.command()
def run(verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output")):
    """Execute the full job discovery pipeline."""
    settings = get_settings()
    if verbose:
        settings.log_level = "DEBUG"
    
    typer.echo("[*] Launching Autonomous LinkedIn Job Discovery Agent...")
    runner = AgentRunner(settings)
    summary = runner.run()
    
    typer.echo("\n" + "=" * 60)
    typer.echo("Execution Summary")
    typer.echo("=" * 60)
    typer.echo(f"Run ID:            {summary.run_id}")
    typer.echo(f"Targets Searched:  {summary.total_targets}")
    typer.echo(f"Jobs Discovered:   {summary.jobs_found}")
    typer.echo(f"Jobs Qualified:    {summary.jobs_qualified}")
    typer.echo(f"Skipped (Dedup):   {summary.jobs_skipped_dedup}")
    typer.echo(f"Skipped (Score):   {summary.jobs_skipped_low_score}")
    typer.echo(f"Duration:          {summary.duration_seconds:.1f}s")
    typer.echo("=" * 60)
    typer.echo(f"[+] Output saved to: {settings.output_path} and {settings.db_path}")

@app.command()
def validate():
    """Validate configuration and criteria without running."""
    runner = AgentRunner()
    if runner.validate():
        typer.echo("✅ Validation passed")
    else:
        typer.echo("❌ Validation failed")
        raise typer.Exit(code=1)

@app.command()
def export():
    """Re-export qualified jobs from database to markdown."""
    runner = AgentRunner()
    runner.export_only()
    typer.echo("✅ Export complete")

@app.command()
def stats():
    """Show database statistics and run history."""
    runner = AgentRunner()
    data = runner.show_stats()
    for k, v in data.items():
        typer.echo(f"{k}: {v}")

@app.command()
def dashboard():
    """Launch the interactive Streamlit dashboard."""
    settings = get_settings()
    app_path = Path(__file__).parent / "dashboard" / "app.py"
    
    typer.echo(f"Starting dashboard on port {settings.dashboard_port}...")
    subprocess.run([
        "streamlit", "run", str(app_path),
        "--server.port", str(settings.dashboard_port)
    ])

@app.command()
def serve():
    """Start the MCP server in standalone mode."""
    typer.echo("Starting MCP server...")
    # Typically this would invoke the mcp server start
    from job_agent.mcp_server.server import main as server_main
    server_main()
