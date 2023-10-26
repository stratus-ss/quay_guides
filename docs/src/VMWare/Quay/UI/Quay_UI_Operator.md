In order to install the Quay Operator, access to the OperatorHub is required. This can be done offline via mirroring the `oc-mirror` process which is documented [here](https://docs.openshift.com/container-platform/4.13/installing/disconnected_install/installing-mirroring-disconnected.html#oc-mirror-support_installing-mirroring-disconnected). However, the offline installation of the Operator Catalog is outside of the scope of this document.

Assuming that there is no problem accessing the Operator Catalog, to install the Quay Operator click on **Operators --> OperatorHub**. From there, search for Quay and select the Operator labeled `Red Hat Quay` as seen below:

![quay_operator1.png](../../images/quay_operator1.png)

The first screen is simply informational, and the `Install` can be clicked after the text has been reviewed.
![quay_operator1.png](../../images/quay_operator2.png)

Finally, select the update channel based on which version of Quay is desired. The default of `All namespaces on the cluster` is likely the appropriate choice. During this phase of the installation process, Custom Resource Definitions (CRDs) are being created but no actual Quay (or Quay component) pods are being created. Lastly, chose the `Update approval` that is appropriate for the enviornment which Quay is being installed.

![quay_operator1.png](../../images/quay_operator3.png)

This process will create several CRDs in the cluster as well as creating an operator pod called `quay-operator.v<version>`. This pod is in charge of reconciling various UI and CLI interactions with Quay.

> [!IMPORTANT]
> Red Hat Quay running on top of OpenShift relies heavily on its' Postgres database. While standalone Quay has a lot of options with regards to editing flat files, Quay on OpenShift stores the majority of its information in the database. If changes you make are not being reflected in the pod, its likely there is a problem with the operator.