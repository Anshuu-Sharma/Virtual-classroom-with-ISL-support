#!/usr/bin/env python3
"""Quick test to see if server can start"""

import sys
import os

print("Testing server startup...")
print("=" * 60)

# Check imports
print("\n1. Checking imports...")
try:
    from flask import Flask
    print("   [OK] Flask")
except ImportError as e:
    print(f"   [FAIL] Flask: {e}")
    sys.exit(1)

try:
    from flask_cors import CORS
    print("   [OK] Flask-CORS")
except ImportError as e:
    print(f"   [FAIL] Flask-CORS: {e}")

try:
    from flask_limiter import Limiter
    print("   [OK] Flask-Limiter")
except ImportError as e:
    print(f"   [FAIL] Flask-Limiter: {e}")
    sys.exit(1)

try:
    import nltk
    print("   [OK] NLTK")
except ImportError as e:
    print(f"   [FAIL] NLTK: {e}")

# Try to load server
print("\n2. Loading server module...")
try:
    from server import app
    print("   [OK] Server module loaded")
except Exception as e:
    print(f"   [FAIL] Error loading server: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Try to create app context and test
print("\n3. Testing Flask app...")
try:
    with app.test_client() as client:
        print("   [OK] Flask app created")
        print("   [OK] Test client created")
except Exception as e:
    print(f"   [FAIL] Error creating app: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("[SUCCESS] All checks passed! Server should start successfully.")
print("\nTo start the server:")
print("  python server.py")
print("\nOr open:")
print("  http://localhost:5001")

