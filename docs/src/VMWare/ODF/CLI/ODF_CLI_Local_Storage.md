The installation and configuration of the Local Storage Operator entails the creation of 5 objects within OpenShift.

1. A Namespace/Project
2. An Operator Group
3. A Subscription
4. LocalVolumeDiscovery
5. LocalVolumeSet

The first three objects require no modification or customization as they are standard objects which might apply to any environment which supports the Local Storage Operator.


> [!IMPORTANT]
> While it is _technically_ possible to have disks of different sizes available to ODF, this is not supported. Choose disks of a reasonable size for your environment. If you are ever required to grow the storage Red Hat exepcts all disks to be the same size. See the [official documentation](https://access.redhat.com/documentation/en-us/red_hat_openshift_data_foundation/4.13/html-single/scaling_storage/index#scaling-up-storage-by-adding-capacity-to-openshift-data-foundation-nodes-using-local-storage-devices_local-vmware) for more information

## Ensuring Namespace Exists

The first object, the namespace, was listed under the [installation section](#odf-cli-installation). For completeness below is the code to create a namespace for the Local Storage Operator:

```
echo '
---
apiVersion: v1
kind: Namespace
metadata:
  name: openshift-local-storage
' | oc apply -f -
```

## Creating The Operator Group & Subscription

The Operator Group and the Subscription are required in order for the Local Storage Operator to be installed. After the creation of these objects, OpenShift will create the CRDs required for the creation of local storage on specific machines. 

> [!NOTE] 
> OpenShift Data Foundation, using this mehtod of installation, exists as pods in the cluster. However, as the name implies, the storage and therefore the files within the local storage are stored locally to the node, even if it is a vm. This is similar to creating a file on a local phyiscal computer. The files only exist on that host and therefore cannot be transfered to another pod. This is different from other styles of Persistent Volumes. See the [official documentation](https://docs.openshift.com/container-platform/4.13/storage/persistent_storage/persistent_storage_local/persistent-storage-local.html) for a greater understanding of local storage options.



```
echo '
apiVersion: operators.coreos.com/v1
kind: OperatorGroup
metadata:
  name: local-operator-group
  namespace: openshift-local-storage
spec:
  targetNamespaces:
  - openshift-local-storage
---
apiVersion: operators.coreos.com/v1alpha1
kind: Subscription
metadata:
  name: local-storage-operator
  namespace: openshift-local-storage
spec:
  channel: stable
  installPlanApproval: Automatic
  name: local-storage-operator
  source: redhat-operators
  sourceNamespace: openshift-marketplace
' | oc apply -f -
```

## LocalVolumeDiscovery

This object can and should be modified if the label `storage: odf` is not being used in the cluster. The below definition uses a `nodeSelector` to ensure that the volume discovery will only apply to ODF nodes

```
echo '
apiVersion: local.storage.openshift.io/v1alpha1
kind: LocalVolumeDiscovery
metadata:
  name: auto-discover-devices
  namespace: openshift-local-storage
spec:
  nodeSelector:
    nodeSelectorTerms:
      - matchExpressions:
          - key: storage
            operator: In
            values:
              - odf
    tolerations:
      - effect: NoSchedule
        key: node.ocs.openshift.io/storage
        operator: Equal
        value: 'true'
| oc apply -f -
```

## LocalVolumeSet

This object defines for the LocalVolumeDiscovery the attributes of the local storage to use. The below definition says to look for partitions or disks that are considered "NonRotational" (i.e. SSDs and the like), with a minimum size of 1Gi. This file also uses a `nodeSelector` to ensure that it only applies to the `storage: odf` label.

```
echo '
apiVersion: local.storage.openshift.io/v1alpha1
kind: LocalVolumeSet
metadata:
  name: overlay
  namespace: openshift-local-storage
spec:
  deviceInclusionSpec:
    deviceMechanicalProperties:
      - NonRotational
    deviceTypes:
      - disk
      - part
    minSize: 1Gi
  nodeSelector:
    nodeSelectorTerms:
      - matchExpressions:
          - key: storage
            operator: In
            values:
              - odf
  storageClassName: overlay
  tolerations:
    - effect: NoSchedule
      key: node.ocs.openshift.io/storage
      operator: Equal
      value: 'true'
  volumeMode: Block
' | oc apply -f -

```

After a few minutes, several PVs should start appearing in the `openshift-local-storage` project. Once the PVs have been verified with the following commands it is safe to move on to the next step:

```
oc get all -n openshift-local-storage
oc get pv
```
