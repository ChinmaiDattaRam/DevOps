# Lab 8 - Jenkins Hello World Freestyle Job

The script prints the expected Jenkins greeting. Create a Freestyle project in
Jenkins and add a shell build step that invokes `bash hello-world.sh`.

## Code: `hello-world.sh`

```bash
#!/bin/bash
echo "Hello, Jenkins!"
```

## Run and verify locally

```powershell
bash .\hello-world.sh
```

Expected output:

```text
Hello, Jenkins!
```

For the Jenkins exercise, create a Freestyle job named `HelloWorld`, add
`bash hello-world.sh` as its build command (or check out this folder from SCM),
save it, select **Build Now**, and verify that the console ends in
`Finished: SUCCESS`.

## Results

Screenshots show the [Hello World job console](./screenshots/01-hello-world-console.jpg)
and [a successful rerun](./screenshots/02-helloworld-build-success.jpg).
