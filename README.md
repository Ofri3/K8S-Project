# Kubernetes Project

## Overview
This project demonstrates deploying a Python application and a static Nginx-based website in a Kubernetes cluster using Minikube. The project covers Kubernetes deployments, services, ingress resources, resource restrictions, and autoscaling with Horizontal Pod Autoscaler (HPA). Additionally, it includes integrating Helm charts, managing sensitive data using Kubernetes Secrets, and setting up a CI/CD pipeline using Jenkins and Argo CD.

## Prerequisites
Ensure you have the following installed:
- [Minikube](https://minikube.sigs.k8s.io/docs/start/)
- [kubectl](https://kubernetes.io/docs/tasks/tools/)
- [Helm](https://helm.sh/docs/intro/install/)
- [Docker](https://docs.docker.com/get-docker/)
- [Jenkins](https://www.jenkins.io/doc/book/installing/)
- [Git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)
- [Argo CD](https://argo-cd.readthedocs.io/en/stable/getting_started/)

## Dependencies
The Python app requires the following dependencies (specified in requirements.txt):

```bash
flask~=3.0.3
telebot~=0.0.5
pillow~=10.3.0
loguru~=0.7.2
matplotlib~=3.8.4
pylint
```

## Project Structure
```bash
K8S-Project/
├── .github/
│   └── workflows/                # Contains CI workflows
├── .img/                         # Contains images used for documentation or visuals
├── argocd-config/                # Configuration files for ArgoCD
│   ├── app.yaml
│   ├── clusterrole-binding.yaml
│   └── clusterrole.yaml
├── jenkins-agent/                # Dockerfile for Jenkins agent
│   └── Dockerfile
├── jenkins-server-k8s/           # Jenkins server running in Kubernetes
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── ingress.yaml
│   ├── serviceaccount.yaml
│   ├── role.yaml
│   ├── rolebinding.yaml
│   ├── cluster-role-binding.yaml
│   └── volume.yaml
├── my-python-app-chart/          # Helm chart for the Python app
│   ├── Chart.yaml
│   ├── values.yaml
│   └── templates/
│       ├── deployment.yaml
│       └── _helpers.tpl
├── nginx/                        # Files related to the Nginx service
│   ├── Dockerfile
│   ├── nginx-config.yaml
│   ├── nginx-deployment.yaml
│   ├── nginx-hpa.yaml
│   ├── nginx-ingress.yaml
│   ├── nginx-pvc.yaml
│   ├── nginx-service.yaml
│   ├── index.html
│   └── nginx.conf
├── polybot/                      # Python app (Telegram bot) source code
│   ├── photos/
│   ├── test/
│   ├── app.py
│   ├── bot.py
│   ├── image_proc.py
│   ├── app-deployment.yaml
│   ├── Dockerfile
│   └── requirements.txt
├── compose.yaml                  # Docker Compose configuration
├── build.Jenkinsfile             # Jenkins pipeline definition
├── .gitignore
├── .pylintrc
└── README.md
```


## Setup Instructions

## 1. Install and Start Minikube
1. Install Minikube by following the [official documentation](https://minikube.sigs.k8s.io/docs/start/).
2. Start your Minikube cluster:
   ```bash
   minikube start
   ```
3. Verify the installation:
   ```bash
    kubectl cluster-info
   ```
   
## 2. Deploy Applications

This project includes two applications: a Python app and a static Nginx website.

**Deploy Nginx Application**

1. Apply the Nginx deployment configuration:
   ```bash
    kubectl apply -f nginx/nginx-deployment.yaml -n demo
   ```
2. Deploy the Nginx service:
   ```bash
    kubectl apply -f nginx/nginx-service.yaml -n demo
    ```
   
**Deploy Python Application**

Apply the Python app deployment:
   ```bash
    kubectl apply -f polybot/app-deployment.yaml -n demo
```

## 3. Configure Ingress

1. Create the Ingress resource for the Nginx service:
   ```bash
    kubectl apply -f nginx/nginx-ingress.yaml -n demo
    ```
2. Verify the Ingress is working by sending an HTTP request:
   ```bash
    curl http://<minikube-ip>
    ```
## 4. Configure Resource Limits and Probes
   
Apply resource limits, readiness, and liveness probes to ensure proper health checks and CPU/memory constraints:
   ```bash
    kubectl apply -f nginx/nginx-deployment.yaml -n demo
```    
## 5. Horizontal Pod Autoscaler (HPA)
Apply the HPA configuration to autoscale the Nginx deployment based on CPU utilization:
   ```bash
kubectl apply -f nginx/nginx-hpa.yaml -n demo
```    

## 6. Persistent Volume for Nginx

1. Create the Persistent Volume Claim (PVC):
   ```bash
    kubectl apply -f nginx/nginx-pvc.yaml -n demo
   ```    
2. Update the Nginx deployment to mount the PVC:
   ```bash
    kubectl apply -f nginx/nginx-deployment.yaml -n demo
    ```    
## 7. Managing Secrets with Kubernetes
The Telegram bot requires a <code>telegram-token</code> to operate. The token is securely managed through Kubernetes Secrets.

1. The secret was created in Kubernetes:
   ```bash
   kubectl create secret generic telegram-token-secret --from-literal=TELEGRAM_TOKEN=<your-token>
   ```    
2. The Helm <code>values.yaml</code> and <code>deployment.yaml</code> files were updated to reference this secret:
```bash
env:
  - name: TELEGRAM_TOKEN
    valueFrom:
      secretKeyRef:
        name: {{ .Values.env.TELEGRAM_TOKEN_SECRET }}
        key: TELEGRAM_TOKEN
```

3. In the <code>app-deployment.yaml</code>, the secret is injected as an environment variable to securely pass the token to the Python application.

## 8. Helm Chart Conversion
All Kubernetes templates have been converted into Helm charts for easy management and deployment.
1. Create a Helm chart structure:
   ```bash
    helm create my-python-app-chart
    ```    
2. Modify <code>Chart.yaml</code>, <code>values.yaml</code>, and the templates in <code>my-python-app-chart/templates</code> to match the Kubernetes YAML configuration.
3. Install the Helm chart:
   ```bash
    helm install my-python-app my-python-app-chart
    ```    
## 9. CI/CD with Jenkins and Kubernetes
Jenkins was installed and configured as part of the CI/CD process, running inside a pod in the Minikube cluster.
- The Jenkins server was deployed via Kubernetes and is running inside a pod.
- You can find the deployment and configuration files for Jenkins in the <code>jenkins-server-k8s</code> directory.
- Jenkins was set up to run jobs using a custom Jenkins agent, which was built from a Dockerfile in the <code>jenkins-agent</code> directory.

### Set up Jenkins Kubernetes Cloud

Set up Jenkins Kubernetes Cloud by creating a service account and configuring Jenkins to connect to the Minikube cluster. 

1. Create a 'jenkins' namespace. 
2. Install the Jenkins Server in the 'jenkins' namespace as pod with volume , if you want to save your Jenkins server configuration you will need to transfer the data from under /var/jenkins to the pod jenkins volume.
5. Check if the pod of the Jenkins Server is running, then use the following command to access the jenkins srver from localhost:8080: <code>kubectl port-forward -n jenkins svc/jenkins-service 8080:80</code>
4. Install Kubernetes plugin in Jenkins and restart Jenkins.
6. Configure Kubernetes cloud in your Jenkins under “Clouds” in the "Manage Jenkins" configuration to use Kubernetes cluster in that specific namepsace.

**Commands you will need to use to configure the cloud:**
- Create service account to jenkins namespace:
```bash
kubectl create serviceaccount jenkins --namespace=jenkins
```
- This command will return the secret for the service account that we created that you will use as credentials value in the Jenkins configure cloud:
```bash
kubectl describe secret $(kubectl describe serviceaccount jenkins --namespace=jenkins | grep Token | awk '{print $2}') --namespace=jenkins
```
- This command will create a role binding of admin with the service account jenkins:
```bash
kubectl create rolebinding jenkins-admin-binding --clusterrole=admin --serviceaccount=jenkins:jenkins --namespace=jenkins
```

## 10. Argo CD Integration for GitOps

Argo CD was used to implement a GitOps workflow, where application deployments are managed automatically through Argo CD.

### 1. Argo CD Installation:

- Installed using Helm with the following commands:
```bash
helm repo add argo https://argoproj.github.io/argo-helm
helm install argo-cd argo/argo-cd -n argocd --create-namespace
```
- Configured Argo CD to track the Git repository and automate the deployment of the Kubernetes resources.

### 2. Application Deployment with Argo CD:

- The application resources (deployment, service, ingress) were defined in a Helm chart and managed by Argo CD.
- After pushing changes to the Git repository, Argo CD automatically detects the updates and deploys them to the Kubernetes cluster.

### 3. Testing Argo CD:

- To test the Argo CD deployment, make changes to the application code, commit the changes, and push them to the repository. Argo CD will handle the rest of the deployment process.

## Testing and Verifying
Check the status of your deployments:
```bash
kubectl get deployments -n demo
```
Verify that the pods are running:
```bash
kubectl get pods -n demo
```
Verify that the services and Ingress are properly configured:
```bash
kubectl get svc -n demo
kubectl get ingress -n demo
```

## Where I Ran the Project

The project was deployed and tested using Minikube, a local Kubernetes cluster. The Jenkins server was deployed as a pod within the Minikube cluster, and it orchestrates the CI/CD pipeline. 

The pipeline uses a custom Jenkins agent built using the Dockerfile in the <code>jenkins-agent</code> directory.

Additionally, the application’s sensitive data, such as the Telegram bot token, was securely managed using Kubernetes Secrets, injected through the Helm chart. 

Argo CD was also integrated to implement GitOps for automatic application deployment from the Git repository.

**Feel free to adapt or expand upon these changes if necessary! Let me know if you'd like any further modifications.**