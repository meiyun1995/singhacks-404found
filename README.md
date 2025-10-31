# Multi-Agent Workflow System

A sophisticated multi-agent workflow system built with the OpenAI Agents Python framework. This system enables coordinated collaboration between specialized AI agents to complete complex tasks through research, content creation, and review workflows.

## 🌟 Features

- **Multiple Specialized Agents**: Research, Writer, Reviewer, and Coordinator agents
- **Flexible Workflow Orchestration**: Pre-built and custom workflow support
- **Rich CLI Interface**: Beautiful terminal output with progress indicators
- **Extensible Architecture**: Easy to add new agents and workflows
- **Result Persistence**: Automatic saving of workflow results
- **Interactive Mode**: User-friendly interactive workflow execution

## 📁 Project Structure

```
singhacks-404found/
├── agents/                      # Agent implementations
│   ├── __init__.py
│   ├── base_agent.py           # Base agent class
│   └── specialized_agents.py   # Specialized agent implementations
├── config/                      # Configuration files
│   ├── __init__.py
│   └── settings.py             # Agent and system configuration
├── utils/                       # Utility functions
│   ├── __init__.py
│   └── helpers.py              # Helper functions
├── examples/                    # Example scripts
│   ├── basic_research_workflow.py
│   ├── custom_workflow.py
│   └── individual_agents.py
├── tests/                       # Test files (to be implemented)
├── outputs/                     # Generated workflow results (auto-created)
├── workflow_orchestrator.py    # Main workflow orchestration
├── main.py                      # CLI entry point
├── requirements.txt             # Python dependencies
├── .env.example                 # Example environment variables
└── README.md                    # This file
```

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- OpenAI API key

### Installation

1. Clone the repository:
```bash
git clone https://github.com/meiyun1995/singhacks-404found.git
cd singhacks-404found
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
```

### Configuration

Edit the `.env` file with your settings:

```env
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4-turbo-preview
MAX_RETRIES=3
TIMEOUT_SECONDS=60
```

## 💻 Usage

### Interactive Mode

Run the system in interactive mode for guided workflow execution:

```bash
python main.py --mode interactive
```

### Research Workflow

Run a complete research workflow from command line:

```bash
python main.py --mode research --topic "Artificial Intelligence in Healthcare"
```

### Using Example Scripts

#### Basic Research Workflow
```bash
python examples/basic_research_workflow.py
```

This runs a complete workflow:
1. Research Agent gathers information
2. Writer Agent creates content
3. Reviewer Agent provides feedback

#### Custom Workflow
```bash
python examples/custom_workflow.py
```

Demonstrates creating custom workflows with specific agent sequences.

#### Individual Agents
```bash
python examples/individual_agents.py
```

Shows how to use agents independently without orchestration.

## 🤖 Available Agents

### Research Agent
Specializes in information gathering and research.
```python
from agents import ResearchAgent

researcher = ResearchAgent()
result = researcher.research_topic("Machine Learning", depth="comprehensive")
```

### Writer Agent
Creates written content based on topics and research.
```python
from agents import WriterAgent

writer = WriterAgent()
content = writer.write_content(
    content_type="article",
    topic="Climate Change",
    research_data=research_result
)
```

### Reviewer Agent
Reviews content and provides constructive feedback.
```python
from agents import ReviewerAgent

reviewer = ReviewerAgent()
feedback = reviewer.review_content(
    content=written_content,
    criteria=["accuracy", "clarity", "engagement"]
)
```

### Coordinator Agent
Plans and manages workflow execution.
```python
from agents import CoordinatorAgent

coordinator = CoordinatorAgent()
plan = coordinator.plan_workflow("Create a comprehensive report on renewable energy")
```

## 🔧 Programmatic Usage

### Using the Workflow Orchestrator

```python
from workflow_orchestrator import WorkflowOrchestrator

# Initialize orchestrator
orchestrator = WorkflowOrchestrator()

# Run research workflow
results = orchestrator.run_research_workflow(
    topic="The Future of Quantum Computing"
)

# Access results
print(results["research"])
print(results["written_content"])
print(results["review"])

# Save results
orchestrator.save_results("output.json")
```

### Creating Custom Workflows

```python
from workflow_orchestrator import WorkflowOrchestrator

orchestrator = WorkflowOrchestrator()

steps = [
    {
        "agent": "researcher",
        "action": "research_topic",
        "params": {"topic": "AI Ethics", "depth": "moderate"}
    },
    {
        "agent": "writer",
        "action": "write_content",
        "params": {"content_type": "report", "topic": "AI Ethics"}
    },
    {
        "agent": "reviewer",
        "action": "review_content",
        "params": {"content": "...", "criteria": ["accuracy", "clarity"]}
    }
]

results = orchestrator.run_custom_workflow(
    task_description="Create AI ethics report",
    steps=steps
)
```

## 📊 Output

Workflow results are automatically saved to the `outputs/` directory with timestamps:
- JSON format for programmatic access
- Rich console output during execution
- Detailed progress indicators

## 🧪 Testing

```bash
# Run tests (to be implemented)
pytest tests/
```

## 🛠️ Extending the System

### Adding a New Agent

1. Create a new agent class in `agents/specialized_agents.py`:
```python
class AnalyzerAgent(BaseAgent):
    def __init__(self, client=None, config=None):
        super().__init__(role="analyzer", client=client, config=config)
    
    def analyze_data(self, data: str) -> str:
        task = f"Analyze the following data: {data}"
        return self.execute(task)
```

2. Add agent configuration in `config/settings.py`:
```python
"analyzer": {
    "name": "Analyzer Agent",
    "description": "Analyzes data and provides insights",
    "instructions": "You are an analyzer agent...",
    "temperature": 0.5,
}
```

3. Register in `agents/__init__.py` and use in workflows.

## 📝 Best Practices

1. **API Keys**: Never commit API keys. Always use `.env` files
2. **Error Handling**: Agents include built-in error handling and retries
3. **Temperature Settings**: Adjust per agent type (lower for factual tasks, higher for creative)
4. **Workflow Design**: Break complex tasks into clear, sequential steps
5. **Result Storage**: Review and organize outputs regularly

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is open source and available under the MIT License.

## 🔗 Resources

- [OpenAI API Documentation](https://platform.openai.com/docs)
- [OpenAI Python SDK](https://github.com/openai/openai-python)
- [Multi-Agent Systems](https://en.wikipedia.org/wiki/Multi-agent_system)

## 📧 Support

For questions or issues, please open an issue on GitHub.

## 🎯 Roadmap

- [ ] Add more specialized agents (Data Analyst, Code Generator, etc.)
- [ ] Implement agent-to-agent communication
- [ ] Add async/parallel workflow execution
- [ ] Create web interface
- [ ] Add workflow templates
- [ ] Implement result caching
- [ ] Add comprehensive test suite
- [ ] Create visualization tools for workflows

---

Built with ❤️ using OpenAI Agents Python Framework