import json

from locust import HttpUser, between, task


class CapsuleUser(HttpUser):
    wait_time = between(1, 5)  # Users wait 1-5 seconds between tasks

    @task
    def generate_reasoning_capsule(self):
        """Simulates a user generating a reasoning capsule."""
        headers = {
            "Content-Type": "application/json",
            "X-API-Key": "test-key",  # Use a valid API key for the test
        }
        payload = {
            "prompt": "Analyze the ethical implications of autonomous drone surveillance in public spaces.",
            "model": "gpt-4-test",
        }
        self.client.post(
            "/reasoning/generate",
            data=json.dumps(payload),
            headers=headers,
            name="/reasoning/generate",
        )
