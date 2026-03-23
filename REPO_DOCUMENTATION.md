# Envio - AI-Powered Development Environment Manager

## Overview

**Envio** is an AI-powered event and package manager designed to automate Python development environment setup. It uses artificial intelligence (LLMs and multi-agent systems) to understand natural language package management requests, resolve package dependencies automatically, generate appropriate installation commands (for pip or conda), create executable bash scripts to set up entire development environments, and run the setup in an isolated tmux session.

Think of it as having an AI assistant that handles all your dependency management headaches - you just tell it what packages you need, and it handles the rest.

---

## Tech Stack and Technologies

### Core Framework
- **Python** - Main programming language
- **CrewAI** - Multi-agent AI framework for orchestrating the workflow
- **LangChain** - AI/LLM integration framework
- **OpenAI GPT-4o-mini** - LLM for natural language understanding and generation

### Key Dependencies
| Category | Packages |
|----------|----------|
| AI/LLM | `crewai`, `langchain`, `langchain-openai`, `openai`, `litellm` |
| Web Frameworks | `fastapi`, `uvicorn` |
| Data Science/ML | `tensorflow`, `keras`, `scikit-learn`, `numpy`, `pandas`, `matplotlib` |
| Vector Databases | `chromadb`, `lancedb`, `qdrant-client` |
| Utilities | `python-dotenv`, `requests`, `httpx`, `pyyaml` |
| Testing | `pytest` |
| Cloud APIs | `google-cloud-aiplatform`, `boto3` |

### External Services
- **OpenAI API** - For LLM processing
- **Serper API** - For web search (fallback package lookup)
- **PyPI** - Python package repository lookup
- **Conda** - Alternative package manager support

---

## Directory Structure

```
envio/
├── .env                    # Environment variables (API keys)
├── README.md               # Basic project description
├── ROADMAP.md              # Development roadmap (6 phases)
├── IMPROVEMENTS.md         # Detailed improvements & feature ideas
├── requirements.txt        # Python dependencies (262 packages!)
├── main.py                 # Main entry point (250 lines)
├── setup_env.sh            # Example setup script
├── agents/                 # AI agent implementations
│   ├── __init__.py
│   ├── nlp_agent.py               # Extracts package info from user input
│   ├── dependency_resolution_agent.py  # Resolves package dependencies
│   ├── command_construction_agent.py   # Generates installation commands
│   └── bash_file_generator_agent.py    # Creates bash scripts
├── tools/                  # Reusable tools for agents
│   ├── __init__.py
│   ├── package_lookup.py         # PyPI/Conda package lookup
│   └── serper_search.py          # Web search fallback
├── utils/                  # Utility functions
│   ├── __init__.py
│   └── bash_executor.py          # Bash script execution
└── testing_env/            # Test environment
    └── setup_env.sh        # Sample generated script
```

---

## Main Features and Functionality

### 1. Natural Language Input
Users can describe their package needs in plain English. For example:
- "I need tensorflow with GPU support and scikit-learn for a data science project"
- "Set up a fastapi web server with uvicorn and sqlalchemy"

### 2. Multi-Agent Pipeline
Four specialized AI agents work together in a sequential workflow:

#### a) NLP Agent (`nlp_agent.py`)
- Parses user input to extract package names
- Determines environment type (pip/conda)
- Identifies Python version requirements
- Extracts version constraints

#### b) Dependency Resolution Agent (`dependency_resolution_agent.py`)
- Looks up packages on PyPI and Conda
- Resolves package dependencies automatically
- Uses web search (Serper) as fallback when package info is unavailable

#### c) Command Construction Agent (`command_construction_agent.py`)
- Generates appropriate installation commands
- Handles both pip and conda syntax
- Includes version pinning when specified

#### d) Bash File Generator Agent (`bash_file_generator_agent.py`)
- Creates executable bash shell scripts
- Includes environment setup (virtualenv/conda env)
- Handles error checking and validation

### 3. Package Lookup
- Checks PyPI API for package information
- Checks Conda API for package information
- Returns package metadata (version, dependencies, description)

### 4. Dual Environment Support
- Supports **pip** environments
- Supports **conda** environments
- User can specify preference in natural language

### 5. Automated Script Execution
- Runs setup in tmux session for isolation
- Creates timestamped log files for each setup
- Provides real-time feedback to user

### 6. Logging
- Creates timestamped log files for each setup
- Tracks all agent interactions
- Records command execution results

---

## Workflow

```
User Input (Natural Language)
        ↓
    NLP Agent (Extract packages, env type, versions)
        ↓
Dependency Resolution Agent (PyPI/Conda lookup + Serper search)
        ↓
Command Construction Agent (Generate pip/conda commands)
        ↓
Bash File Generator Agent (Create shell script)
        ↓
Execute in tmux session (with user input for path/name)
```

---

## Usage Example

```bash
# Run the main script
python main.py

# Enter your request in natural language:
# "I need a data science environment with pandas, numpy, matplotlib and scikit-learn"
```

The system will:
1. Parse your request and identify the packages
2. Look up each package on PyPI/Conda
3. Resolve any dependencies
4. Generate appropriate installation commands
5. Create a bash script
6. Execute the script in a tmux session

---

## Configuration

### Environment Variables (`.env`)
Create a `.env` file with the following:

```env
OPENAI_API_KEY=your_openai_api_key_here
SERPER_API_KEY=your_serper_api_key_here
```

### Requirements
Install dependencies:
```bash
pip install -r requirements.txt
```

---

## Documentation Files

### README.md
Brief 4-line project description.

### ROADMAP.md
Comprehensive 6-phase development plan:
- **Phase 1**: Foundation & Infrastructure (gitignore, packaging, CI/CD)
- **Phase 2**: Code Quality & Testing (linting, typing, testing)
- **Phase 3**: Refactoring & Architecture (DI, error handling)
- **Phase 4**: Quick Win Features (dry-run, import, templates)
- **Phase 5**: Medium-Term Features (Docker, security scanning, history)
- **Phase 6**: Long-Term Vision (web UI, VS Code extension, plugins)

### IMPROVEMENTS.md
Detailed analysis of:
- Critical infrastructure gaps
- Code quality improvements needed
- Architecture improvements
- Security improvements
- Short/medium/long-term features
- Dependency cleanup recommendations

---

## Current Status and Areas for Improvement

### What's Working
- ✅ Functional multi-agent AI pipeline for environment creation
- ✅ Support for both pip and conda
- ✅ Package lookup from PyPI/Conda
- ✅ Web search fallback via Serper
- ✅ Automated bash script generation

### Areas Needing Improvement
- ❌ No `.gitignore` file
- ❌ No proper Python packaging (`pyproject.toml` missing)
- ❌ No tests (0% coverage)
- ❌ No CI/CD setup
- ❌ Large dependency list (262 packages, many unused)
- ❌ No type hints
- ❌ No logging (uses `print()` statements)
- ❌ Large `main.py` (250 lines) that should be refactored
- ❌ `.env` file committed to repository (security risk)
- ❌ Minimal README documentation

---

## License

Not specified in the repository.
