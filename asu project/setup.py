#!/usr/bin/env python3
"""
Setup script for Flask Chatbot Application
"""

import os
import subprocess
import sys

def install_requirements():
    """Install required packages from requirements.txt"""
    print("Installing required packages...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Requirements installed successfully!")
        print("📦 Installed packages:")
        print("   - Flask (Web framework)")
        print("   - Google Generative AI (Gemini API)")
        print("   - PyPDF2 (PDF processing)")
        print("   - python-docx (Word document processing)")
        print("   - Werkzeug (File upload handling)")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing requirements: {e}")
        return False
    return True

def check_api_key():
    """Check if Google API key is set"""
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        print("⚠️  Warning: GOOGLE_API_KEY environment variable not set!")
        print("Please set your Google API key:")
        print("Windows: set GOOGLE_API_KEY=your_api_key_here")
        print("Linux/Mac: export GOOGLE_API_KEY=your_api_key_here")
        return False
    else:
        print("✅ Google API key is set!")
        return True

def main():
    print("⚡ Setting up Lumora AI - Lightning Fast Intelligence...")
    print("=" * 60)
    
    # Install requirements
    if not install_requirements():
        sys.exit(1)
    
    # Check API key
    api_key_set = check_api_key()
    
    print("\n" + "=" * 60)
    if api_key_set:
        print("✅ Lumora AI setup complete! Ready for lightning-fast responses!")
        print("   Run: python main.py")
    else:
        print("⚠️  Setup complete, but please set your Google API key before running.")
        print("   After setting the API key, run: python main.py")
    
    print("\n⚡ Lumora AI will be available at: http://localhost:5000")
    print("🚀 Experience lightning-fast AI responses!")

if __name__ == "__main__":
    main()
