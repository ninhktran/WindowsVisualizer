import io
import unittest

from fastapi.testclient import TestClient
from PIL import Image

from server.main import app


class WindowsVisualizerApiTests(unittest.TestCase):
    def test_health(self):
        response = TestClient(app).get("/api/health")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["ok"])

    def test_analyze_and_render_fallback(self):
        image = io.BytesIO()
        Image.new("RGB", (320, 240), "#d8d1c1").save(image, format="JPEG")
        image.seek(0)
        client = TestClient(app)
        response = client.post(
            "/api/analyze",
            files={"upload": ("room.jpg", image, "image/jpeg")},
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "ready")
        job_id = payload["job_id"]

        render = client.post(
            f"/api/jobs/{job_id}/render",
            json={"style": "double_hung", "use_ai": False},
        )
        self.assertEqual(render.status_code, 200)
        result = client.get(render.json()["result_url"])
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.headers["content-type"], "image/jpeg")


if __name__ == "__main__":
    unittest.main()
