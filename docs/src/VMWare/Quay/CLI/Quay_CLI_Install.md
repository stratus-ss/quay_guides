To create the namespace use the following example:

```
echo '
apiVersion: v1
kind: Namespace
metadata:
  name: quay
' | oc create -f -
```