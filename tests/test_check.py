from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

response = client.post("/api/schedule", json={"run_id": "inspect_structure"})
print(response.status_code)
print(response.json())