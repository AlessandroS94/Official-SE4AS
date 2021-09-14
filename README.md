<img src="https://github.com/kubernetes/kubernetes/raw/master/logo/logo.png" width="100">

----
# Official-SE4AS
SE4AS Project
## Table of contents
* [General info](#general-info)
* [Technologies](#technologies)
* [Setup](#setup)

## General info
This project is realized for the exam.
	
## Technologies
Project is created with:
* Kubernetes
* Docker
* Minikube
	
## Setup
To run this project, install it locally using kubernetes and minikube
First of all install docker desktop and minikube.
This process is tested for MacOS:
1. Install docker Desktop with kubernetes
2. Install minikube:
```
$ brew install minikube
$ minikube start 
$ minikube start --memory 2048
$ minikube dashboard
```

At the and do this command:
```
$ git clone https://github.com/AlessandroS94/Official-SE4AS.git

$ cd Official-SE4AS

$ cd Mosquitto-Broker && kubectl apply -f Mosquitto2 && cd ..

$ cd Sensor && kubectl apply -f deployment.yaml && cd ..

$ cd Planning && kubectl apply -f deployment.yaml && cd ..

$ cd Management && kubectl apply -f deployment.yaml && cd ..

$ cd Executing && kubectl apply -f deployment.yaml && cd ..

cd Analyzing && kubectl apply -f deployment.yaml && cd ..

After deployed all deployment run this command 

$ kubectl port-forward service/mosquitto 27000:9001

$ minikube service angular-service

```

With last command you can connect with the angular-dashboard to console
