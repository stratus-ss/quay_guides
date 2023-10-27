# Installing Local Storage Operator
To install the Local Storage Operator via the UI, click on **Operators --> OperatorHub** then filter for `local storage` and click on the `Local Storage provided by Red Hat` from the options below:

![odf_ui_localstorage.png](../../images/odf_ui_localstorage.png)

The next screen is basic information about the operator. Once the information has been reviewed, click `Install`

![odf_ui_localstorage2.png](../../images/odf_ui_localstorage2.png)

On the next screen, the default options are sufficient.
> [!NOTE]
> As in the screenshot below, if the `openshift-local-storage` namespace does not exist, it will be created during this process

![odf_ui_localstorage3.png](../../images/odf_ui_localstorage3.png)


# Installing Local Storage Discovery

While there is an option to specify which drives in a system will be used for the Local Storage Operator, it is often preferable to use the `Local Storage Discovery`. This will allow OpenShift to scan the hosts and automatically determine which disks to add for local storage.

![odf_ui_localdiscovery.png](../../images/odf_ui_localdiscovery.png)

It is possible to use the form view to populate the appropriate options for the `LocalVolumeDiscovery`, however for this guide, the definition is fairly short and is simpler to insert the appropriate YAML definition.

![odf_ui_localdiscovery2.png](../../images/odf_ui_localdiscovery2.png)

After creating the LocalVolumeDiscovery, you can click on the `auto-discover-devices` link.

![odf_ui_localdiscovery3.png](../../images/odf_ui_localdiscovery3.png)

Viewing the events shows that the hosts are identified and the disks are found after a short period of time.

![odf_ui_localdiscovery4.png](../../images/odf_ui_localdiscovery4.png)
