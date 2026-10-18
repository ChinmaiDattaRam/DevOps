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
