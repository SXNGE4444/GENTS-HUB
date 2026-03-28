# Quick setup script for AI Automation Orchestrator (Windows PowerShell)
Write-Host "🚀 Setting up AI Automation Orchestrator..." -ForegroundColor Green

# Create virtual environment
python -m venv venv
.\venv\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install -e .

# Create .env file if it doesn't exist
if (-not (Test-Path .env)) {
    Copy-Item .env.example .env
    Write-Host "⚠️  Created .env file. Please add your API keys!" -ForegroundColor Yellow
}

Write-Host "✅ Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Quick start:"
Write-Host "  .\venv\Scripts\activate"
Write-Host "  aiauto list-agents"
Write-Host "  aiauto run --agent openhands --task 'Write a Python function'"
Write-Host "  aiauto run-workflow --workflow examples/dev_security_workflow.yaml"
