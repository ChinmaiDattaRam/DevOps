# Lab 4 - Docker Bridge Networking

This lab connects a Flask API, MySQL, and Redis to a user-defined bridge
network. The MySQL image is initialized with an exercise-only password.

## Code

### `app.py`

```python
from flask import Flask, jsonify

app = Flask(__name__)


@app.get("/about")
def about():
    return jsonify(
        name="Simple REST API",
        version="1.0",
        description="This is a simple REST API built with Flask.",
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
```

### `requirements.txt`

```text
Flask>=3.1,<4
```

### `Dockerfile`

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
EXPOSE 5001
CMD ["python", "app.py"]
```

## Run and verify (PowerShell)

```powershell
docker network create --driver bridge lab4-bridge
docker build -t lab4-flask .
docker run -d --name lab4-mysql --network lab4-bridge -e MYSQL_ROOT_PASSWORD=lab-only-password mysql:8.4
docker run -d --name lab4-redis --network lab4-bridge redis:7-alpine
docker run -d --name lab4-flask --network lab4-bridge -p 5001:5001 lab4-flask
Invoke-RestMethod http://127.0.0.1:5001/about
docker exec lab4-flask python -c "import socket; [(print(f'{host}: {socket.getaddrinfo(host, port)[0][4][0]}:{port}'), socket.create_connection((host, port), timeout=5).close()) for host, port in [('lab4-mysql',3306),('lab4-redis',6379)]]"
docker network inspect lab4-bridge
```

The Flask container joins the same named network as both databases. Docker's
embedded DNS resolves the container names; the connection check verifies that
MySQL and Redis accept TCP connections. Name resolution and TCP checks replace
the exercise's `ping` checks because the slim Flask image does not include ping.

Clean up only the resources created for this lab:

```powershell
docker rm -f lab4-flask lab4-mysql lab4-redis
docker network rm lab4-bridge
```

## Results

Screenshots show the [Flask API response](./screenshots/01-flask-about.jpg),
[bridge network](./screenshots/02-bridge-network.jpg),
[three running containers](./screenshots/03-network-containers.jpg), and
[DNS/TCP connectivity checks](./screenshots/04-dns-tcp-and-api.jpg).

## Exercise questions

1. `--network` (the `--net` shorthand) attaches a container to the selected
   Docker network.
2. Containers on a user-defined bridge network can reach one another by
   container name or IP address.
3. A bridge network isolates containers on a private network; host networking
   shares the host's network stack.
4. Publish a container port to the host with `-p host-port:container-port`.
