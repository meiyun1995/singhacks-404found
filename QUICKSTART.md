# Quick Start Guide

This guide will help you get started with the Multi-Agent Workflow System quickly.

## Installation

```bash
# Clone the repository
git clone https://github.com/meiyun1995/singhacks-404found.git
cd singhacks-404found

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env and add your OpenAI API key
```

## Your First Workflow

### Option 1: Interactive Mode (Easiest)

```bash
python main.py --mode interactive
```

Follow the prompts to select and run a workflow.

### Option 2: Command Line

```bash
python main.py --mode research --topic "Future of AI"
```

### Option 3: Use Example Scripts

```bash
# Run a complete research workflow
python examples/basic_research_workflow.py

# Run custom workflow
python examples/custom_workflow.py

# Use individual agents
python examples/individual_agents.py
```

## Quick Code Example

```python
from workflow_orchestrator import WorkflowOrchestrator

# Initialize
orchestrator = WorkflowOrchestrator()

# Run workflow
results = orchestrator.run_research_workflow(
    topic="Climate Change Solutions"
)

# Get results
print(results["research"])
print(results["written_content"])
print(results["review"])
```

## Next Steps

1. Check out the full [README.md](README.md) for detailed documentation
2. Explore the `examples/` directory for more use cases
3. Customize agent configurations in `config/settings.py`
4. Create your own custom workflows

## Common Issues

### Missing API Key
```
Error: OPENAI_API_KEY is required but not set
```
**Solution**: Add your OpenAI API key to the `.env` file

### Import Errors
```
ModuleNotFoundError: No module named 'openai'
```
**Solution**: Run `pip install -r requirements.txt`

## Getting Help

- Check the [README.md](README.md) for full documentation
- Review example scripts in `examples/`
- Open an issue on GitHub for bugs or questions
