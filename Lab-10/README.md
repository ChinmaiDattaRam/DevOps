# Lab 10 - Multi-Node Minikube, Product Catalog, and Shopping Cart

This lab creates a dedicated three-node cluster and deploys a product catalog
(two replicas) plus a shopping cart (three replicas). Required Pod anti-affinity
spreads each application's replicas across distinct nodes. The applications
have separate, runnable Dockerfiles and Deployments/Services.

## Code

### `product_catalog.py`

```python
from flask import Flask, jsonify

app = Flask(__name__)
products = [
    {"id": 1, "name": "Laptop", "price": 1200},
    {"id": 2, "name": "Phone", "price": 800},
    {"id": 3, "name": "Headphones", "price": 150},
]


@app.get("/products")
def get_products():
    return jsonify(products)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
```

### `shopping_cart.py`

```python
from flask import Flask, jsonify, request

app = Flask(__name__)
cart = []


@app.get("/cart")
def get_cart():
    return jsonify(cart)


@app.post("/cart")
def add_to_cart():
    item = request.json
    cart.append(item)
    return jsonify(cart), 201


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
```

### `Dockerfile.product`

```dockerfile
FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir "Flask>=3.1,<4"
COPY product_catalog.py .
EXPOSE 80
CMD ["python", "product_catalog.py"]
```

### `Dockerfile.shopping`

```dockerfile
FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir "Flask>=3.1,<4"
COPY shopping_cart.py .
EXPOSE 80
CMD ["python", "shopping_cart.py"]
```

### `product_catalog_deployment.yaml`

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: product-catalog
  namespace: default
spec:
  replicas: 2
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 0
      maxUnavailable: 1
  selector:
    matchLabels:
      app: product-catalog
  template:
    metadata:
      labels:
        app: product-catalog
    spec:
      affinity:
        podAntiAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            - labelSelector:
                matchLabels:
                  app: product-catalog
              topologyKey: kubernetes.io/hostname
      containers:
        - name: product-catalog
          image: product-catalog:latest
          imagePullPolicy: Never
          ports:
            - containerPort: 80
---
apiVersion: v1
kind: Service
metadata:
  name: product-catalog-service
  namespace: default
spec:
  selector:
    app: product-catalog
  ports:
    - protocol: TCP
      port: 80
      targetPort: 80
  type: NodePort
```

### `shopping_cart_deployment.yaml`

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: shopping-cart
  namespace: default
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 0
      maxUnavailable: 1
  selector:
    matchLabels:
      app: shopping-cart
  template:
    metadata:
      labels:
        app: shopping-cart
    spec:
      affinity:
        podAntiAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            - labelSelector:
                matchLabels:
                  app: shopping-cart
              topologyKey: kubernetes.io/hostname
      containers:
        - name: shopping-cart
          image: shopping-cart:latest
          imagePullPolicy: Never
          ports:
            - containerPort: 80
---
apiVersion: v1
kind: Service
metadata:
  name: shopping-cart-service
  namespace: default
spec:
  selector:
    app: shopping-cart
  ports:
    - protocol: TCP
      port: 80
      targetPort: 80
  type: NodePort
```

## Run

The dedicated profile below avoids stopping or deleting another Minikube
cluster. From PowerShell:

```powershell
minikube start -p devops-multinode --driver=docker --nodes=3 --keep-context
docker build -t product-catalog:latest -f Dockerfile.product .
docker build -t shopping-cart:latest -f Dockerfile.shopping .
minikube -p devops-multinode image load product-catalog:latest
minikube -p devops-multinode image load shopping-cart:latest
kubectl --context=devops-multinode apply -f product_catalog_deployment.yaml
kubectl --context=devops-multinode apply -f shopping_cart_deployment.yaml
kubectl --context=devops-multinode rollout status deployment/product-catalog --timeout=240s
kubectl --context=devops-multinode rollout status deployment/shopping-cart --timeout=240s
kubectl --context=devops-multinode get pods -o wide
kubectl --context=devops-multinode get services
```

Both Service resources are NodePort Services and can be opened with
`minikube -p devops-multinode service product-catalog-service --url` and
`minikube -p devops-multinode service shopping-cart-service --url`. Keep the
forwarding terminal open while using each URL. Use `minikube -p
devops-multinode delete` only when you intend to remove this exercise's
cluster.

## Results

Screenshots show the [product catalog](./screenshots/01-product-catalog.jpg),
[shopping cart](./screenshots/02-shopping-cart.jpg),
[three Ready nodes](./screenshots/03-cluster-nodes-ready.jpg),
[replica placement](./screenshots/04-replica-placement.jpg),
[NodePort Services](./screenshots/05-nodeport-services.jpg),
[catalog response](./screenshots/06-product-catalog-response.jpg), and
[cart GET/POST flow](./screenshots/07-cart-get-post.jpg).
