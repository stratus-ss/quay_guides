When working within a VMWare environment there are a couple of options provided that the cluster was installed via the IPI method. 

First, it is possible to let the VMWare CSI driver handle the management of the ODF storage backend for the operator. This means that no additional configuration is required.

Second, the operator could opt to use the Local Storage Operator and bring their own disks to the vms that are hosting ODF.

> [!WARNING]
> If the cluster was installed via UPI, as of the time of this writing the only option is to use the local storage operator.