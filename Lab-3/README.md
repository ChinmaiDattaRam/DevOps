# Lab 3 - Scale a Flask App with a ReplicaSet

This lab builds a flash-sale Flask API, runs three replicas, scales to five,
deletes a Pod, and verifies that the ReplicaSet restores the desired count.

## Code

### `app.py`

```python
from flask import Flask, request
import random
import socket
import time

app = Flask(__name__)


@app.get("/")
def homepage():
    return {
        "message": "Welcome to Big Sale!",
        "pod": socket.gethostname(),
        "ts": time.time(),
    }


@app.get("/buy")
def buy():
    item = random.choice(["Smartphone", "Shoes", "Headphones", "Laptop"])
    user = request.args.get("user", f"user{random.randint(1, 1000)}")
    return {
        "status": "success",
        "item": item,
        "user": user,
        "served_by_pod": socket.gethostname(),
        "time": time.strftime("%H:%M:%S"),
    }


@app.get("/health")
def health():
    return {"status": "healthy", "pod": socket.gethostname()}
```

### `requirements.txt`

```text
Flask>=3.1,<4
gunicorn>=23,<24
```

### `Dockerfile`

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
EXPOSE 5000
CMD ["gunicorn", "--bind=0.0.0.0:5000", "app:app", "--workers=1", "--threads=2"]
```

### `flashsale-replicaset.yaml`

```yaml
apiVersion: apps/v1
kind: ReplicaSet
metadata:
  name: flashsale-rs
  labels:
    app: flashsale
spec:
  replicas: 3
  selector:
    matchLabels:
      app: flashsale
  template:
    metadata:
      labels:
        app: flashsale
    spec:
      containers:
        - name: flashsale
          image: flashsale:1.0
          imagePullPolicy: Never
          ports:
            - containerPort: 5000
          readinessProbe:
            httpGet:
              path: /health
              port: 5000
            periodSeconds: 5
          livenessProbe:
            httpGet:
              path: /health
              port: 5000
            periodSeconds: 10
          resources:
            requests:
              cpu: 100m
              memory: 128Mi
            limits:
              cpu: 500m
              memory: 256Mi
---
apiVersion: v1
kind: Service
metadata:
  name: flashsale-svc
spec:
  selector:
    app: flashsale
  ports:
    - name: http
      port: 80
      targetPort: 5000
  type: ClusterIP
```

## Run

Run from this directory in PowerShell:

```powershell
docker build -t flashsale:1.0 .
minikube -p devops-labs image load flashsale:1.0
kubectl --context=devops-labs apply -f flashsale-replicaset.yaml
kubectl --context=devops-labs wait --for=condition=Ready pod -l app=flashsale --timeout=180s
kubectl --context=devops-labs get rs,pods -l app=flashsale
kubectl --context=devops-labs scale rs/flashsale-rs --replicas=5
kubectl --context=devops-labs wait --for=condition=Ready pod -l app=flashsale --timeout=180s
$pod = kubectl --context=devops-labs get pod -l app=flashsale -o jsonpath='{.items[0].metadata.name}'
kubectl --context=devops-labs delete pod $pod
kubectl --context=devops-labs wait --for=jsonpath='{.status.readyReplicas}'=5 rs/flashsale-rs --timeout=120s
kubectl --context=devops-labs get pods -l app=flashsale -o wide
```

## Results

Screenshots show the application responses and scaling/recovery checkpoints:
[health check](./screenshots/01-flashsale-health.jpg),
[flash-sale purchase](./screenshots/02-flashsale-purchase.jpg),
[five-replica state](./screenshots/03-replicaset-scaled-five.jpg), and
[deleted-Pod recovery](./screenshots/04-replicaset-self-healing.jpg).

## Exercise questions

1. The initial ReplicaSet has 3 replicas.
2. It creates 3 Pods.
3. Scaling to 5 creates 2 additional Pods.
4. Deleting one Pod causes the ReplicaSet to create a replacement.
5. The ReplicaSet controller continuously reconciles the actual Pod count with
   the desired replica count.
6. This exercise uses one Minikube node.
7. All five Pods run on that single node.
