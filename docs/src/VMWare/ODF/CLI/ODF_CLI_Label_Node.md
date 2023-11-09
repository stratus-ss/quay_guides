The CLI installation method in this guide assumes that nodes will use the label `storage: odf`. The `yaml` files found within all reference this label. Should you choose a different label the `yaml` files will need to be adjusted.

> [!NOTE]
> Red Hat recommends labeling the ODF nodes with the infrastructure label `node-role.kubernetes.io/infra=""`

Nodes can be labeled with the following:

```
oc label node $x node-role.kubernetes.io/infra=""
oc label node $x stroage=odf
```
