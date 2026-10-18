# Lab 2 - Deploy a Flask App on Minikube

## Exercise check

The existing Flask route, port (15000), Deployment, and NodePort Service match
Exercise 2. The Dockerfile previously used Python 3.8 while installing the
latest Flask and did not expose the application port. It now uses Python 3.12,
installs the pinned dependency range from `requirements.txt`, and documents
port 15000. The manifest is unchanged.

## Code

### `app.py`

```python
from flask import Flask

app = Flask(__name__)


@app.route("/")
def home():
    return "Hello from Flask on Kubernetes!"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=15000)
```

### `Dockerfile`

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .

EXPOSE 15000

CMD ["python", "app.py"]
```

### `requirements.txt`

```text
Flask>=3.1,<4
```

### `flask-deployment.yaml`

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: flask-app
spec:
  replicas: 1
  selector:
    matchLabels:
      app: flask-app
  template:
    metadata:
      labels:
        app: flask-app
    spec:
      containers:
        - name: flask-app
          image: flask-app:latest
          imagePullPolicy: Never
          ports:
            - containerPort: 15000

---
apiVersion: v1
kind: Service
metadata:
  name: flask-app-service
spec:
  selector:
    app: flask-app
  ports:
    - port: 15000
      targetPort: 15000
  type: NodePort
```

## Run

Run from this directory in PowerShell:

```powershell
docker build -t flask-app:latest .
minikube -p devops-labs image load flask-app:latest
kubectl --context=devops-labs apply -f flask-deployment.yaml
kubectl --context=devops-labs rollout status deployment/flask-app --timeout=180s
kubectl --context=devops-labs port-forward service/flask-app-service 15000:15000
```

In another terminal, check the exact response:

```powershell
(Invoke-WebRequest http://127.0.0.1:15000).Content
```

Expected: `Hello from Flask on Kubernetes!`

## Results

Screenshots show the Flask response and deployment checkpoints:
[Flask service response](./screenshots/01-flask-service.jpg),
[Deployment ready](./screenshots/02-deployment-ready.jpg), and
[Pod running](./screenshots/03-flask-pod-running.jpg).

## Exercise questions

1. `minikube service flask-app-service --url` provides a usable URL for the
   Service running in Minikube.
2. Minikube locates the Service and prints a URL that forwards traffic to it.
3. `targetPort` selects the port on which the container listens.
4. `port` is the Service port; `targetPort` is the application/container port.
5. Run `minikube service flask-app-service --url`, then request the printed URL.
6. With Minikube's Docker driver, the forwarding process must remain running
   while the URL is in use.
7. `--url` gives the caller a ready-to-use address instead of requiring it to
   construct one from cluster details.
8. Use `kubectl expose` or apply a Service manifest.
9. Minikube provides a local Kubernetes cluster for development and testing.
10. `kubectl` is the CLI used to create, inspect, scale, and manage Kubernetes
    resources.
