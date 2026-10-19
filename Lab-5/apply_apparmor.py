import docker
import time

client = docker.from_env()

print("Building image from Dockerfile...")
client.images.build(path=".", tag="flask-apparmor")

print("Running container with AppArmor profile...")
container = client.containers.run(
    "flask-apparmor",
    ports={'5000/tcp': 5000},
    security_opt=["apparmor=my-apparmor-profile"],
    detach=True
)
print(f"Container started: {container.short_id}")

time.sleep(2)

print("Inspecting container to verify AppArmor profile...")
info = client.api.inspect_container(container.id)
print(f"AppArmor profile applied: {info['HostConfig']['SecurityOpt']}")
print(f"AppArmor profile (runtime): {info['AppArmorProfile']}")

print("Stopping the container...")
container.stop()
container.remove()