The below steps provide a solid example of how to setup ODF for supporting Quay. This guide assumes that ODF should be deployed to nodes that have `storage: odf` as the label.

## Create The Namespaces

After the machines are configured appropriately, create the OpenShift namespaces required to handle ODF.

```
echo '
apiVersion: v1
kind: Namespace
metadata:
  labels:
    openshift.io/cluster-monitoring: "true"
  name: openshift-storage
' | oc create -f -
```


> [!NOTE] 
> You do not **_need_** the Local Storage Operator when using an IPI installation. However, it is a valid deployment pattern.
> If using the Local Storage Operator, its' namespace will need to be created as well.
> ```
> echo '
> ---
> apiVersion: v1
> kind: Namespace
> metadata:
>   name: openshift-local-storage
> ' | oc create -f -
> ```

