#!/usr/bin/env python3
"""
Test Clipboard Capture by Simulating Conversation Content
"""

import subprocess
import time
import requests

def put_in_clipboard(content):
    """Put content in clipboard."""
    process = subprocess.Popen(['pbcopy'], stdin=subprocess.PIPE)
    process.communicate(content.encode())

def test_capture():
    """Test the capture system."""
    
    print("🧪 Testing Fixed Conversation Capture")
    print("=" * 50)
    
    # Test conversation
    test_conversation = """User: I'm implementing a UATP system with real-time conversation capture. The current system creates empty timeout sessions instead of capturing real conversations. How do I fix cross-platform integration for Claude Desktop and Windsurf?