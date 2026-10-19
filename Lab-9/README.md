# Lab 9 - Jenkins Multi-Stage Python Pipeline

The pipeline builds an isolated virtual environment, installs the exercise
Flask version, runs the unit test, copies the app to a mock deployment
directory, starts that deployed copy, and tests its live HTTP response. A
post-build cleanup step stops the background process.

## Code

### `app.py`

```python
import os

from flask import Flask

app = Flask(__name__)


@app.route("/")
def home():
    return "Hello, Jenkins Multi-Stage Pipeline!"


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        debug=True,
        port=int(os.environ.get("PORT", "5000")),
        use_reloader=False,
    )
```

### `test_app.py`

```python
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
```

### `requirements.txt`

```text
Flask==2.1.2
Werkzeug<2.3
```

The Werkzeug cap preserves compatibility with the exercise's older Flask
release.

### `Jenkinsfile`

```groovy
pipeline {
    agent any
    options {
        disableConcurrentBuilds()
    }
    stages {
        stage('Build') {
            steps {
                dir('Lab-9') {
                    sh 'python3 -m venv .venv'
                    sh '.venv/bin/python -m pip install --upgrade pip'
                    sh '.venv/bin/pip install -r requirements.txt'
                }
            }
        }
        stage('Test') {
            steps {
                dir('Lab-9') {
                    sh '.venv/bin/python -m unittest discover -s . -v'
                }
            }
        }
        stage('Deploy') {
            steps {
                dir('Lab-9') {
                    sh '''
                        rm -rf python-app-deploy
                        mkdir -p python-app-deploy
                        cp app.py python-app-deploy/
                        test -f python-app-deploy/app.py
                    '''
                }
            }
        }
        stage('Run Application') {
            steps {
                dir('Lab-9') {
                    sh '''
                        if [ -f app.pid ]; then
                            kill "$(cat app.pid)" 2>/dev/null || true
                            rm -f app.pid
                        fi
                        APP_PORT=$(.venv/bin/python -c 'import socket; s=socket.socket(); s.bind(("127.0.0.1", 0)); print(s.getsockname()[1]); s.close()')
                        echo "$APP_PORT" > app.port
                        PORT="$APP_PORT" nohup .venv/bin/python python-app-deploy/app.py \
                            >app.log 2>&1 </dev/null &
                        echo $! > app.pid
                    '''
                }
            }
        }
        stage('Test Application') {
            steps {
                dir('Lab-9') {
                    sh 'APP_URL="http://127.0.0.1:$(cat app.port)/" .venv/bin/python -m unittest discover -s . -v'
                }
            }
        }
    }
    post {
        always {
            dir('Lab-9') {
                sh '''
                    if [ -f app.pid ]; then
                        kill "$(cat app.pid)" 2>/dev/null || true
                        rm -f app.pid
                    fi
                    rm -f app.port
                '''
            }
        }
        success {
            echo 'Pipeline completed successfully.'
        }
        failure {
            echo 'Pipeline failed; inspect the stage output.'
        }
    }
}
```

## Run locally

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m unittest discover -s . -v
```

The Jenkinsfile uses POSIX shell syntax. In Jenkins, create a Pipeline job and
load the script from SCM with Script Path `Lab-9/Jenkinsfile`, then run **Build
Now**. Jenkins agents must have Python 3, `venv`, and permission to bind a
localhost TCP port. The final test uses `APP_URL` to exercise the deployed copy
over HTTP rather than only retesting the source module.

## Results

Screenshots show the [pipeline console](./screenshots/01-multistage-pipeline.jpg),
[Build](./screenshots/02-pipeline-build-stage.jpg),
[Test](./screenshots/03-pipeline-test-stage.jpg),
[Deploy](./screenshots/04-pipeline-deploy-stage.jpg),
[Run Application](./screenshots/05-pipeline-run-stage.jpg),
[Test Application](./screenshots/06-pipeline-application-test.jpg), and
[successful completion](./screenshots/07-pipeline-success.jpg).
