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
