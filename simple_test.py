#!/usr/bin/env python3

import subprocess

# Put test content in clipboard
test_content = "User: How do I implement UATP conversation capture? Assistant: You need to fix the clipboard monitoring and platform detection systems."

subprocess.run(["pbcopy"], input=test_content.encode())
print("✅ Test conversation content placed in clipboard")
print("💡 Now run: python3 fixed_conversation_capture.py")
print("📋 The service should detect and process this content automatically")
