For this guide the prerequisites are as follows:

1. An up-to-date OpenShift 4.x cluster
2. 8Gi of ram & 2 vCPUs per Quay application pod
3. Object storage

For more information please see the [official documentation](https://access.redhat.com/documentation/en-us/red_hat_quay/3.9/html/deploying_the_red_hat_quay_operator_on_openshift_container_platform/operator-concepts#operator-prereq)

> [!NOTE]
> Resource requirements vary greatly based on the components installed and managed via the operator. Below find the minimum expected resources for a minimal Quay installation:
> Quay Redis: 4vCPU & 16 Gi Ram
> Quay Database (postgresql): 0.5 vCPU & 2Gi Ram
> Quay ConfigEditor: 0.2 vCPU & 500Mi Ram
>
> Additional components such as clair, HPA, etc have even greater resource requirements.

Aside from the hardware requirements, the following software related requirements need to met:

1. A namespace/project in which the quay objects will reside.
2. Access to the Operator Catalog