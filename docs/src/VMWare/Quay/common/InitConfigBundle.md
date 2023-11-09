Regardless how which storage option is deployed to enable Quay, the most important thing from an automation perspective is setting up the `init-config-bundle-secret`. This secret (whose name is only `init-config-bundle-secret` by convention) hold the information required to bootstrap Quay. _Most_ of Quay's options can be adjusted post-install except for the storage. If OpenShift Data Foundation is not being used to provide the storage, the `init-config-bundle-secret` **needs** to contain the information required for the Quay Operator to create the resources it needs.

## `init-config-bundle-secret` With OpenShift Data Foundation (ODF)

When using ODF, there is no additional information required in the secret. By default (unless altered by the installer) Quay will opt to manage its' own storage requirements and Quay will look for the CRDs provided by ODF. These can be either Noobaa or the Multicloud Object Gateway. Assuming these are already in place, adjust the below configuration adding in the LDAP config, SERVER_HOSTNAME and SUPER_USERS.

> [!NOTE]
> A Quay SUPER USER is just as it sounds. These are the admin users for Quay and at least one is required. If a default, non-SSO user is desired, there are 2 options.
> 1. Set the `FEATURE_USER_CREATION:` to `true`. This allows users to register themselves with Quay. They cannot obtain elevated privileges in this manner. A `SUPER_USERS` definition is still required in the `init-config-bundle-secret`
> 2. Set the `FEATURE_USER_INITIALIZE:` to `true`. This allows an operator to create the initial Quay user via the API by hitting the `/api/v1/user/initialize` end point.

The below config uses the `FEATURE_USER_CREATION: true` to accommodate new user creation. 


```
EXTERNAL_TLS_TERMINATION: true
FEATURE_ANONYMOUS_ACCESS: true
FEATURE_CHANGE_TAG_EXPIRATION: true
FEATURE_DIRECT_LOGIN: true
FEATURE_EXTENDED_REPOSITORY_NAMES: true
FEATURE_INVITE_ONLY_USER_CREATION: false
FEATURE_MAILING: false
FEATURE_NONSUPERUSER_TEAM_SYNCING_SETUP: false
FEATURE_PARTIAL_USER_AUTOCOMPLETE: true
FEATURE_PROXY_CACHE: true
FEATURE_PROXY_STORAGE: true
FEATURE_SECURITY_NOTIFICATIONS: true
FEATURE_TEAM_SYNCING: true
FEATURE_USER_CREATION: true
FEATURE_USER_LAST_ACCESSED: true
FEATURE_USERNAME_CONFIRMATION: true
FRESH_LOGIN_TIMEOUT: 10m
LDAP_ADMIN_DN: <user>
LDAP_ADMIN_PASSWD: <password>
LDAP_ALLOW_INSECURE_FALLBACK: true
LDAP_BASE_DN:
- OU=Group1
- DC=example
- DC=com
LDAP_EMAIL_ATTR: mail
LDAP_UID_ATTR: uid
LDAP_URI: ldap://ldap-host.example.com:389
LDAP_USER_RDN:
- OU=Uusers
- OU=Group1
- DC=example
- DC=com
PREFERRED_URL_SCHEME: https
REGISTRY_TITLE: Red Hat Quay
REGISTRY_TITLE_SHORT: Red Hat Quay
SEARCH_MAX_RESULT_PAGE_COUNT: 10
SEARCH_RESULTS_PER_PAGE: 10
SERVER_HOSTNAME: central-quay.apps.ocp.example.com
SETUP_COMPLETE: true
SUPER_USERS:
- user1
- user2
```

## `init-config-bundle-secret` External Object Store 

The `init-config-bundle-secret` stays almost identical in this example except for the addition of the storage options.

> [!WARNING]
> If `DISTRIBUTED_STORAGE_DEFAULT_LOCATIONS` and `DISTRIBUTED_STORAGE_PREFERENCE` are not set, Quay will not initialize. The [config.py](https://github.com/quay/quay/blob/master/config.py#L428-L429) within Quay's code base sets these values to `local_us` unless declared. This will cause confusing and misleading errors during Quay's initialization.

```
DISTRIBUTED_STORAGE_CONFIG:
    default:
        - RadosGWStorage
        - access_key: <key>
          bucket_name: <bucket>
          hostname: <host>
          is_secure: false
          port: <port>
          secret_key: <bucket secret key>
          storage_path: <bucket path>
DISTRIBUTED_STORAGE_DEFAULT_LOCATIONS:
    - default
DISTRIBUTED_STORAGE_PREFERENCE:
    - default
```

See the [official documentation](https://docs.projectquay.io/config_quay.html#config-fields-storage) for more example configurations for various storage backends.
