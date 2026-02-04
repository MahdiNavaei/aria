"""Improve ARIA repository discoverability on GitHub."""

import os
import requests
import subprocess
import sys
from typing import List

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
if not GITHUB_TOKEN:
    print("[ERROR] GITHUB_TOKEN environment variable not set")
    print("Set it with: $env:GITHUB_TOKEN='your_token'")
    sys.exit(1)
OWNER = "MahdiNavaei"
REPO = "aria"

# Enhanced topics for better discoverability
TOPICS = [
    # Core technologies
    "agentic-ai",
    "llm",
    "langgraph",
    "automation",
    "event-sourcing",
    "human-in-the-loop",
    # Additional discoverability topics
    "python",
    "ai-agent",
    "langchain",
    "autonomous-agent",
    "vision-language-model",
    "production-ready",
    "event-driven",
    "cognitive-architecture",
    "local-llm",
    "ollama",
    "playwright",
    "automation-framework",
    "rag",
    "retrieval-augmented-generation",
    "kafka",
    "redis",
    "vector-database",
    "qdrant",
    "fastapi",
    "streamlit",
    "machine-learning",
    "deep-learning",
    "nlp",
    "computer-vision",
    "mlops",
    "ai-framework",
    "agent-framework",
    "task-automation",
    "workflow-automation",
]

# Enhanced description
DESCRIPTION = "🤖 Production-grade Agentic AI Framework | Vision + LLM + Event Sourcing | Local LLMs | LangGraph | HITL Safety | Autonomous Task Execution"


def update_repo_topics() -> bool:
    """Update repository topics via GitHub API."""
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/topics"
    headers = {
        "Accept": "application/vnd.github.mercy-preview+json",
        "Authorization": f"token {GITHUB_TOKEN}",
        "Content-Type": "application/json",
    }
    data = {"names": TOPICS}

    try:
        response = requests.patch(url, headers=headers, json=data)
        response.raise_for_status()
        print(f"[OK] Successfully updated topics: {len(TOPICS)} topics added")
        return True
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Error updating topics: {e}")
        if hasattr(e, "response") and e.response is not None:
            print(f"Response: {e.response.text}")
        return False


def update_repo_description() -> bool:
    """Update repository description via GitHub API."""
    url = f"https://api.github.com/repos/{OWNER}/{REPO}"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"token {GITHUB_TOKEN}",
        "Content-Type": "application/json",
    }
    data = {"description": DESCRIPTION}

    try:
        response = requests.patch(url, headers=headers, json=data)
        response.raise_for_status()
        print(f"[OK] Successfully updated description")
        return True
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Error updating description: {e}")
        if hasattr(e, "response") and e.response is not None:
            print(f"Response: {e.response.text}")
        return False


def prepare_pypi_publish():
    """Prepare project for PyPI publishing."""
    print("\n[INFO] Preparing for PyPI publish...")
    
    # Check if build tools are available
    try:
        import build
    except ImportError:
        print("[WARN] 'build' package not found. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "build", "twine"], check=False)
    
    # Update pyproject.toml with keywords
    print("[OK] PyPI preparation: Update pyproject.toml with keywords manually")
    print("   Add keywords: ['agentic-ai', 'llm', 'langgraph', 'automation', 'ai-agent']")


def create_awesome_list_prs():
    """Create PRs for Awesome Lists."""
    print("\n[INFO] Awesome Lists PRs:")
    print("   To add ARIA to Awesome Lists, create PRs to:")
    print("   1. https://github.com/langchain-ai/awesome-langchain")
    print("   2. https://github.com/langchain-ai/awesome-langgraph")
    print("   3. https://github.com/eugeneyan/awesome-ai-agents")
    print("   4. https://github.com/jupyter-naas/awesome-ai-agents")
    print("   5. https://github.com/ai-collection/awesome-ai-agents")
    print("\n   Entry format:")
    print('   - [ARIA](https://github.com/MahdiNavaei/aria) - Production-grade Agentic AI Framework')


def main():
    """Main entry point."""
    import sys
    import io
    # Fix encoding for Windows
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    
    print("Improving ARIA Repository Discoverability")
    print("=" * 60)
    
    # Update topics
    print("\n[1] Updating repository topics...")
    update_repo_topics()
    
    # Update description
    print("\n[2] Updating repository description...")
    update_repo_description()
    
    # Prepare PyPI
    prepare_pypi_publish()
    
    # Awesome Lists info
    create_awesome_list_prs()
    
    print("\n" + "=" * 60)
    print("[OK] Done! Repository discoverability improved.")
    print("\nNext steps:")
    print("  - Review and merge topics/description changes")
    print("  - Consider publishing to PyPI")
    print("  - Create PRs to Awesome Lists")


if __name__ == "__main__":
    main()
