# Lab 9 - Jenkins Multi-Stage Python Pipeline

The pipeline builds an isolated virtual environment, installs Flask, runs the
unit test, copies the source into a mock deployment directory, starts that
copy, reruns the application test, and stops the background process in a
post-build cleanup step.

## Code

### `app.py`

```python
from flask import Flask

app = Flask(__name__)


@app.get("/")
def home():
    return "Hello, Jenkins Multi-Stage Pipeline!"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
```

### `test_app.py`

```python
import unittest

from app import app


class TestApp(unittest.TestCase):
    def test_home(self):
        response = app.test_client().get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.get_data(as_text=True),
            "Hello, Jenkins Multi-Stage Pipeline!",
        )


if __name__ == "__main__":
    unittest.main()
```

### `requirements.txt`

```text
Flask>=3.1,<4
```

### `Jenkinsfile`

```groovy
pipeline {
    agent any
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
                    sh '.venv/bin/python -m unittest discover -v'
                }
            }
        }
        stage('Deploy') {
            steps {
                dir('Lab-9') {
                    sh '''
                        rm -rf python-app-deploy
                        mkdir -p python-app-deploy
                        cp app.py requirements.txt python-app-deploy/
                    '''
                    archiveArtifacts artifacts: 'python-app-deploy/**', fingerprint: true
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
                        nohup .venv/bin/python python-app-deploy/app.py \
                            >/dev/null 2>&1 </dev/null &
                        echo $! > app.pid
                    '''
                }
            }
        }
        stage('Test Application') {
            steps {
                dir('Lab-9') {
                    sh '.venv/bin/python -m unittest discover -v'
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
.\.venv\Scripts\python.exe -m unittest discover -v
New-Item -ItemType Directory -Force python-app-deploy | Out-Null
Copy-Item app.py,requirements.txt .\python-app-deploy\
```

In Jenkins, create a Pipeline job and load the script from SCM with Script Path
`Lab-9/Jenkinsfile`, then run **Build Now**. Jenkins agents must have Python 3
and `venv` available.

## Results

Screenshots show the [pipeline console](./screenshots/01-multistage-pipeline.jpg),
[Build](./screenshots/02-pipeline-build-stage.jpg),
[Test](./screenshots/03-pipeline-test-stage.jpg),
[Deploy](./screenshots/04-pipeline-deploy-stage.jpg),
[Run Application](./screenshots/05-pipeline-run-stage.jpg),
[Test Application](./screenshots/06-pipeline-application-test.jpg), and
[successful completion](./screenshots/07-pipeline-success.jpg).
