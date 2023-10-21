# Proxy Caching
Registries like Docker or Google Cloud Platform have rate limitations and throttling on the number of times users can pull from these registries.

Red Hat Quay can act as a proxy cache and has the following benefits:

* Bypass pull-rate limitations from upstream registries
* Accelerate pull performance, because images are pulled from the cache rather than upstream dependencies
* Cached images are only updated when the upstream image digest differs from the cached image, thereby reducing rate limitations and potential throttling

1. Enable proxy caching by setting the below flag in your config bundle secret

```
FEATURE_PROXY_CACHE: true
```

2. Scroll down and click Save. It will take a minute for the changes to take effect

3. Create a new organisation named proxytest

* Enter the Remote registry value: quay.io

* Enter the corresponding Remote registry username and password

* * Expiration is an optional field

* Click Save

![Proxy](../images/proxy_cache_quay.png)


Now pull an image

```
podman login <quay url>
podman pull --tls-verify=false <quay url>/proxytest/projectquay/quay:3.7.9
podman pull --tls-verify=false <quay url>/proxytest/projectquay/quay:3.6.2
```

These images are pulled from quay.io but is being cached in the proxytest organization of your quay registry

## Set Quotas

You may wish to set quotas so that the proxy cache does not overwhelm your storage (depending on the frequency of change in your environment). To enable quota management:

1. Set the feature flag in your config.yaml to true. You can do this from the OpenShift console UI, by editing the config bundle secret to include the following line and click Save.

```
FEATURE_QUOTA_MANAGEMENT: true
```
Create a new organization, click on the Create New Organization button. Enter a new name (testorg in this case) and click Create Organization

2. Ensure that you are logged in as the Super User in Quay then under Organizations, click on the gear and select "Configure Quota"
![quay_quotas.png](../images/quay_quotas.png)

3. Set the storage quota as per your requirements and click "Apply".

![quay_quota_size.png](../images/quay_quota_size.png)

### (Optional) Rejection/Warning Limits

From the superuser panel, navigate to the Manage Organizations tab. Click the Options icon for the organization and select Configure Quota. In the Quota Policy section, with the Action type set to Reject, set the Quota Threshold 

![quay_quota_reject.png](../images/quay_quota_reject.png)


# Auto prune feature
Pull the last image that will result in your repository exceeding the allotted quota, for example:

```
podman pull --tls-verify=false <quay url>/proxytest/projectquay/quay:3.8.1
```
Refresh the Tags page of your Red Hat Quay registry

The first image that you pushed, for example, quay:3.7.9 should have been auto-pruned

The Tags page should now show quay:3.6.2 and quay:3.8.1




