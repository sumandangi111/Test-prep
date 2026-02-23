# Deploy Education App to Kubernetes

## 📌 Project Overview
This project demonstrates deployment of an Education Quiz Application using Docker and Kubernetes on AWS EC2. The application is containerized, deployed with multiple replicas, exposed using NodePort, and updated using rolling updates to achieve zero downtime.

---

## 🎯 Objectives
- Containerize the education quiz application  
- Deploy the application on Kubernetes  
- Expose application externally using NodePort  
- Demonstrate rolling updates for seamless upgrades  

---

## 🛠️ Technologies Used
- Python Flask – Backend development  
- HTML/CSS – Frontend  
- Docker – Containerization  
- DockerHub – Image registry  
- AWS EC2 – Cloud infrastructure  
- Kubernetes (K3s) – Container orchestration  
- GitHub – Version control  

---

## 🏗️ Architecture / Workflow
Developer → GitHub → Docker Build → DockerHub → AWS EC2 → Kubernetes → Pods → Service → Users

---

## 🚀 Deployment Steps

### 1️⃣ Build Docker Image
docker build -t sumanddevops/quiz-app:v1 
### 2️⃣ Push Image to DockerHub
docker login
docker push sumanddevops/quiz-app:v1
### 3️⃣ Deploy on Kubernetes
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
### 4️⃣ Verify Deployment
kubectl get pods
kubectl get svc

Access application:

http://<EC2-IP>:30007
### 🔄 Rolling Update

To update application version:

- docker build -t sumanddevops/quiz-app:v2 .
- docker push sumanddevops/quiz-app:v2
- kubectl set image deployment/quiz-app quiz-container=sumanddevops/quiz-app:v2
- kubectl rollout status deployment/quiz-app
- kubectl rollout history deployment/quiz-app

### 📊 Features

- Containerized deployment
- Kubernetes orchestration
- Multiple replicas for high availability
- External access using NodePort
- Zero downtime rolling updates

### ⚠️ Challenges Faced

- ImagePullBackOff error
- Port accessibility issues
- Kubernetes configuration complexity

#### ✅ Results

- Application successfully deployed on Kubernetes

- Rolling updates implemented

- External access enabled

- High availability achieved

### 🔮 Future Scope

- Integrate CI/CD using GitHub Actions

- Deploy on AWS EKS

- Add monitoring with Prometheus and Grafana

- Implement auto-scaling
