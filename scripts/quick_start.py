#!/usr/bin/env python3
"""
Quick Start Script
Guides users through initial setup and running the application
"""

import os
import sys
import subprocess
import platform
from pathlib import Path


def print_header(text):
    """Print formatted header"""
    print("\n" + "=" * 60)
    print(text)
    print("=" * 60 + "\n")


def check_python():
    """Check Python version"""
    print("Checking Python version...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 9):
        print(f"  [ERROR] Python 3.9+ required. Found: {version.major}.{version.minor}")
        return False
    print(f"  [OK] Python {version.major}.{version.minor}.{version.micro}")
    return True


def check_dependencies():
    """Check if dependencies are installed"""
    print("Checking dependencies...")
    
    required = ['flask', 'torch', 'nltk']
    missing = []
    
    for package in required:
        try:
            __import__(package)
            print(f"  [OK] {package}")
        except ImportError:
            print(f"  [MISSING] {package}")
            missing.append(package)
    
    if missing:
        print(f"\n  Missing packages: {', '.join(missing)}")
        return False
    return True


def install_dependencies():
    """Install dependencies"""
    print("\nInstalling dependencies...")
    print("This may take a few minutes...\n")
    
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ])
        print("\n  [SUCCESS] Dependencies installed!")
        return True
    except subprocess.CalledProcessError:
        print("\n  [ERROR] Failed to install dependencies")
        return False


def run_server():
    """Run the Flask server"""
    print_header("Starting Server")
    
    print("Starting Flask server...")
    print("Open your browser to: http://localhost:5001")
    print("Press Ctrl+C to stop the server\n")
    
    try:
        subprocess.run([sys.executable, "server.py"])
    except KeyboardInterrupt:
        print("\n\nServer stopped.")
    except FileNotFoundError:
        print("[ERROR] server.py not found")
        print("Please run this script from the AudioToSignLanguageConverter directory")


def main():
    """Main function"""
    # Change to project directory
    script_dir = Path(__file__).parent.parent
    os.chdir(script_dir)
    
    print_header("Audio-to-Sign-Language Converter - Quick Start")
    
    # Check Python
    if not check_python():
        print("\nPlease install Python 3.9+ and try again.")
        return 1
    
    # Check dependencies
    deps_ok = check_dependencies()
    
    if not deps_ok:
        print("\nDependencies are missing. Installing...")
        if not install_dependencies():
            print("\nFailed to install dependencies. Please install manually:")
            print("  pip install -r requirements.txt")
            return 1
    
    # Verify setup
    print("\nVerifying setup...")
    try:
        subprocess.run([sys.executable, "scripts/verify_setup.py"], check=False)
    except Exception as e:
        print(f"  [WARNING] Verification script failed: {e}")
    
    # Ask user what to do next
    print_header("Setup Complete!")
    
    print("What would you like to do?")
    print("  1. Run the server now")
    print("  2. Exit (run later with: python scripts/quick_start.py)")
    print()
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == "1":
        run_server()
    else:
        print("\nTo run the server later:")
        print("  python scripts/quick_start.py")
        print("  or")
        print("  python server.py")
    
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nExiting...")
        sys.exit(0)

