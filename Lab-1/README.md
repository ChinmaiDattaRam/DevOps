# Lab 1 - Kubernetes: Hello Pod

## Exercise check

The original Lab-1 files ran Flask on port 15000. That is the next exercise, not
this exercise, which specifically requires an Nginx Pod. Those files have been
replaced with the Nginx Pod and NodePort Service below.

## Code: `nginx-pod.yaml`

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: hello-k8s
  labels:
    app: hello-k8s
spec:
  containers:
    - name: nginx
      image: nginx:1.27-alpine
      ports:
        - containerPort: 80
---
apiVersion: v1
kind: Service
metadata:
  name: hello-k8s
spec:
  type: NodePort
  selector:
    app: hello-k8s
  ports:
    - port: 80
      targetPort: 80
```

## Run

Use a dedicated Minikube profile so this lab does not replace another cluster:

```powershell
minikube start -p devops-labs --driver=docker --nodes=1 --keep-context
kubectl --context=devops-labs apply -f nginx-pod.yaml
kubectl --context=devops-labs get pod,service hello-k8s
kubectl --context=devops-labs port-forward service/hello-k8s 18080:80
```

In another terminal, verify the Nginx welcome page:

```powershell
Invoke-WebRequest http://127.0.0.1:18080
```

Stop the port-forward with Ctrl+C. The cluster and lab resources are left
available for Labs 2 and 3; remove only this lab's resources with
`kubectl --context=devops-labs delete -f nginx-pod.yaml`.

## Results

Screenshots show the Nginx response and the Kubernetes setup checkpoints:
[welcome page](./screenshots/01-nginx-welcome.jpg),
[Pod running](./screenshots/02-pod-running.jpg), and
[NodePort Service](./screenshots/03-nodeport-service.jpg).
