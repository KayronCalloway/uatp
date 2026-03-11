# UATP Examples

Working examples to help you get started with UATP.

## Quick Start

| Example | Purpose | Prerequisites |
|---------|---------|---------------|
| `quickstart.py` | Create and verify your first capsule | Backend running (`python run.py`) |
| `local_signing.py` | Sign capsules without any server | None (fully offline) |
| `verify_standalone.py` | Verify capsules without trusting UATP | None (fully offline) |

## Run Examples

```bash
# Start the backend first (for quickstart.py)
python run.py

# In another terminal
cd examples
python quickstart.py
```

## Example Descriptions

### quickstart.py
The simplest end-to-end example. Creates a capsule with a reasoning chain, stores it via the API, and verifies it. Start here.

### local_signing.py
Demonstrates the zero-trust model. Signs capsules entirely on your device—private keys never touch the network. Use this pattern for sensitive applications.

### verify_standalone.py
Shows how to verify a capsule without any network connection. This is the "don't trust UATP" verification—cryptographic proof that doesn't require trusting any server.

### gold_standard_signing.py
Production-grade signing with all security features enabled: encrypted key storage, RFC 3161 timestamps, and full audit logging.

### enterprise_integration_demo.py
Complex enterprise integration showing authentication, batch processing, and error handling patterns.

### pragmatic_attribution_demo.py
Demonstrates attribution tracking—linking AI outputs to their training data influences.

## Next Steps

- [SDK Documentation](../sdk/python/README.md)
- [API Reference](../docs/api-documentation.md)
- [Trust Model](../TRUST_MODEL.md)
