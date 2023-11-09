After the Quay Operator is confirmed ready, the CRDs are present in the cluster. The next step is to create a `QuayRegistry` Object. Click `Operators --> Installed Operators --> QuayRegistry` tab. 

Select `Current namespace only`. While it is possible to install the QuayRegistry object throughout the cluster this is not the recommended practice unless you plan on letting users have their own instance of Quay or you are in a multitenancy environment where you are host discrete instances of Quay to various clients.

Click `Create QuayRegistry`:

![quayregistry0.png](../../images/quayregistry0.png)

The form view is the default presentation of options in the OpenShift Console. If you have a prepared YAML definition you can toggle the view to `YAML view`. Otherwise enter a name. By convention Red Hat uses the name `central` for Quay instances. 

> [!IMPORTANT]
> Make sure that the `init-config-bundle-secret` which was created earlier, is selected. Otherwise Quay will have a minimal default configuration for the initial bootstrapping. Depending on storage and other required options, this could cause the installation to fail.

![quayregistry1.png](../../images/quayregistry1.png)

As seen above there is an `Advanced configuration` drop down which can expose the components Quay manages.

Below is an example of modifying the Quay pods themselves to turn on a `DEBUGLOG` as well as reduce the replicas to a single pod.

![quayregistry2.png](../../images/quayregistry2.png)