The above can be done in an scriptable fashion. The operator requires an Operator Group and a Subscription. Post-install configurations, with regards to Quay are documented in either the section for Noobaa or the Multicloud Object Gateway below.

You can use these definitions to install the operator

```
echo '
apiVersion: operators.coreos.com/v1
kind: OperatorGroup
metadata:
  name: openshift-storage-operatorgroup
  namespace: openshift-storage
spec:
  targetNamespaces:
  - openshift-storage
---
apiVersion: operators.coreos.com/v1alpha1
kind: Subscription
metadata:
  name: odf-operator
  namespace: openshift-storage
spec:
  channel: stable-4.13
  installPlanApproval: Automatic
  name: odf-operator
  source: redhat-operators
  sourceNamespace: openshift-marketplace
' | oc apply -f -
```

At this point a decision needs to be made whether to use Noobaa by itself or whether to deploy the Multicloud Object Gateway.