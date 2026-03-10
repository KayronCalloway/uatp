#!/usr/bin/env python3
import os

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Print environment variables
print(f"OPENAI_API_KEY exists: {'OPENAI_API_KEY' in os.environ}")
print(f"UATP_SIGNING_KEY exists: {'UATP_SIGNING_KEY' in os.environ}")
print(f"UATP_VERIFY_KEY exists: {'UATP_VERIFY_KEY' in os.environ}")
