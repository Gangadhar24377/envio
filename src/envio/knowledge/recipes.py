"""Curated package recipes for offline resolution.

Each recipe maps a use-case keyword/phrase to a list of recommended
PyPI packages.  The matcher scores user input against these keys
using token overlap so ``envio prompt "flask web app"`` resolves
even without an LLM.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Web Frameworks & APIs
# ---------------------------------------------------------------------------
_WEB: dict[str, list[str]] = {
    "flask": ["flask", "flask-cors", "python-dotenv", "gunicorn"],
    "flask api": ["flask", "flask-restful", "flask-cors", "marshmallow", "gunicorn", "python-dotenv"],
    "flask jwt": ["flask", "flask-jwt-extended", "flask-cors", "python-dotenv", "gunicorn"],
    "flask sqlalchemy": ["flask", "flask-sqlalchemy", "flask-migrate", "psycopg2-binary", "python-dotenv"],
    "django": ["django", "djangorestframework", "django-cors-headers", "gunicorn", "psycopg2-binary"],
    "django rest": ["django", "djangorestframework", "django-filter", "django-cors-headers", "drf-spectacular"],
    "django graphql": ["django", "graphene-django", "django-filter", "django-cors-headers"],
    "fastapi": ["fastapi", "uvicorn", "pydantic", "python-multipart", "httpx"],
    "fastapi postgres": ["fastapi", "uvicorn", "sqlalchemy", "asyncpg", "alembic", "pydantic"],
    "fastapi mongodb": ["fastapi", "uvicorn", "motor", "pydantic", "beanie"],
    "rest api": ["fastapi", "uvicorn", "pydantic", "httpx", "python-dotenv"],
    "graphql": ["strawberry-graphql", "fastapi", "uvicorn", "pydantic"],
    "web app": ["flask", "flask-cors", "python-dotenv", "gunicorn", "jinja2"],
    "websocket": ["fastapi", "uvicorn", "websockets", "python-dotenv"],
    "grpc": ["grpcio", "grpcio-tools", "protobuf", "grpcio-reflection"],
    "tornado": ["tornado", "motor", "python-dotenv"],
    "starlette": ["starlette", "uvicorn", "httpx", "python-multipart"],
    "aiohttp web": ["aiohttp", "aiohttp-cors", "aiohttp-jinja2", "python-dotenv"],
    "sanic": ["sanic", "sanic-ext", "python-dotenv"],
}

# ---------------------------------------------------------------------------
# Data Science & Analytics
# ---------------------------------------------------------------------------
_DATA_SCIENCE: dict[str, list[str]] = {
    "data analysis": ["pandas", "numpy", "matplotlib", "seaborn", "jupyter"],
    "data science": ["pandas", "numpy", "scipy", "matplotlib", "seaborn", "scikit-learn", "jupyter"],
    "data visualization": ["matplotlib", "seaborn", "plotly", "pandas", "numpy"],
    "dashboard": ["streamlit", "plotly", "pandas", "numpy"],
    "streamlit": ["streamlit", "plotly", "pandas", "numpy", "pillow"],
    "gradio": ["gradio", "pandas", "numpy", "pillow"],
    "jupyter": ["jupyter", "jupyterlab", "ipywidgets", "pandas", "numpy", "matplotlib"],
    "notebook": ["jupyter", "jupyterlab", "pandas", "numpy", "matplotlib"],
    "statistics": ["scipy", "statsmodels", "pandas", "numpy", "matplotlib"],
    "exploratory data analysis": ["pandas", "numpy", "matplotlib", "seaborn", "sweetviz"],
    "excel": ["openpyxl", "pandas", "xlsxwriter", "numpy"],
    "csv": ["pandas", "numpy", "csv23"],
    "reporting": ["pandas", "jinja2", "weasyprint", "matplotlib"],
    "pandas": ["pandas", "numpy", "matplotlib", "openpyxl"],
}

# ---------------------------------------------------------------------------
# Machine Learning
# ---------------------------------------------------------------------------
_ML: dict[str, list[str]] = {
    "machine learning": ["scikit-learn", "pandas", "numpy", "matplotlib", "jupyter"],
    "sklearn": ["scikit-learn", "pandas", "numpy", "matplotlib", "joblib"],
    "classification": ["scikit-learn", "pandas", "numpy", "matplotlib", "imbalanced-learn"],
    "regression": ["scikit-learn", "pandas", "numpy", "matplotlib", "statsmodels"],
    "clustering": ["scikit-learn", "pandas", "numpy", "matplotlib", "hdbscan"],
    "automl": ["auto-sklearn", "pandas", "numpy", "scikit-learn"],
    "xgboost": ["xgboost", "scikit-learn", "pandas", "numpy", "matplotlib"],
    "lightgbm": ["lightgbm", "scikit-learn", "pandas", "numpy", "matplotlib"],
    "catboost": ["catboost", "scikit-learn", "pandas", "numpy", "matplotlib"],
    "feature engineering": ["featuretools", "pandas", "numpy", "scikit-learn"],
    "hyperparameter tuning": ["optuna", "scikit-learn", "pandas", "numpy"],
    "mlflow": ["mlflow", "scikit-learn", "pandas", "numpy", "matplotlib"],
    "experiment tracking": ["mlflow", "wandb", "pandas", "numpy"],
}

# ---------------------------------------------------------------------------
# Deep Learning
# ---------------------------------------------------------------------------
_DL: dict[str, list[str]] = {
    "deep learning": ["torch", "torchvision", "numpy", "matplotlib", "tensorboard"],
    "pytorch": ["torch", "torchvision", "torchaudio", "numpy", "matplotlib", "tensorboard"],
    "tensorflow": ["tensorflow", "keras", "numpy", "matplotlib", "tensorboard"],
    "keras": ["tensorflow", "keras", "numpy", "matplotlib"],
    "neural network": ["torch", "torchvision", "numpy", "matplotlib", "tensorboard"],
    "cnn": ["torch", "torchvision", "numpy", "matplotlib", "pillow"],
    "rnn": ["torch", "numpy", "matplotlib", "tensorboard"],
    "transformer": ["torch", "transformers", "tokenizers", "numpy", "datasets"],
    "training": ["torch", "torchvision", "numpy", "tensorboard", "tqdm", "wandb"],
    "fine tuning": ["torch", "transformers", "datasets", "accelerate", "peft", "bitsandbytes"],
    "model serving": ["torch", "fastapi", "uvicorn", "onnxruntime", "numpy"],
    "onnx": ["onnx", "onnxruntime", "numpy", "torch"],
    "jax": ["jax", "jaxlib", "flax", "optax", "numpy"],
}

# ---------------------------------------------------------------------------
# NLP & LLM
# ---------------------------------------------------------------------------
_NLP: dict[str, list[str]] = {
    "nlp": ["transformers", "tokenizers", "datasets", "torch", "spacy"],
    "natural language processing": ["transformers", "tokenizers", "datasets", "torch", "spacy"],
    "text processing": ["spacy", "nltk", "textblob", "regex"],
    "sentiment analysis": ["transformers", "torch", "pandas", "numpy", "datasets"],
    "named entity recognition": ["spacy", "transformers", "torch"],
    "text classification": ["transformers", "torch", "datasets", "scikit-learn"],
    "chatbot": ["transformers", "torch", "fastapi", "uvicorn", "python-dotenv"],
    "llm": ["transformers", "torch", "accelerate", "bitsandbytes", "datasets"],
    "langchain": ["langchain", "langchain-community", "langchain-openai", "chromadb", "python-dotenv"],
    "langgraph": ["langgraph", "langchain", "langchain-openai", "python-dotenv"],
    "rag": ["langchain", "chromadb", "sentence-transformers", "python-dotenv", "pypdf"],
    "embeddings": ["sentence-transformers", "torch", "numpy", "faiss-cpu"],
    "vector database": ["chromadb", "sentence-transformers", "langchain", "python-dotenv"],
    "semantic search": ["sentence-transformers", "faiss-cpu", "torch", "numpy"],
    "openai": ["openai", "python-dotenv", "tiktoken", "httpx"],
    "anthropic": ["anthropic", "python-dotenv", "httpx"],
    "gemini": ["google-generativeai", "python-dotenv"],
    "huggingface": ["transformers", "datasets", "tokenizers", "accelerate", "torch"],
    "spacy": ["spacy", "numpy"],
    "topic modeling": ["gensim", "spacy", "pyLDAvis", "numpy", "pandas"],
    "translation": ["transformers", "torch", "sentencepiece", "sacremoses"],
    "summarization": ["transformers", "torch", "datasets", "rouge-score"],
    "speech recognition": ["openai-whisper", "torch", "numpy", "soundfile"],
    "text to speech": ["TTS", "torch", "numpy", "soundfile"],
    "ocr": ["pytesseract", "pillow", "opencv-python", "pdf2image"],
}

# ---------------------------------------------------------------------------
# Computer Vision
# ---------------------------------------------------------------------------
_CV: dict[str, list[str]] = {
    "computer vision": ["opencv-python", "torch", "torchvision", "pillow", "numpy"],
    "image processing": ["pillow", "opencv-python", "numpy", "scikit-image"],
    "image classification": ["torch", "torchvision", "pillow", "numpy", "matplotlib"],
    "object detection": ["ultralytics", "torch", "torchvision", "opencv-python", "numpy"],
    "yolo": ["ultralytics", "torch", "opencv-python", "numpy", "pillow"],
    "face detection": ["dlib", "opencv-python", "pillow", "numpy"],
    "face recognition": ["face-recognition", "dlib", "opencv-python", "pillow", "numpy"],
    "video processing": ["opencv-python", "numpy", "pillow", "moviepy"],
    "image generation": ["diffusers", "torch", "transformers", "accelerate", "pillow"],
    "stable diffusion": ["diffusers", "torch", "transformers", "accelerate", "safetensors"],
    "opencv": ["opencv-python", "numpy", "pillow"],
    "mediapipe": ["mediapipe", "opencv-python", "numpy", "pillow"],
}

# ---------------------------------------------------------------------------
# AI Agents & Orchestration
# ---------------------------------------------------------------------------
_AGENTS: dict[str, list[str]] = {
    "ai agent": ["langchain", "langgraph", "langchain-openai", "python-dotenv", "httpx"],
    "multi agent": ["crewai", "langchain", "langchain-openai", "python-dotenv"],
    "crewai": ["crewai", "crewai-tools", "langchain", "python-dotenv"],
    "autogen": ["pyautogen", "python-dotenv", "openai"],
    "agent framework": ["langchain", "langgraph", "langchain-openai", "tavily-python", "python-dotenv"],
    "tool calling": ["langchain", "langchain-openai", "python-dotenv"],
    "agentic": ["langgraph", "langchain", "langchain-openai", "tavily-python", "python-dotenv"],
}

# ---------------------------------------------------------------------------
# Web Scraping & Automation
# ---------------------------------------------------------------------------
_SCRAPING: dict[str, list[str]] = {
    "web scraping": ["beautifulsoup4", "requests", "lxml", "httpx"],
    "scraping": ["beautifulsoup4", "requests", "lxml", "httpx"],
    "scrapy": ["scrapy", "itemloaders", "scrapy-splash"],
    "selenium": ["selenium", "webdriver-manager", "beautifulsoup4"],
    "playwright": ["playwright", "beautifulsoup4", "httpx"],
    "browser automation": ["playwright", "selenium", "webdriver-manager"],
    "crawling": ["scrapy", "beautifulsoup4", "requests", "lxml"],
    "pdf parsing": ["pymupdf", "pdfplumber", "pypdf", "tabula-py"],
    "pdf": ["pypdf", "reportlab", "pillow"],
}

# ---------------------------------------------------------------------------
# Database & Storage
# ---------------------------------------------------------------------------
_DATABASE: dict[str, list[str]] = {
    "database": ["sqlalchemy", "alembic", "psycopg2-binary", "python-dotenv"],
    "postgres": ["psycopg2-binary", "sqlalchemy", "alembic", "python-dotenv"],
    "postgresql": ["psycopg2-binary", "sqlalchemy", "alembic", "python-dotenv"],
    "mysql": ["mysqlclient", "sqlalchemy", "alembic", "python-dotenv"],
    "sqlite": ["sqlalchemy", "alembic"],
    "mongodb": ["pymongo", "motor", "python-dotenv"],
    "redis": ["redis", "python-dotenv"],
    "elasticsearch": ["elasticsearch", "python-dotenv"],
    "orm": ["sqlalchemy", "alembic", "psycopg2-binary"],
    "supabase": ["supabase", "python-dotenv", "httpx"],
    "firebase": ["firebase-admin", "python-dotenv"],
    "dynamodb": ["boto3", "python-dotenv"],
    "neo4j": ["neo4j", "python-dotenv"],
    "cassandra": ["cassandra-driver", "python-dotenv"],
}

# ---------------------------------------------------------------------------
# DevOps, Cloud & Infrastructure
# ---------------------------------------------------------------------------
_DEVOPS: dict[str, list[str]] = {
    "aws": ["boto3", "botocore", "python-dotenv"],
    "azure": ["azure-identity", "azure-storage-blob", "python-dotenv"],
    "gcp": ["google-cloud-storage", "google-auth", "python-dotenv"],
    "docker": ["docker", "python-dotenv"],
    "kubernetes": ["kubernetes", "pyyaml", "python-dotenv"],
    "terraform": ["python-terraform", "pyyaml"],
    "ansible": ["ansible-core", "pyyaml", "jinja2"],
    "monitoring": ["prometheus-client", "grafana-api", "psutil"],
    "logging": ["loguru", "structlog", "python-json-logger"],
    "ci cd": ["tox", "nox", "pytest", "coverage"],
    "cli tool": ["click", "rich", "typer", "python-dotenv"],
    "cli": ["click", "rich", "typer"],
}

# ---------------------------------------------------------------------------
# Data Engineering
# ---------------------------------------------------------------------------
_DATA_ENG: dict[str, list[str]] = {
    "etl": ["apache-airflow", "pandas", "sqlalchemy", "python-dotenv"],
    "airflow": ["apache-airflow", "pandas", "sqlalchemy"],
    "data pipeline": ["prefect", "pandas", "sqlalchemy", "python-dotenv"],
    "prefect": ["prefect", "pandas", "sqlalchemy", "python-dotenv"],
    "luigi": ["luigi", "pandas", "sqlalchemy"],
    "spark": ["pyspark", "pandas", "numpy"],
    "dask": ["dask", "distributed", "pandas", "numpy"],
    "polars": ["polars", "numpy", "connectorx"],
    "kafka": ["confluent-kafka", "python-dotenv"],
    "celery": ["celery", "redis", "python-dotenv"],
    "data validation": ["pydantic", "pandera", "great-expectations"],
}

# ---------------------------------------------------------------------------
# Testing & Code Quality
# ---------------------------------------------------------------------------
_TESTING: dict[str, list[str]] = {
    "testing": ["pytest", "pytest-cov", "pytest-mock", "factory-boy"],
    "pytest": ["pytest", "pytest-cov", "pytest-mock", "pytest-xdist"],
    "unittest": ["pytest", "pytest-cov", "coverage"],
    "integration testing": ["pytest", "testcontainers", "httpx", "pytest-asyncio"],
    "load testing": ["locust", "httpx"],
    "linting": ["ruff", "mypy", "black", "isort"],
    "code quality": ["ruff", "mypy", "black", "pre-commit", "bandit"],
    "type checking": ["mypy", "pyright", "types-requests"],
}

# ---------------------------------------------------------------------------
# Security & Crypto
# ---------------------------------------------------------------------------
_SECURITY: dict[str, list[str]] = {
    "security": ["bandit", "safety", "cryptography", "python-dotenv"],
    "cryptography": ["cryptography", "pynacl", "python-jose"],
    "authentication": ["pyjwt", "python-jose", "passlib", "bcrypt"],
    "jwt": ["pyjwt", "python-jose", "cryptography"],
    "oauth": ["authlib", "httpx", "python-dotenv"],
    "encryption": ["cryptography", "pynacl"],
    "hashing": ["passlib", "bcrypt", "argon2-cffi"],
    "pen testing": ["scapy", "impacket", "paramiko"],
}

# ---------------------------------------------------------------------------
# Bots & Messaging
# ---------------------------------------------------------------------------
_BOTS: dict[str, list[str]] = {
    "discord bot": ["discord.py", "python-dotenv", "aiohttp"],
    "discord": ["discord.py", "python-dotenv", "aiohttp"],
    "telegram bot": ["python-telegram-bot", "python-dotenv"],
    "telegram": ["python-telegram-bot", "python-dotenv"],
    "slack bot": ["slack-sdk", "python-dotenv", "flask"],
    "slack": ["slack-sdk", "python-dotenv"],
    "whatsapp": ["twilio", "flask", "python-dotenv"],
    "twitter bot": ["tweepy", "python-dotenv"],
    "reddit bot": ["praw", "python-dotenv"],
    "email": ["yagmail", "python-dotenv"],
}

# ---------------------------------------------------------------------------
# IoT & Embedded
# ---------------------------------------------------------------------------
_IOT: dict[str, list[str]] = {
    "iot": ["paho-mqtt", "pyserial", "python-dotenv"],
    "mqtt": ["paho-mqtt", "python-dotenv"],
    "serial": ["pyserial", "python-dotenv"],
    "raspberry pi": ["RPi.GPIO", "gpiozero", "pillow"],
    "sensor": ["paho-mqtt", "pyserial", "influxdb-client"],
    "edge computing": ["onnxruntime", "numpy", "pillow", "paho-mqtt"],
}

# ---------------------------------------------------------------------------
# Scientific Computing
# ---------------------------------------------------------------------------
_SCIENTIFIC: dict[str, list[str]] = {
    "scientific computing": ["numpy", "scipy", "matplotlib", "sympy", "jupyter"],
    "numerical": ["numpy", "scipy", "matplotlib", "numba"],
    "simulation": ["simpy", "numpy", "scipy", "matplotlib"],
    "optimization": ["scipy", "cvxpy", "numpy", "matplotlib"],
    "signal processing": ["scipy", "numpy", "matplotlib", "librosa"],
    "bioinformatics": ["biopython", "pandas", "numpy", "matplotlib"],
    "chemistry": ["rdkit", "numpy", "pandas", "matplotlib"],
    "physics": ["numpy", "scipy", "matplotlib", "sympy", "vpython"],
    "math": ["numpy", "scipy", "sympy", "matplotlib"],
}

# ---------------------------------------------------------------------------
# Finance & Trading
# ---------------------------------------------------------------------------
_FINANCE: dict[str, list[str]] = {
    "finance": ["yfinance", "pandas", "numpy", "matplotlib", "ta"],
    "trading": ["ccxt", "pandas", "numpy", "ta", "python-dotenv"],
    "stock": ["yfinance", "pandas", "numpy", "matplotlib", "mplfinance"],
    "crypto trading": ["ccxt", "pandas", "numpy", "ta", "python-dotenv"],
    "backtesting": ["backtrader", "pandas", "numpy", "matplotlib"],
    "portfolio": ["pypfopt", "pandas", "numpy", "yfinance"],
    "quantitative": ["quantlib", "pandas", "numpy", "scipy"],
}

# ---------------------------------------------------------------------------
# Audio & Music
# ---------------------------------------------------------------------------
_AUDIO: dict[str, list[str]] = {
    "audio processing": ["librosa", "soundfile", "numpy", "matplotlib"],
    "audio": ["librosa", "soundfile", "numpy", "pydub"],
    "music": ["music21", "mido", "librosa", "numpy"],
    "speech": ["openai-whisper", "torch", "soundfile", "numpy"],
    "whisper": ["openai-whisper", "torch", "soundfile", "numpy"],
    "voice": ["pyttsx3", "speechrecognition", "pyaudio"],
}

# ---------------------------------------------------------------------------
# Geospatial
# ---------------------------------------------------------------------------
_GEO: dict[str, list[str]] = {
    "geospatial": ["geopandas", "shapely", "folium", "rasterio"],
    "gis": ["geopandas", "shapely", "fiona", "pyproj"],
    "mapping": ["folium", "geopandas", "shapely"],
    "geocoding": ["geopy", "folium", "geopandas"],
    "satellite": ["rasterio", "numpy", "matplotlib", "earthpy"],
}

# ---------------------------------------------------------------------------
# Game Development
# ---------------------------------------------------------------------------
_GAME: dict[str, list[str]] = {
    "game": ["pygame", "numpy", "pillow"],
    "pygame": ["pygame", "numpy", "pillow"],
    "game development": ["pygame", "numpy", "pillow", "pymunk"],
    "3d": ["panda3d", "numpy", "pillow"],
    "game ai": ["pygame", "numpy", "gymnasium"],
}

# ---------------------------------------------------------------------------
# Robotics
# ---------------------------------------------------------------------------
_ROBOTICS: dict[str, list[str]] = {
    "robotics": ["roboticstoolbox-python", "numpy", "scipy", "matplotlib"],
    "ros": ["rclpy", "numpy", "opencv-python"],
    "control systems": ["control", "numpy", "scipy", "matplotlib"],
    "reinforcement learning": ["gymnasium", "stable-baselines3", "torch", "numpy"],
    "rl": ["gymnasium", "stable-baselines3", "torch", "numpy", "tensorboard"],
}

# ---------------------------------------------------------------------------
# Miscellaneous
# ---------------------------------------------------------------------------
_MISC: dict[str, list[str]] = {
    "api wrapper": ["httpx", "pydantic", "python-dotenv"],
    "http client": ["httpx", "aiohttp", "requests"],
    "async": ["asyncio", "aiohttp", "httpx", "uvloop"],
    "gui": ["tkinter", "customtkinter", "pillow"],
    "desktop app": ["pyqt6", "pillow", "pyinstaller"],
    "image editing": ["pillow", "numpy", "opencv-python"],
    "qr code": ["qrcode", "pillow"],
    "barcode": ["python-barcode", "pillow"],
    "email sending": ["yagmail", "python-dotenv", "jinja2"],
    "scheduling": ["schedule", "apscheduler", "python-dotenv"],
    "task queue": ["celery", "redis", "python-dotenv"],
    "caching": ["cachetools", "diskcache", "redis"],
    "config management": ["pydantic-settings", "python-dotenv", "pyyaml"],
    "documentation": ["sphinx", "mkdocs", "mkdocs-material"],
    "packaging": ["hatchling", "build", "twine", "setuptools"],
    "file processing": ["watchdog", "pathlib", "python-magic"],
    "zip": ["zipfile36", "py7zr"],
    "markdown": ["markdown", "mistune", "rich"],
    "yaml": ["pyyaml", "ruamel.yaml"],
    "json": ["orjson", "ujson", "pydantic"],
    "xml": ["lxml", "xmltodict"],
    "toml": ["tomli", "tomli-w"],
    "template": ["jinja2", "mako"],
    "regex": ["regex", "re2"],
    "date time": ["pendulum", "arrow", "python-dateutil"],
    "timezone": ["pytz", "pendulum", "zoneinfo"],
    "color": ["colorama", "termcolor", "rich"],
    "progress bar": ["tqdm", "rich", "alive-progress"],
    "table": ["rich", "tabulate", "prettytable"],
    "argparse": ["click", "typer", "argparse"],
    "environment variables": ["python-dotenv", "environs"],
    "validation": ["pydantic", "cerberus", "marshmallow"],
    "serialization": ["marshmallow", "pydantic", "cattrs"],
}


def _merge_all() -> dict[str, list[str]]:
    """Merge all recipe dictionaries into one."""
    merged: dict[str, list[str]] = {}
    for d in (
        _WEB, _DATA_SCIENCE, _ML, _DL, _NLP, _CV, _AGENTS,
        _SCRAPING, _DATABASE, _DEVOPS, _DATA_ENG, _TESTING,
        _SECURITY, _BOTS, _IOT, _SCIENTIFIC, _FINANCE,
        _AUDIO, _GEO, _GAME, _ROBOTICS, _MISC,
    ):
        merged.update(d)
    return merged


PACKAGE_RECIPES: dict[str, list[str]] = _merge_all()
