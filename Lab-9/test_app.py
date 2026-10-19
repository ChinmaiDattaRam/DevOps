import os
import time
import unittest
from urllib.error import URLError
from urllib.request import urlopen

from app import app


class TestApp(unittest.TestCase):
    def test_home(self):
        app_url = os.environ.get("APP_URL")
        if app_url:
            last_error = None
            for _ in range(15):
                try:
                    with urlopen(app_url, timeout=2) as response:
                        body = response.read().decode("utf-8")
                        status = response.status
                    break
                except URLError as error:
                    last_error = error
                    time.sleep(1)
            else:
                self.fail(f"Deployed application did not become ready: {last_error}")
        else:
            response = app.test_client().get("/")
            body = response.get_data(as_text=True)
            status = response.status_code

        print(body)
        self.assertEqual(status, 200)
        self.assertEqual(body, "Hello, Jenkins Multi-Stage Pipeline!")


if __name__ == "__main__":
    unittest.main()
