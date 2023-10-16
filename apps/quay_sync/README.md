# Quay Sync

## Description

The purpose of this program is to provide functionality for automation of day 2 activities that may otherwise be combersome to do with Quay out of the box. 

**Current Features**

1. Checks both the source and destination Quay instances to ensure that DNS can resolve and that they are listening on the expected port (443)
2. Uses `podman` to login to both instances. The program currently assumes the credentials are the same on both sides as they are supposed to be mirrors of each other
3. The program has 2 options:
    
    **Option 1**: Use a config file to enumerate the specific repositories to be mirrored. There is a `sample_config.yaml` in this repo with examples. However the basic structure is as follows:
    ```
    source_server: <hostname>
    source_token: <pregenerated token>
    destination_server: <dest hostname>
    destination_token: <pregenerated token>
    failover: false
    repositories:
    - <organization/user>/<repo name>:<tag>
    ```

    **Option 2**: Autodiscovery. This attempts to scan the source Quay instance and then create missing organizations and repositories on the destination server.

4. Operations happen by shelling out to `podman`. While `skopeo` could be used, caching the images on the host running this script might be adventagious if there is mirroring happening between more than 2 hosts (for example a mirror and a backup mirror). The flow is a `podman pull`, `podman tag`, `podman push`.

5. Optionally, you can choose to skip tls verification for these operations in the event you are using a self-signed cert.
6. Optionally, you can choose not to have the program bail out if there is a problem with an image or images. If this option is set, the program will continue to attempt to mirror all images that are found regardless of whether they succeed.

USAGE:

```
optional arguments:
  -h, --help            show this help message and exit
  --username USERNAME   Quay Username
  --password PASSWORD   Quay Password
  --config-file CONFIG_FILE
                        The full path to the config file
  --skip-tls-verify     Ignore self signed certs on registries
  --skip-broken-images  Don't stop because of broken image pull/push
  --auto-discovery      Attempt to auto discover any repositories present in organizations
```

EXAMPLES:

```
./quay_sync.py --username <quayadmin> --password <password> --config-file ./sample_config.yaml --skip-tls-verify --skip-broken-images
```

## Python Classes

### PreflightChecker:

This class is used to check the prerequisites for running the ImageMover class. It has two methods:

    check_dns(): This method checks if the specified server can be resolved by DNS. It returns True if the server can be resolved, False otherwise.
    check_port(): This method checks if the specified server is listening on the specified port. It returns True if the server is listening on the specified port, False otherwise.

### ImageMover:

This class is used to move images between Quay servers. It has the following methods:

    load_config(): This method loads the configuration from the specified file. It returns a dictionary containing the configuration data.
    login_to_quay(): This method logs in to Quay on the specified server.
    podman_operations(): This method performs a Podman operation on an image.
    do_i_skip_tls(): This method adds the --tls-verify=false flag to the specified command if args.skip_tls_verify is True.

### QuayAPI:

This class provides an interface to the Quay API. It can be used to check if an object (repository or organization) exists in Quay, create a new organization, get data from the Quay API, and get information about tags in a Quay repository.

To use this class, you would first need to create an instance of it and pass in the base URL of the Quay API and the API token for authentication. Once you have created an instance of the class, you can call the following methods:

    check_if_object_exists(): This method checks if an object (repository or organization) exists in Quay. It returns True if the object exists, False otherwise.
    create_org(): This method creates a new organization on Quay. It returns True if the organization was created successfully, False otherwise.
    get_data(): This method fetches data from the Quay API. It returns a dictionary containing the JSON response from the API.
    get_tag_info(): This method gets information about tags in a Quay repository. It returns a list of dictionaries, each representing a tag in the repository.

This class can be used to automate tasks such as creating new organizations, checking if objects exist, and getting information about tags. It can also be used to develop tools that interact with the Quay API.