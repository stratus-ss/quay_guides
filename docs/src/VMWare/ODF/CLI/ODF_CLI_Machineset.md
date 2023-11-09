After you have created the `odf_machineset.yaml`, simply apply it to the cluster:

```
oc apply -f odf_machineset.yaml -n openshift-machine-api
```

After several minutes you should see the following:

```
$ oc get machineset -n openshift-machine-api
NAME                      DESIRED   CURRENT   READY   AVAILABLE   AGE
odf-workers-0             3         3         3       3           21h
```