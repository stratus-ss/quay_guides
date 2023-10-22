
To proceed with the full installation of ODF, enabling all of its' storage serving options, a Storage Cluster will need to be created after the ODF Operator has completed its' installation.

```
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
              storage: '1'
          storageClassName: overlay
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
```

