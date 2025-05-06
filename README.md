# TeamCity Kubernetes Helm Charts

This repository contains two Helm charts for deploying and automating JetBrains TeamCity in Kubernetes:

```
charts/
├── teamcity
└── teamcity-k8s-agent
```

## [`teamcity`](charts/teamcity)

**A Helm chart for deploying JetBrains TeamCity Server in Kubernetes.**

### Supported Cluster Modes

- **Method 1: High Availability (HA)**
  - Main and secondary nodes (secondary is passive/read-only standby)
  - Ensures failover and high availability

- **Method 2: Load-Distributed Nodes**
  - Multiple nodes, each with distinct roles (e.g., build queue, VCS polling)
  - High scalability and flexibility

- **Method 3: Main + Secondary (Active Responsibilities)**
  - Secondary node can take on extra tasks (build triggering, VCS polling)
  - Better resource utilization and easier scaling

### Prerequisites

- A Kubernetes StorageClass supporting `**ReadWriteMany**` for sharing `/data` between main and secondary nodes.
- Domain for teamcity server
- Certs


## [`teamcity-k8s-agent`](charts/teamcity-k8s-agent)

**A Helm chart for automated, on-demand TeamCity agent provisioning in Kubernetes.**

- Automatically registers a Kubernetes cluster with a specific TeamCity project.
- Enables TeamCity to run agents in the configured namespace.
- Removes the need for manual agent registration via the TeamCity UI.

## Installation

### 1. TeamCity Cluster

- **Create a StorageClass** with ReadWriteMany support for shared `/data`.
- **Create a namespace:**
  ```sh
  kubectl create namespace teamcity-cluster
  ```
- **Add database secrets:**  
  The chart includes a PostgreSQL dependency; configure secrets for DB auth.
- **Prepare your values file:**  
  Use `values-ha.yaml` and configure SSL and domain settings as needed.
- **Install the chart:**
  ```sh
  helm install ci ./charts/teamcity -f ./values-ha.yaml --namespace teamcity-cluster
  ```
- **Check pod status and access the UI** to set the admin password.

### 2. Agent Registration

- **Prerequisites:**  
  - Create a TeamCity access token for API automation.
  - Prepare your agent values file (e.g., `agents-values.yaml`).
- **Install the agent registration chart:**
  ```sh
  helm install register-ci-agents charts/teamcity-k8s-agent --namespace teamcity-agents --create-namespace -f agents-values.yaml
  ```
- **Run post-install tests:**
  ```sh
  helm -n teamcity-agents test register-ci-agents
  ```
- **Verify agent registration from the TeamCity UI.**
- Check pods status in `teamcity-agents` namespace.
---

## TODO

Currently following steps are manual on first time setup for teamcity cluster
I didn't find any docs on how to automate this yet. 

 - [ ] Automate license agreement accept button
 - [ ] Automate admin setup
 - [ ] Automate api token creation with granular permissions to use in agent side 
 - [ ] Add tests for failover
 - [ ] Test and document upgrade process

## Enjoy!

- Scalable, automated TeamCity CI/CD on Kubernetes.
- For improvement: Watch for JetBrains updates on automating main/secondary node registration.
