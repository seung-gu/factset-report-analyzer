#!/usr/bin/env python3
"""Setup Google Cloud credentials file from environment variable."""

import os
import json
import sys

creds_json = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS_JSON', '')
if not creds_json:
    print("❌ GOOGLE_APPLICATION_CREDENTIALS_JSON is empty")
    sys.exit(1)

# Validate JSON
try:
    json.loads(creds_json)
    print("✅ JSON is valid")
except json.JSONDecodeError as e:
    print(f"❌ Invalid JSON: {e}")
    print(f"First 200 chars: {creds_json[:200]}")
    sys.exit(1)

# Write file
output_path = 'gen-lang-client-0316337343-f310859556ae.json'
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(creds_json)

# Verify file was written correctly
with open(output_path, 'r', encoding='utf-8') as f:
    file_content = f.read()
    try:
        json.loads(file_content)
        print("✅ File written and verified successfully")
    except json.JSONDecodeError as e:
        print(f"❌ File verification failed: {e}")
        print(f"First 200 chars of file: {file_content[:200]}")
        sys.exit(1)

print(f"✅ Google Cloud credentials file created: {output_path}")

