```
oc create secret generic init-config-bundle-secret --from-file=config.yaml=quay-config.yaml
```

## Create Quay `Subscription`

For Quay, only a generic `Subscription` object is required to install the operator. However, it should be noted that installing the Quay Operator only creates CRDs in the cluster so there are additional steps required before a registry is available.

Below is the `Subscription` for Quay v3.9.2. This file is mostly static save for installing different versions of Quay.

```
echo '
apiVersion: v1
items:
- apiVersion: operators.coreos.com/v1alpha1
  kind: Subscription
  metadata:
    labels:
      operators.coreos.com/quay-operator.openshift-operators: ""
    name: quay-operator
    namespace: openshift-operators
  spec:
    channel: stable-3.9
    installPlanApproval: Automatic
    name: quay-operator
    source: redhat-operators
    sourceNamespace: openshift-marketplace
    startingCSV: quay-operator.v3.9.2
kind: List
metadata:
  resourceVersion: ""
' | oc apply -f -
```

This process will create several CRDs in the cluster as well as creating an operator pod called `quay-operator.v<version>`. This pod is in charge of reconciling various UI and CLI interactions with Quay.

> [!IMPORTANT]
> Red Hat Quay running on top of OpenShift relies heavily on its' Postgres database. While standalone Quay has a lot of options with regards to editing flat files, Quay on OpenShift stores the majority of its information in the database. If changes you make are not being reflected in the pod, its likely there is a problem with the operator.

## Create `QuayRegistry`

The next step required for installing Quay is the `QuayRegistry` object. It consists of a definition of which components should be installed and managed by the Quay Operator. In addition, this object also references the `init-config-bundle-secret` that was created earlier. Generally speaking, the `QuayRegistry` object should be created in whatever namespace/project has been dedicated to holding Quay.  Below is a `QuayRegistry` with all of the components installed and managed by the operator:

```
echo '
apiVersion: quay.redhat.com/v1
kind: QuayRegistry
metadata:
  name: central
  namespace: quay
spec:
  configBundleSecret: init-config-bundle-secret
  components:
    - managed: true
      kind: clair
    - managed: true
      kind: postgres
    - managed: true
      kind: objectstorage
    - managed: true
      kind: redis
    - managed: true
      kind: horizontalpodautoscaler
    - managed: true
      kind: route
    - managed: true
      kind: mirror
    - managed: true
      kind: monitoring
    - managed: true
      kind: tls
    - managed: true
      kind: quay
    - managed: true
      kind: clairpostgres
' | oc apply -f -
```

> [!NOTE]
> Any component that is not explicitly listed will be assumed to have a `managed: true` declaration

A more minimalist `QuayRegistry` can be achieved with the following:

```
echo '
apiVersion: quay.redhat.com/v1
kind: QuayRegistry
metadata:
  name: central
  namespace: quay
spec:
  configBundleSecret: init-config-bundle-secret
  components:
    - kind: clair
      managed: false
    - kind: clairpostgres
      managed: false
    - kind: horizontalpodautoscaler
      managed: false
    - kind: mirror
      managed: false
    - kind: quay
      managed: true
        replicas: 1
' | oc apply -f -
```

Obviously, the above is meant for testing only. Setting the `quay` pod to a single replica is **_NOT_** a recommended production configuration.

> [!IMPORTANT]
> debug logs for Quay components are turned on by adjusting the `QuayRegistry` object. For example if debugging is needed for the quay pod from the above definition, it would look like this:
> ```
>    - kind: quay
>      managed: true
>      overrides:
>        env:
>        - name: DEBUGLOG
>          value: "True"
>        replicas: 1
>```

