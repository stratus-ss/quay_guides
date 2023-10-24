Quay has the ability to mirror specific repositories. By default the `QuayRegistry` object has the `managed: true` option set. However, if you are adding capability to a minimal Quay instance, the `QuayRegistry` needs to have the following section added in addition to what may already be in the object:

```
spec:
  components:
    - kind: mirror
      managed: true
    ...
```

In addition, the `init-config-bundle-secret` should have a line that reads `FEATURE_REPO_MIRROR: true` in order for the mirroring options to be displayed in the Quay UI.

Unfortunately, the rest of the mirror configuration has to be done via the webUI and there is no bulk import of repositories that may wish to be mirrored. A [program](../../apps/quay_sync/README.md) was created to address these shortcomings.