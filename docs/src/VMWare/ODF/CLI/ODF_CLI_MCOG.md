
To proceed with the full installation of ODF, enabling all of its' storage serving options, a Storage Cluster will need to be created after the ODF Operator has completed its' installation.

> [!WARNING]
> The `storageClassName` below is important. If using the VMWare CSI driver, the storage class is `thin-csi`. However, if using the local storage operator as documented in this guide, the value should be changed to `overlay`.


```
echo "
---
apiVersion: ocs.openshift.io/v1
kind: StorageCluster
metadata:
  annotations:
    cluster.ocs.openshift.io/local-devices: 'true'
    uninstall.ocs.openshift.io/cleanup-policy: delete
    uninstall.ocs.openshift.io/mode: graceful
  name: ocs-storagecluster
  namespace: openshift-storage
spec:
  storageDeviceSets:
    - config: {}
      count: 3
      dataPVCTemplate:
        metadata: {}
        spec:
          accessModes:
            - ReadWriteOnce
          resources:
            requests:
              storage: '100Gi'
          storageClassName: thin-csi
          volumeMode: Block
        status: {}
      name: overlay
      placement: {}
      preparePlacement: {}
      replica: 1
      resources: {}
  encryption:
    kms: {}
  mirroring: {}
  monDataDirHostPath: /var/lib/rook
  managedResources:
    cephObjectStoreUsers: {}
    cephCluster: {}
    cephBlockPools: {}
    cephNonResilientPools: {}
    cephObjectStores: {}
    cephFilesystems: {}
    cephRBDMirror: {}
    cephToolbox: {}
    cephDashboard: {}
    cephConfig: {}
  arbiter: {}
  network:
    connections:
      encryption: {}
    multiClusterService: {}
  nodeTopologies: {}
  externalStorage: {}
  flexibleScaling: true
" | oc apply -f -
```

The above storage cluster definition will create a StorageSystem. It may take a few minutes before the status in the UI changes from a yellow banner warning to normal display.

Next, create the file system storage class with the following definition:

```
echo '
kind: StorageClass
apiVersion: storage.k8s.io/v1
metadata:
  name: ocs-storagecluster-cephfs
  annotations:
    description: Provides RWO and RWX Filesystem volumes
    storageclass.kubernetes.io/is-default-class: 'true'
provisioner: openshift-storage.cephfs.csi.ceph.com
parameters:
  clusterID: openshift-storage
  csi.storage.k8s.io/controller-expand-secret-name: rook-csi-cephfs-provisioner
  csi.storage.k8s.io/controller-expand-secret-namespace: openshift-storage
  csi.storage.k8s.io/node-stage-secret-name: rook-csi-cephfs-node
  csi.storage.k8s.io/node-stage-secret-namespace: openshift-storage
  csi.storage.k8s.io/provisioner-secret-name: rook-csi-cephfs-provisioner
  csi.storage.k8s.io/provisioner-secret-namespace: openshift-storage
  fsName: ocs-storagecluster-cephfilesystem
reclaimPolicy: Delete
allowVolumeExpansion: true
volumeBindingMode: Immediate
' | oc apply -f -
```

Finally, update the `rook-ceph-operator-config` to specify tolerations that it should respect:

```
echo '
kind: ConfigMap
apiVersion: v1
metadata:
  name: rook-ceph-operator-config
  namespace: openshift-storage
data:
  CSI_PLUGIN_TOLERATIONS: |
    - effect: NoSchedule
      key: node-role.kubernetes.io/infra
      operator: Exists
    - key: node.ocs.openshift.io/storage
      operator: Equal
      value: "true"
      effect: NoSchedule
'
```
At this point the ODF cluster should be ready to serve storage to the cluster.

> [!IMPORTANT]
> When installing ODF via the command line, the plugin for the OpenShift Console does not get installed. To enable the plugin run the following patch command
> ```
> oc patch console.operator cluster -n openshift-storage --type json -p '[{"op": "add", "path": "/spec/plugins", "value": ["odf-console"]}]'
>```