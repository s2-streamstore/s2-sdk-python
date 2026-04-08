"""Documentation examples for SDK Overview page.

These snippets are extracted by the docs build script.

Run with: python examples/docs/overview.py
Requires: S2_ACCESS_TOKEN environment variable
"""

# ANCHOR: create-client
import os

from s2_sdk import S2

client = S2(os.environ["S2_ACCESS_TOKEN"])

basin = client.basin("my-basin")
stream = basin.stream("my-stream")
# ANCHOR_END: create-client

print("Client created successfully")
