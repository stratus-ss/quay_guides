## Secret Creation Via UI

To create a secret via the UI, click on **Workloads --> Secrets**.

> {!WARNING}
> Ensure that you select the correct project from the drop down or else you may accidentally delete the secret or have problems during installation and configuration of Quay.

Select `Create` and then choose `Key/value` secret:

![quay_secret.png](../../images/quay_secret.png)

Ensure that the name chosen for this secret is clearly understood and consistent throughout the configuration files. By convention, Red Hat uses `init-config-bundle-secret` as the name of this secret.

> [!WARNING]
> It is very important that the key be exactly `config.yaml`. This is the name of the file that will be mounted into the Quay pods. If the name is wrong Quay will assume it has no configuration and start with a minimal default.

For the value, enter the options you want to utilize in the Quay registry. See [the documentation](https://access.redhat.com/documentation/en-us/red_hat_quay/3.9/html-single/configure_red_hat_quay/index#config-fields-intro) for more options.

![quay_secret2.png](../../images/quay_secret2.png)



Before proceeding with the installation of the Quay Operator, a project is required. To create a new project, ensure that you are in the `Administrator` view on the left hand menu.

Then click **Home --> Projects --> Create Project** as seen below:

![quay_project_create.png](../../images/quay_project_create.png)

Fill in the project details. By convention Red Hat uses a project starting with the name `quay`. A `Display Name` and `Description` are not required but may be useful for managing large clusters where there are several different groups administering the system. Some organizations may also have certain key words required in the description to meet compliance standards.
![quay_project_create2.png](../../images/quay_project_create2.png)

Once satisfied, click `Create` to create the project.