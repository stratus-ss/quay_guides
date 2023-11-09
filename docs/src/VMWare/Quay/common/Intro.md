Quay is a versatile registry that can be combine with tooling like Claire in order to provide a container registry with image scanning. This can then be used with other products such as Advanced Cluster Security in order to make deployment decisions and increase the security posture for the entire cluster but blocking or alerting on problematic container images with known active CVEs. 

Quay can be used to provide a caching layer to external registries without having to reconfigure client access allowing an organization to have only a single approved egress point for fetching containers outside of the premises.

This guide assumes that Quay will reside in a `quay` namespace and that the `QuayRegistry` object will be named `central`. This is convention only and completely arbitrary. 