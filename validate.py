#!/usr/bin/env python3
"""
Quick validation script to test the project structure.
"""

import sys
from pathlib import Path

def validate_project():
    """Validate that all required files and directories exist."""
    
    print("🔍 Validating project structure...\n")
    
    # Required directories
    dirs = [
        "app",
        "app/routes",
        "app/tools", 
        "app/services",
        "app/utils",
        "data",
        "vectorstore"
    ]
    
    # Required files
    files = [
        "app/__init__.py",
        "app/main.py",
        "app/agent.py",
        "app/routes/__init__.py",
        "app/routes/chat.py",
        "app/tools/__init__.py",
        "app/tools/db_tools.py",
        "app/tools/rag_tools.py",
        "app/tools/stripe_tools.py",
        "app/services/__init__.py",
        "app/services/database.py",
        "app/services/llm_engine.py",
        "app/services/vectorstore.py",
        "app/utils/__init__.py",
        "app/utils/config.py",
        "data/db.sqlite",
        ".env.example",
        "requirements.txt",
        "README.md"
    ]
    
    # Check directories
    print("📁 Checking directories:")
    all_good = True
    for dir_path in dirs:
        path = Path(dir_path)
        if path.exists() and path.is_dir():
            print(f"  ✅ {dir_path}")
        else:
            print(f"  ❌ {dir_path} - MISSING")
            all_good = False
    
    print("\n📄 Checking files:")
    for file_path in files:
        path = Path(file_path)
        if path.exists() and path.is_file():
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ {file_path} - MISSING")
            all_good = False
    
    # Try importing key modules
    print("\n🐍 Testing Python imports:")
    try:
        from app.utils.config import settings
        print(f"  ✅ Config loaded - App: {settings.app_name}")
    except Exception as e:
        print(f"  ❌ Config import failed: {e}")
        all_good = False
    
    try:
        from app.services.database import get_db_connection
        print("  ✅ Database service imported")
    except Exception as e:
        print(f"  ❌ Database import failed: {e}")
        all_good = False
    
    try:
        from app.tools.db_tools import db_tools
        print(f"  ✅ DB tools imported ({len(db_tools)} tools)")
    except Exception as e:
        print(f"  ❌ DB tools import failed: {e}")
        all_good = False
    
    try:
        from app.tools.rag_tools import rag_tools
        print(f"  ✅ RAG tools imported ({len(rag_tools)} tools)")
    except Exception as e:
        print(f"  ❌ RAG tools import failed: {e}")
        all_good = False
    
    try:
        from app.tools.stripe_tools import stripe_tools
        print(f"  ✅ Stripe tools imported ({len(stripe_tools)} tools)")
    except Exception as e:
        print(f"  ❌ Stripe tools import failed: {e}")
        all_good = False
    
    # Summary
    print("\n" + "="*50)
    if all_good:
        print("✅ All checks passed! Project is ready.")
        print("\nNext steps:")
        print("  1. Copy .env.example to .env and configure")
        print("  2. Make sure Ollama is running: ollama serve")
        print("  3. Start the server: python -m app.main")
        print("  4. Visit: http://localhost:8000/docs")
        return 0
    else:
        print("❌ Some checks failed. Please review the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(validate_project())
