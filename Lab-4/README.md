# Lab 4 - Docker Networking with Multiple Containers

This lab follows the exercise: create a user-defined bridge, build the Flask
API image, connect Flask, MySQL, and Redis to the bridge, and use `ping` by
container name from the Flask container. The Flask image includes
`iputils-ping`, which the exercise's original slim image did not install.

## Code

### `app.py`

```python
from flask import Flask, jsonify

app = Flask(__name__)


@app.route("/about", methods=["GET"])
def about():
    return jsonify({
        "name": "Simple REST API",
        "version": "1.0",
        "description": "This is a simple REST API built with Flask."
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=5001)
```

### `requirements.txt`

```text
Flask==2.0.1
Werkzeug<2.3
```

The Werkzeug cap preserves compatibility with this older Flask release.

### `Dockerfile`

```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN apt-get update \
    && apt-get install -y --no-install-recommends iputils-ping \
    && rm -rf /var/lib/apt/lists/*
COPY app.py .
EXPOSE 5001
CMD ["python", "app.py"]
```

## Run the exercise (PowerShell)

Run these commands from this directory:

```powershell
docker network create --driver bridge my-bridge-net
docker build -t flask-api .
docker run -d --name mysql --net=my-bridge-net -e MYSQL_ROOT_PASSWORD=lab-only-password mysql:latest
docker run -d --name redis --net=my-bridge-net redis:latest
docker run -d --name flask --net=my-bridge-net -p 5001:5001 flask-api
Invoke-RestMethod http://127.0.0.1:5001/about
docker exec -it flask bash
```

At the Flask container prompt, run the two checks from the exercise:

```bash
ping -c 3 mysql
ping -c 3 redis
```

For non-interactive verification, run the same commands from PowerShell:

```powershell
docker exec flask ping -c 3 mysql
docker exec flask ping -c 3 redis
```

The MySQL root password is set because current MySQL images require one when
initializing the container.

## Clean up

```powershell
docker stop mysql redis flask
docker rm mysql redis flask
docker network rm my-bridge-net
```

## Exercise questions

1. `--net` connects a container to the selected Docker network.
2. Containers on a user-defined bridge can communicate by container name or
   IP address.
3. A bridge network isolates containers on a private network; host networking
   shares the host's network stack.
4. Publish a container port to the host with `-p host-port:container-port`.

## Results

Screenshots show the [Flask API response](./screenshots/01-flask-about.jpg),
[bridge network](./screenshots/02-bridge-network.jpg),
[three running containers](./screenshots/03-network-containers.jpg), and the
[container-name ping checks](./screenshots/04-ping-connectivity.jpg).
