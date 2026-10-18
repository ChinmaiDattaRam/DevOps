# Lab 7 - Jenkins CI Automation

This exercise introduces Jenkins as a CI server and asks you to install it,
unlock the dashboard, and complete the initial setup. It does not specify a
Jenkinsfile or a Pipeline job; the pipeline exercise is in Lab 6.

## Run Jenkins locally

From the DevOps workspace in PowerShell:

```powershell
docker start devops-jenkins
docker exec devops-jenkins cat /var/jenkins_home/secrets/initialAdminPassword
```

For a new installation, use the Jenkins Docker image and publish only
localhost-bound ports. Open <http://localhost:8080>, unlock Jenkins with the
initial password, and install the suggested plugins. Do not expose an
unauthenticated Jenkins instance to a network. Stop only the exercise
container with `docker stop devops-jenkins` when finished.

## Results

Screenshots show the [Jenkins dashboard](./screenshots/01-jenkins-dashboard.jpg)
and [configured exercise jobs with their latest successful builds](./screenshots/02-jenkins-jobs-ready.jpg).
