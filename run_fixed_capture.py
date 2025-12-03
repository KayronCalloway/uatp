#!/usr/bin/env python3
"""
Run the Fixed Conversation Capture Service
"""

import subprocess
import sys
import time


def main():
    print("🚀 Starting Fixed Conversation Capture Service")
    print("=" * 60)
    print()
    print("This service will:")
    print("✅ Monitor clipboard for conversation content")
    print("✅ Auto-detect platform (Claude Desktop, Windsurf, Claude Code)")
    print("✅ Calculate significance scores for conversations")
    print("✅ Send high-value conversations to UATP system")
    print("✅ Create attribution capsules automatically")
    print()
    print("💡 How to use:")
    print("   1. Copy any conversation content (Cmd+C)")
    print("   2. Service automatically detects and processes it")
    print("   3. Check dashboard at http://localhost:3000 for results")
    print()
    print("⏹️ Press Ctrl+C to stop the service")
    print("=" * 60)
    print()

    try:
        # Run the fixed capture service
        subprocess.run([sys.executable, "fixed_conversation_capture.py"], check=True)
    except KeyboardInterrupt:
        print("\n⏹️ Service stopped by user")
    except Exception as e:
        print(f"\n❌ Error running service: {e}")


if __name__ == "__main__":
    main()
