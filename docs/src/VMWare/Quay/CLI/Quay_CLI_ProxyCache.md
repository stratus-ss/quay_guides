From a CLI perspective, there is very little that can be accomplished with the native tooling when it comes to setting up the ProxyCache. As with mirroring, a feature needs to be turned on in the `init-config-bundle-secret` in order to use this feature. Make sure that the following feature flag is set:

```
FEATURE_PROXY_CACHE: true
```

The only option for creating ProxyCache from the command line is using the API. The [python program](../../apps/quay_sync/README.md) in this repo can be used to address this.