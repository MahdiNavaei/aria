"""Submit ARIA to all possible platforms for maximum discoverability."""

import os
import sys
import subprocess
import requests
import json
from typing import List, Dict

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
OWNER = "MahdiNavaei"
REPO = "aria"

# Topics to add (manually via GitHub UI if API fails)
TOPICS = [
    "agentic-ai", "llm", "langgraph", "automation", "event-sourcing",
    "human-in-the-loop", "python", "ai-agent", "langchain", "autonomous-agent",
    "vision-language-model", "production-ready", "event-driven",
    "cognitive-architecture", "local-llm", "ollama", "playwright",
    "automation-framework", "rag", "retrieval-augmented-generation",
    "kafka", "redis", "vector-database", "qdrant", "fastapi", "streamlit",
    "machine-learning", "deep-learning", "nlp", "computer-vision", "mlops",
    "ai-framework", "agent-framework", "task-automation", "workflow-automation",
]

ARIA_INFO = {
    "name": "ARIA",
    "full_name": "Adaptive Reasoning & Intelligent Automation",
    "description": "Production-grade Agentic AI Framework with Vision + LLM + Event Sourcing. Supports local LLMs, LangGraph orchestration, and HITL safety.",
    "url": "https://github.com/MahdiNavaei/aria",
    "repo": "https://github.com/MahdiNavaei/aria",
    "stars": "Check current stars",
    "license": "MIT",
    "language": "Python",
    "tags": ["agentic-ai", "llm", "langgraph", "automation", "local-llm", "vision-language-model"],
}


def create_awesome_list_pr(repo_owner: str, repo_name: str, file_path: str, entry: str, section: str) -> Dict:
    """Create a PR to an Awesome List repository."""
    print(f"\n[INFO] Preparing PR for {repo_owner}/{repo_name}")
    print(f"  File: {file_path}")
    print(f"  Section: {section}")
    print(f"  Entry: {entry}")
    
    return {
        "repo": f"{repo_owner}/{repo_name}",
        "file": file_path,
        "section": section,
        "entry": entry,
        "instructions": f"""
1. Fork https://github.com/{repo_owner}/{repo_name}
2. Clone your fork
3. Edit {file_path}
4. Add entry under '{section}' section:
   {entry}
5. Commit and push
6. Create PR with title: "Add ARIA - Production-grade Agentic AI Framework"
        """
    }


def main():
    """Main entry point."""
    print("=" * 70)
    print("ARIA - Submit Everywhere Script")
    print("=" * 70)
    
    # 1. GitHub Topics (manual if API fails)
    print("\n[1] GitHub Topics")
    print("   Status: Manual (API requires different scope)")
    print("   Action: Go to https://github.com/MahdiNavaei/aria/settings")
    print("   → Topics → Add these topics:")
    for topic in TOPICS[:10]:  # Show first 10
        print(f"      - {topic}")
    print(f"      ... and {len(TOPICS) - 10} more (see scripts/improve-discoverability.py)")
    
    # 2. Awesome Lists PRs
    print("\n[2] Awesome Lists - Pull Requests")
    awesome_lists = [
        {
            "owner": "langchain-ai",
            "repo": "awesome-langchain",
            "file": "README.md",
            "section": "Agent Frameworks",
            "entry": f"- [ARIA]({ARIA_INFO['repo']}) - {ARIA_INFO['description']}"
        },
        {
            "owner": "langchain-ai",
            "repo": "awesome-langgraph",
            "file": "README.md",
            "section": "Projects Built with LangGraph",
            "entry": f"- [ARIA]({ARIA_INFO['repo']}) - Production-grade Agentic AI system using LangGraph for stateful orchestration, with cognitive architecture (Brain/Eye/Hand/Memory) and event sourcing."
        },
        {
            "owner": "eugeneyan",
            "repo": "awesome-ai-agents",
            "file": "README.md",
            "section": "Frameworks",
            "entry": f"- [ARIA]({ARIA_INFO['repo']}) - {ARIA_INFO['description']}"
        },
        {
            "owner": "jupyter-naas",
            "repo": "awesome-ai-agents",
            "file": "README.md",
            "section": "Frameworks",
            "entry": f"- [ARIA]({ARIA_INFO['repo']}) - Adaptive Reasoning & Intelligent Automation: {ARIA_INFO['description']}"
        },
    ]
    
    for i, list_info in enumerate(awesome_lists, 1):
        pr_info = create_awesome_list_pr(
            list_info["owner"],
            list_info["repo"],
            list_info["file"],
            list_info["entry"],
            list_info["section"]
        )
        print(f"\n   [{i}] {pr_info['repo']}")
        print(f"       {pr_info['instructions']}")
    
    # 3. AI Tool Directories
    print("\n[3] AI Tool Directories - Form Submissions")
    directories = [
        {
            "name": "Futurepedia",
            "url": "https://www.futurepedia.io/submit",
            "description": "Submit ARIA as AI Agent/Automation Framework"
        },
        {
            "name": "There's An AI For That",
            "url": "https://theresanaiforthat.com/submit/",
            "description": "Submit as AI Agent / Developer Tools"
        },
        {
            "name": "AI Tools Directory",
            "url": "https://aitoolsdirectory.com/submit",
            "description": "Submit as AI Framework / Automation"
        },
        {
            "name": "TopAI.tools",
            "url": "https://topai.tools/submit",
            "description": "Submit with standard description"
        },
        {
            "name": "AIHunters",
            "url": "https://aihunters.com/submit",
            "description": "Submit as Agentic AI Framework"
        },
    ]
    
    for i, directory in enumerate(directories, 1):
        print(f"\n   [{i}] {directory['name']}")
        print(f"       URL: {directory['url']}")
        print(f"       Description: {directory['description']}")
        print(f"       Use standard description from scripts/submit-to-directories.md")
    
    # 4. PyPI Preparation
    print("\n[4] PyPI Publishing")
    print("   Status: Ready (pyproject.toml configured)")
    print("   To publish:")
    print("   1. Get PyPI API token from https://pypi.org/manage/account/token/")
    print("   2. Run: python -m build")
    print("   3. Run: python -m twine upload dist/*")
    print("   Or use: scripts/publish-pypi.sh (create this script)")
    
    # 5. Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"\n✅ Completed:")
    print("   - Repository description updated")
    print("   - pyproject.toml configured with keywords")
    print("   - Documentation files created")
    
    print(f"\n📋 Manual Actions Required:")
    print("   1. Add Topics via GitHub UI (see [1] above)")
    print("   2. Create PRs to Awesome Lists (see [2] above)")
    print("   3. Submit to AI Directories (see [3] above)")
    print("   4. Publish to PyPI (see [4] above)")
    
    print(f"\n📝 Files Created:")
    print("   - scripts/improve-discoverability.py")
    print("   - scripts/awesome-lists-submissions.md")
    print("   - scripts/submit-to-directories.md")
    print("   - scripts/submit-everywhere.py (this file)")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
