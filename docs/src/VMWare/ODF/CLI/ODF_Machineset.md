
The base requirement is that there are 3 nodes able to host ODF. According to [the official documentation](https://access.redhat.com/documentation/en-us/red_hat_openshift_data_foundation/4.12/html/planning_your_deployment/infrastructure-requirements_rhodf) ODF requires 30 vCPUs and 72G of ram across the 3 nodes. Below is a sample MachineSet definition that will meet the minimum requirements with a little bit of extra ram for overhead. Regardless of whether you install via the UI or the CLI, if you are creating machinesets for your ODF deployment the following Machineset can be used. 

> [!NOTE]
> The following definition needs to be adjusted for your environment 

```
apiVersion: machine.openshift.io/v1beta1
kind: MachineSet
metadata:
  name: odf-workers-0
  namespace: openshift-machine-api
spec:
  replicas: 3
  selector:
    matchLabels:
      machine.openshift.io/cluster-api-cluster: <infra_id>
      machine.openshift.io/cluster-api-machineset: <infra_id>-worker-0
  template:
    metadata:
      labels:
        machine.openshift.io/cluster-api-machine-role: worker
        machine.openshift.io/cluster-api-machine-type: worker
        machine.openshift.io/cluster-api-machineset: <infra_id>-worker-0
    spec:
      metadata:
        labels:
          storage: odf
          cluster.ocs.openshift.io/openshift-storage: ''
          node-role.kubernetes.io/infra: ''
          node-role.kubernetes.io/worker: ''
      providerSpec:
        value:
          numCoresPerSocket: 1
          diskGiB: 120
          snapshot: ''
          userDataSecret:
            name: worker-user-data
          memoryMiB: 28672
          credentialsSecret:
            name: vsphere-cloud-credentials
          network:
            devices:
              - networkName: VM Network
          numCPUs: 11
          kind: VSphereMachineProviderSpec
          workspace:
            datacenter: <datacentre>
            datastore: /<datacentre>/datastore/OCP
            folder: /<datacentre>/vm/<infra_id>
            resourcePool: /<datacentre>/<resource pool>
            server: vcenter.x86experts.com
          template: <infra_id>-rhcos-generated-region-generated-zone
          apiVersion: machine.openshift.io/v1beta1
      taints:
        - effect: NoSchedule
          key: node.ocs.openshift.io/storage
          value: 'true'
```

> [!WARNING]
> If you chose not to use a Machineset, you must label the nodes yourself. 