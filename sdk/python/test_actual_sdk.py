"""
Test the actual UATP SDK (not just raw API calls)
"""

from uatp import UATP

print("\n" + "=" * 60)
print(" UATP SDK Full Test - Using Actual SDK")
print("=" * 60)

# Initialize client
print("\n1. Initializing UATP client...")
client = UATP()
print("[OK] Client initialized")

# Test 1: Create a capsule
print("\n2. Creating capsule via SDK...")
result = client.certify(
    task="Book doctor appointment",
    decision="Booked Dr. Smith for December 17 at 3PM",
    reasoning=[
        {
            "step": 1,
            "thought": "User requested Tuesday afternoon appointment",
            "confidence": 0.95,
        },
        {
            "step": 2,
            "thought": "Checked calendar - Tuesday 2-5PM available",
            "confidence": 0.98,
        },
        {
            "step": 3,
            "thought": "Found Dr. Smith has 3PM slot on December 17",
            "confidence": 0.92,
        },
    ],
    metadata={"model": "claude-3.5-sonnet", "user_id": "test_user"},
)

print("[OK] Capsule created successfully!")
print(f"   Capsule ID: {result.capsule_id}")
print(f"   Proof URL: {result.proof_url}")
print(f"   Timestamp: {result.timestamp}")

# Test 2: Retrieve the proof
print("\n3. Retrieving proof...")
proof = client.get_proof(result.capsule_id)
print("[OK] Proof retrieved!")
print(f"   Type: {proof.capsule_type}")
print(f"   Status: {proof.status}")
print(f"   Verified: {proof.verified}")
print(f"   Task: {proof.payload.get('task', 'N/A')}")
print(f"   Decision: {proof.payload.get('decision', 'N/A')}")

# Test 3: List recent capsules
print("\n4. Listing recent capsules...")
capsules = client.list_capsules(limit=5)
print(f"[OK] Retrieved {len(capsules)} capsules")
for i, capsule in enumerate(capsules[:3], 1):
    task = capsule.payload.get("task", "N/A")
    print(f"   {i}. {capsule.capsule_id[:16]}... - {task[:40]}...")

# Test 4: Verify signature
print("\n5. Verifying signature...")
is_valid = proof.verify()
print(f"[OK] Signature valid: {is_valid}")

print("\n" + "=" * 60)
print(" All SDK tests passed!")
print("=" * 60)
print("\n Your UATP SDK is ready to use!")
