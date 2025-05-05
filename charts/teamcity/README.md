# teamcity

A Helm chart for deploying JetBrains TeamCity Server in Kubernetes

You can configure teamcity self-hosted with following method using this helm chart:

- Method-1: HA: Main and Secondary
  - Secondary node acts as a passive, read-only standby
  - Ensures High Availability (failover)

- Method-2: Load-Distributed Nodes 
  - Multiple nodes with distinct roles (e.g., build queue, VCS polling)
  - High scalability and flexibility

- Method-3: Main + Secondary (Active with Responsibilities)
  - Secondary node takes on extra tasks (e.g., build triggering, VCS polling)
  - Better resource utilization, Load distribution, Easier future scaling

Improvement needed from Jetbrain side:
- Currently there is manual step to register main and secondary node. 
  didn't find any documents to automate `“Startup confirmation is required”`

## Pre-requisite

- Storage class with `ReadWriteMany` to shared data volume with main and secondary

## Requirements

| Repository | Name | Version |
|------------|------|---------|
| https://charts.bitnami.com/bitnami | postgresql | 12.2.6 |

## Values

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| imagePullSecrets | list | `[]` |  |
| ingress.annotations | object | `{}` |  |
| ingress.enabled | bool | `true` |  |
| ingress.hosts[0] | string | `"teamcity.example.com"` |  |
| ingress.tls[0].hosts[0] | string | `"teamcity.example.com"` |  |
| ingress.tls[0].secretName | string | `"teamcity-tls"` |  |
| main.affinity.podAntiAffinity.requiredDuringSchedulingIgnoredDuringExecution[0].labelSelector.matchExpressions[0].key | string | `"role"` |  |
| main.affinity.podAntiAffinity.requiredDuringSchedulingIgnoredDuringExecution[0].labelSelector.matchExpressions[0].operator | string | `"In"` |  |
| main.affinity.podAntiAffinity.requiredDuringSchedulingIgnoredDuringExecution[0].labelSelector.matchExpressions[0].values[0] | string | `"secondary"` |  |
| main.affinity.podAntiAffinity.requiredDuringSchedulingIgnoredDuringExecution[0].labelSelector.matchExpressions[0].values[1] | string | `"main"` |  |
| main.affinity.podAntiAffinity.requiredDuringSchedulingIgnoredDuringExecution[0].topologyKey | string | `"kubernetes.io/hostname"` |  |
| main.annotations | object | `{}` |  |
| main.image.name | string | `"jetbrains/teamcity-server"` |  |
| main.image.tag | string | `""` |  |
| main.nodeId | string | `"main"` |  |
| main.nodeSelector | object | `{}` |  |
| main.podAnnotations | object | `{}` |  |
| main.resources.requests.cpu | string | `"400m"` |  |
| main.resources.requests.memory | string | `"1500Mi"` |  |
| main.responsibilities[0] | string | `"MAIN_NODE"` |  |
| main.responsibilities[1] | string | `"CAN_PROCESS_USER_DATA_MODIFICATION_REQUESTS"` |  |
| main.tolerations | list | `[]` |  |
| persistence.dataDir.accessMode | string | `"ReadWriteMany"` |  |
| persistence.dataDir.annotations | object | `{}` |  |
| persistence.dataDir.size | string | `"4Gi"` |  |
| persistence.dataDir.storageClass | string | `""` |  |
| persistence.enabled | bool | `true` |  |
| persistence.logDir.accessMode | string | `"ReadWriteOnce"` |  |
| persistence.logDir.annotations | object | `{}` |  |
| persistence.logDir.size | string | `"4Gi"` |  |
| persistence.logDir.storageClass | string | `""` |  |
| podSecurityContext.fsGroup | int | `1000` |  |
| podSecurityContext.fsGroupChangePolicy | string | `"OnRootMismatch"` |  |
| podSecurityContext.runAsGroup | int | `1000` |  |
| podSecurityContext.runAsUser | int | `1000` |  |
| postgresql.auth.existingSecret | string | `"teamcity-db-secret"` |  |
| postgresql.enabled | bool | `true` |  |
| secondary.affinity.podAntiAffinity.requiredDuringSchedulingIgnoredDuringExecution[0].labelSelector.matchExpressions[0].key | string | `"role"` |  |
| secondary.affinity.podAntiAffinity.requiredDuringSchedulingIgnoredDuringExecution[0].labelSelector.matchExpressions[0].operator | string | `"In"` |  |
| secondary.affinity.podAntiAffinity.requiredDuringSchedulingIgnoredDuringExecution[0].labelSelector.matchExpressions[0].values[0] | string | `"secondary"` |  |
| secondary.affinity.podAntiAffinity.requiredDuringSchedulingIgnoredDuringExecution[0].labelSelector.matchExpressions[0].values[1] | string | `"main"` |  |
| secondary.affinity.podAntiAffinity.requiredDuringSchedulingIgnoredDuringExecution[0].topologyKey | string | `"kubernetes.io/hostname"` |  |
| secondary.annotations | object | `{}` |  |
| secondary.image.name | string | `"jetbrains/teamcity-server"` |  |
| secondary.image.tag | string | `""` |  |
| secondary.nodeSelector | object | `{}` |  |
| secondary.podAnnotations | object | `{}` |  |
| secondary.replicas | int | `3` |  |
| secondary.resources.requests.cpu | string | `"400m"` |  |
| secondary.resources.requests.memory | string | `"1500Mi"` |  |
| secondary.responsibilities[0] | string | `"CAN_CHECK_FOR_CHANGES"` |  |
| secondary.responsibilities[1] | string | `"CAN_PROCESS_BUILD_TRIGGERS"` |  |
| secondary.responsibilities[2] | string | `"CAN_PROCESS_USER_DATA_MODIFICATION_REQUESTS"` |  |
| secondary.responsibilities[3] | string | `"CAN_PROCESS_BUILD_MESSAGES"` |  |
| secondary.tolerations | list | `[]` |  |
| securityContext.runAsNonRoot | bool | `true` |  |
| securityContext.runAsUser | int | `1000` |  |
| service.port | int | `8111` |  |
| service.type | string | `"ClusterIP"` |  |
| serviceAccount.annotations | object | `{}` |  |
| serviceAccount.create | bool | `true` |  |
| serviceAccount.name | string | `"teamcity"` |  |
| teamcityGlobalConfigurations.additionalServerOpts | string | `""` |  |
| teamcityGlobalConfigurations.dataDirPath | string | `"/storage/data"` |  |
| teamcityGlobalConfigurations.database | object | `{}` |  |
| teamcityGlobalConfigurations.logDirPathPrefix | string | `"/logs"` |  |
| teamcityGlobalConfigurations.startupProperties."teamcity.startup.maintenance" | bool | `false` |  |
| teamcityGlobalConfigurations.xmxValue | string | `"1024m"` |  |

----------------------------------------------
Autogenerated from chart metadata using [helm-docs v1.14.2](https://github.com/norwoodj/helm-docs/releases/v1.14.2)
