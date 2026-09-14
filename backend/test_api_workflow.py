import json
import urllib.request


URL = "http://127.0.0.1:8000/api/v1/workflows"

payload = {
    "name": "API Persistence Test",
    "description": "Testing FastAPI workflow persistence",
    "workflow_type": "document_processing",
    "version": 1,
    "is_active": True,
    "config": {
        "nodes": []
    }
}

data = json.dumps(payload).encode("utf-8")

request = urllib.request.Request(
    URL,
    data=data,
    headers={
        "Content-Type": "application/json",
    },
    method="POST",
)

print("=" * 60)
print("FASTAPI WORKFLOW POST TEST")
print("=" * 60)

try:
    with urllib.request.urlopen(request) as response:
        body = response.read().decode("utf-8")

        print()
        print("STATUS:", response.status)

        print()
        print("RESPONSE:")
        print(body)

except Exception as exc:
    print()
    print("ERROR:", repr(exc))

print()
print("=" * 60)