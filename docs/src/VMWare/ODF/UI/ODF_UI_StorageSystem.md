> [!IMPORTANT]
> The OCP console UI needs to be refreshed before continuing or else the `Data Foundation` menu entry will not appear!

The next step is to create a Storage System for ODF to present to the cluster.

> [!WARNING]
> At the current time it is not recommended to follow the prompts of the ODF Operator post-install.

To create a Storage System click on **Storage --> Data Foundation --> Storage System**. Initially there should be a green check mark :white_check_mark: best the `Data Foundation` in the Status section of the overview:

![odf_ui_storagesystem.png](../../images/odf_ui_storagesystem.png)

Click on `Create StorageSystem`:

![odf_ui_storagesystem2.png](../../images/odf_ui_storagesystem2.png)

There are several storage backing options presented. In this guide, the Local Storage Operator is presented as an option but using the VMWare CSI driver (indicated via the Storage Class `thin-csi`) is the easiest option:

![odf_ui_storagesystem3.png](../../images/odf_ui_storagesystem3.png)

On the next screen, select the storage options that make sense for your environment in terms of capacity. If the machineset was created properly, the nodes in the ODF machineset will automatically be selected. If not, the appropriate nodes can be manually selected. Once confirmed the selected nodes will have the `cluster.ocs.openshift.io/openshift-storage` label applied to them for the deployment. 

Optionally, taint the nodes to ensure they are dedicated to ODF. Click next when ready.

![odf_ui_storagesystem4.png](../../images/odf_ui_storagesystem4.png)

The next screen will provide encryption options as well as networking options, though at the time of writing only the `Default (SDN)` is supported.

![odf_ui_storagesystem5.png](../../images/odf_ui_storagesystem5.png)

Finally confirm the previous selections by clicking `Create StorageSystem`
![odf_ui_storagesystem6.png](../../images/odf_ui_storagesystem6.png)