# Lab 5 - Docker Security with AppArmor

This lab packages a Flask service, defines a restrictive AppArmor profile, and
includes Docker SDK scripts for applying the profile and probing denied
operations. **AppArmor enforcement requires a Linux Docker host that has loaded
the named profile.** This host can parse the profile from WSL, but Docker
Desktop's engine does not load that WSL profile, so enforcement cannot be
verified here.

## Code

### `app.py`

```python
from flask import Flask

app = Flask(__name__)


@app.get("/")
def home():
    return (
        "Hello, this is a secure Flask application running inside a Docker "
        "container!"
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
```

### `Dockerfile`

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
EXPOSE 5000
CMD ["python", "app.py"]
```

### `my-apparmor-profile`

Install this profile on the Linux machine running the Docker daemon. The
executable path matches the Python 3.12 slim image used above.

```text
#include <tunables/global>

/usr/local/bin/python3.12 flags=(attach_disconnected,mediate_deleted) {
  #include <abstractions/base>
  network inet stream,
  capability net_bind_service,
  deny capability sys_admin,
  deny /etc/** r,
  deny /var/** rw,
  /app/** r,
  /usr/local/lib/python3.12/** r,
  deny /bin/** x,
  deny /usr/bin/** x,
}
```

### `requirements.txt`

```text
Flask>=3.1,<4
```

### `requirements-admin.txt`

```text
docker>=7,<8
```

### `apply_apparmor.py`

```python
import docker


def main():
    client = docker.from_env()
    client.images.build(path=".", tag="flask-apparmor")
    container = client.containers.run(
        "flask-apparmor",
        ports={"5000/tcp": 5000},
        security_opt=["apparmor=my-apparmor-profile"],
        detach=True,
        remove=True,
    )
    try:
        print(f"Container started: {container.short_id}")
        container_info = client.api.inspect_container(container.id)
        apparmor_profile = container_info["AppArmorProfile"]
        security_options = container_info["HostConfig"]["SecurityOpt"] or []
        print(f"AppArmor profile applied: {security_options}")
        if apparmor_profile != "my-apparmor-profile":
            raise RuntimeError(
                f"Expected my-apparmor-profile to be enforced, "
                f"got {apparmor_profile!r}."
            )
    finally:
        container.stop()
        print("Container stopped")


if __name__ == "__main__":
    main()
```

### `test_restricted_actions.py`

```python
import docker


def main():
    client = docker.from_env()
    container = client.containers.run(
        "flask-apparmor",
        ports={"5000/tcp": 5000},
        security_opt=["apparmor=my-apparmor-profile"],
        detach=True,
        remove=True,
    )
    try:
        print(f"Container started: {container.short_id}")
        profile = client.api.inspect_container(container.id)["AppArmorProfile"]
        print(f"Active AppArmor profile: {profile}")
        if profile != "my-apparmor-profile":
            raise RuntimeError(
                f"AppArmor profile was not enforced; active profile is {profile!r}."
            )
        read_command = [
            "/usr/local/bin/python3.12",
            "-c",
            "print(open('/etc/passwd').read())",
        ]
        exit_code, output = container.exec_run(read_command)
        print(
            "Attempt to read /etc/passwd: "
            f"Exit Code {exit_code}, Output: {output.decode(errors='replace')}"
        )
        if exit_code == 0 or b"root:" in output or b"Permission denied" not in output:
            raise AssertionError("AppArmor did not deny reading /etc/passwd.")

        for command, label in (
            ("/bin/bash", "execute /bin/bash"),
        ):
            exit_code, output = container.exec_run(command)
            print(
                f"Attempt to {label}: Exit Code {exit_code}, "
                f"Output: {output.decode(errors='replace')}"
            )
            if exit_code == 0:
                raise AssertionError(f"AppArmor did not deny {label}.")
    finally:
        container.stop()
        print("Container stopped")


if __name__ == "__main__":
    main()
```

## Run on a supported Linux Docker host

```bash
sudo install -m 0644 my-apparmor-profile /etc/apparmor.d/my-apparmor-profile
sudo apparmor_parser -r /etc/apparmor.d/my-apparmor-profile
docker build -t flask-apparmor .
docker run -d --name flask-apparmor --security-opt apparmor=my-apparmor-profile -p 5000:5000 flask-apparmor
curl http://127.0.0.1:5000/
docker exec flask-apparmor cat /etc/passwd
docker rm -f flask-apparmor
```

Install the Docker SDK with `python -m pip install -r requirements-admin.txt`
on the machine running the Docker CLI. Run `python apply_apparmor.py` and
`python test_restricted_actions.py` only after loading the profile on the
Docker daemon host. These scripts fail if the profile is not active or the
expected restrictions are not enforced.

## Exercise questions

1. AppArmor confines a container process to a defined set of resources and
   actions, adding host-level mandatory access controls.
2. Profiles define permitted and denied file, network, capability, and
   execution operations.
3. Restricting `/etc` and `/var` protects system configuration, secrets, and
   mutable host state from unauthorized reads or writes.
4. AppArmor can restrict capabilities, network access, file writes, and
   executable launches.
5. Inspect the container's `AppArmorProfile` and `HostConfig.SecurityOpt`,
   then verify expected denials. The configured option alone does not prove
   enforcement.

## Results and host limitation

Screenshots show the [Flask response](./screenshots/01-secure-flask.jpg),
[the requested Docker profile option](./screenshots/02-profile-requested.jpg),
and [the host's AppArmor enforcement limitation](./screenshots/03-enforcement-limitation.jpg).
The profile-option screenshot is not evidence that the profile was enforced.
