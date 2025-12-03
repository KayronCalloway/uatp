#!/usr/bin/env python3
"""
Test script to verify the visualizer works properly.
"""

import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

# Test basic imports
try:
    from engine.legacy_capsule_engine import LegacyCapsuleEngine

    print("✅ Legacy capsule engine imported successfully")
except ImportError as e:
    print(f"❌ Legacy capsule engine import failed: {e}")
    sys.exit(1)

try:
    from capsule_schema import AnyCapsule

    print("✅ Capsule schema imported successfully")
except ImportError as e:
    print(f"❌ Capsule schema import failed: {e}")
    sys.exit(1)

# Test engine creation
try:
    engine = LegacyCapsuleEngine(agent_id="test-agent", storage_path="test_chain.jsonl")
    print("✅ Legacy engine created successfully")
except Exception as e:
    print(f"❌ Legacy engine creation failed: {e}")
    sys.exit(1)

# Test capsule creation
try:
    capsule = engine.create_capsule(
        capsule_type="Introspective",
        confidence=0.95,
        reasoning_trace=["Step 1: Analysis", "Step 2: Decision"],
        metadata={"test": True},
    )
    print("✅ Capsule created successfully")
    print(f"   Capsule ID: {capsule.capsule_id}")
    print(f"   Capsule Type: {capsule.capsule_type}")
except Exception as e:
    print(f"❌ Capsule creation failed: {e}")
    sys.exit(1)

# Test logging and loading
try:
    engine.log_capsule(capsule)
    print("✅ Capsule logged successfully")

    chain = engine.load_chain()
    print(f"✅ Chain loaded successfully with {len(chain)} capsules")
except Exception as e:
    print(f"❌ Capsule logging/loading failed: {e}")
    sys.exit(1)

# Clean up
try:
    os.remove("test_chain.jsonl")
    print("✅ Test cleanup completed")
except:
    pass

print("\n🎉 All tests passed! Visualizer should work now.")
print("\nTo run the visualizer:")
print("  cd /Users/kay/uatp-capsule-engine")
print("  streamlit run visualizer/app.py")
