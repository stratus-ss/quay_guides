ProxyCache can be used to both restrict access to external repositories to a single client (the Quay registry itself) as well as provide a caching mechanism so that popular images do not have to be repeatedly downloaded from outside sources.

Assuming that the feature flag `FEATURE_PROXY_CACHE` has been set to `true` in the `init-config-bundle-secret`, the ProxyCache will show up as an option when examining the `Organization Settings` in the Quay UI. Select the 3 gear icon from the left hand panel.

![quayregistry1.png](../../images/quayregistry1.png)

The options are self explanatory. In order to test that the configuration is valid try doing pull with podman:

```
podman login <quay url>
podman pull --tls-verify=false <quay url>/<organizaltion>/<external repository>/<image>:<tag>
```

For example assuming the ProxyCache config is for `quay.io`:

```
podman pull --tls-verify=false <quay url>/example-org/projectquay/quay:3.7.9
```

This should pull the image `quay:3.7.9` from the repo `quay.io/projecctquay` and cache it in the local Quay instance.

## Quotas/Auto Pruning

1. To enable quota management, set the feature flag in your config.yaml to true. You can do this from the OpenShift console UI, by editing the config bundle secret to include the following line and click Save.

```
FEATURE_QUOTA_MANAGEMENT: true
```


2. Ensure that you are logged in as the Super User in Quay then under the Organization, click on the gear and select "Configure Quota"
![quay_quotas.png](../../images/quay_quotas0.png)

3. Set the storage quota as per your requirements and click "Apply".

![quay_quotas2.png](../../images/quay_quotas2.png)

4. Optionally create rejection and warning limits. From the superuser panel, navigate to the Manage Organizations tab. Click the Options icon for the organization and select Configure Quota. In the Quota Policy section, with the Action type set to Reject, set the Quota Threshold 

![quay_quotas3.png](../../images/quay_quotas3.png)

Once the quota is exceeded, previous tags are removed and the most recent are preserved.
