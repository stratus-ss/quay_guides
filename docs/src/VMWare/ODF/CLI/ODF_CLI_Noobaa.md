
If you do not have need for block or file storage provided by ODF you can opt to install only the Noobaa component. This consists of Noobaa itself as well as a BackingStore. The below definitions can have their resources adjusted based on how busy the environment is

```
echo '
apiVersion: noobaa.io/v1alpha1
kind: NooBaa
metadata:
  name: noobaa
  namespace: openshift-storage
spec:
 dbResources:
   requests:
     cpu: '2'
     memory: 8Gi
 dbType: postgres
 coreResources:
   requests:
     cpu: '2'
     memory: 8Gi
---
apiVersion: noobaa.io/v1alpha1
kind: BackingStore
metadata:
  finalizers:
  - noobaa.io/finalizer
  labels:
    app: noobaa
  name: noobaa-pv-backing-store
  namespace: openshift-storage
spec:
  pvPool:
    numVolumes: 1
    resources:
      requests:
        storage: 100Gi
  type: pv-pool
' | oc create -f -
```

After this a Noobaa backend should eventually become available. The Quay Operator will detect this automatically if the option to manage storage is turned on in Quay (which is its' default).