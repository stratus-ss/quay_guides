# Introduction

This directory contains various tools for interacting with Quay Enterprise on OpenShift. Written in python, the programs here use the Quay API as well as `oc` command line tools to accomplish tasks

Almost all the options that have 'values' are referenced from the application configuration file. While you may not need to have every option for your specific use case, they need to be defined or else the parser will refuse to run the program. If there is an undefined variable or section the program will dump expected headings, types and a description of each heading to the CLI. Everything in the configuration file is in `yaml`.

> [!IMPORTANT]
> For ease of maintenance and code cleanliness, dictionaries in the output of the help are outputted in JSON/Python style dicts. You will have to translate this into a `yaml` dict in order for the parser (which uses Python's stdlib `yaml`) to be able to handle the config file properly.

## Quay Management Tasks

This program is used to do things like create OpenShift objects, add robot and proxycache configurations and other management tasks to Quay. It makes use of the classes found in the `modules/` directory. 

### Expectations

#### Using Quay Management for Installation On OpenShift

##### Files and Folders
This functionality is a slightly more intelligent version of `kustomize`. `kustomize` takes the resources as input, renders them and then provides the output to `stdout`. [Questions](https://github.com/kubernetes-sigs/kustomize/issues/4371#issuecomment-1010408437) around whether or not `kustomize` can be used to wait until a resource is created have been answered by the project as "out of scope". As such this functionality adds in some intelligent waits where it can, before applying yaml files.

In order to know which order to apply files **YOU MUST** prefix the files with something that is easily sortable. The recommendation is to use numbers such as:

```
0001-ODF_machineset.yaml  0004-odf_storagecluster.yaml  001-quay_namespace.yaml
0002-odf_namespace.yaml   0005_ceph_storageclass.yaml   002-quay_og.yaml
0003-odf_og.yaml          0006_rook_cm.yaml             002-quay_sub.yaml
0003-odf_sub.yaml         0007-odf_console_patch.yaml   003-quay_registry.yaml
```

If the same prefix is used, such as `0003-odf_og.yaml`, the prgram falls back to alphabetization.

It is expected that all files are in the same directory and no other files are in that directory. Currently, the expectation is that these are valid `yaml` files for OpenShift. The program eventually reads the `kind:` in each `yaml` file to determine the appropriate resources to watch while waiting. The program **WILL** error out if the file is not valid `yaml`.

##### Cluster Login

As this is meant to install Operators and other objects, a user with cluster admin is expected. Currently, the login expects a username and password, but this may be changed in the future to also support `kubeconfig` files.

## Quay Sync

The purpose of this program is to provide functionality for automation of day 2 activities that may otherwise be cumbersome to do with Quay out of the box. 

**Current Features**

1. Checks both the source and destination Quay instances to ensure that DNS can resolve and that they are listening on the expected port (443)
2. Uses `podman` to login to both instances. The program currently assumes the credentials are the same on both sides as they are supposed to be mirrors of each other. 
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

4. Operations happen by shelling out to `podman`. While `skopeo` could be used, caching the images on the host running this script might be advantageous if there is mirroring happening between more than 2 hosts (for example a mirror and a backup mirror). The flow is a `podman pull`, `podman tag`, `podman push`.

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

### BaseOperations
BaseOperations.py is a Python class file that contains the implementation of the BaseOperations class. This class is designed to handle various operations related to configuration and data manipulation.

The class has the following methods:

1. `load_config(cls, config_file: str) -> dict[str,str]`: This static method loads the configuration data from the specified file and returns it as a dictionary.

2. `yaml_file_list(file_directory)`: This static method returns a list of YAML files present in the specified directory.

3. `do_i_skip_tls(cls, command: list[str], skip_tls_verify: bool = False ) -> list[str]`: This class method adds the `--tls-verify=false` flag to the specified command if the `skip_tls_verify` parameter is set to True. It returns the updated command.

The class also has an `__init__` method that initializes the class object. It takes a `config_file` parameter and loads the configuration data from the file using the `load_config` method. It also sets various attributes based on the loaded configuration data.

### PreflightChecker:

This class is used to check the prerequisites for running the ImageMover class. It has two methods:

    check_dns(): This method checks if the specified server can be resolved by DNS. It returns True if the server can be resolved, False otherwise.
    check_port(): This method checks if the specified server is listening on the specified port. It returns True if the server is listening on the specified port, False otherwise.

### QuayAPI:

This class provides an interface to the Quay API. It can be used to check if an object (repository or organization) exists in Quay, create a new organization, get data from the Quay API, and get information about tags in a Quay repository.

To use this class, you would first need to create an instance of it and pass in the base URL of the Quay API and the API token for authentication. Once you have created an instance of the class, you can call the following methods:

    assemble_proxyurl(): Assembles the proxycache URL, basic find/replace function
    check_if_object_exists() This method checks if an object (repository or organization) exists in Quay. It returns True if the object exists, False otherwise.
    create_proxycache(): Uses the QuayAPI to create a proxycache setting under a specific organization
    create_robot_acct(): Creates a robot account in quay
    create_org(): This method creates a new organization on Quay. It returns True if the organization was created successfully, False otherwise.
    create_initial_user(): Uses the Quay initialize endpoint to create the first user in Quay. Returns the response object from the API
    delete_robot_acct(): Deletes a robot account if it exists
    delete_data(): Deletes data from a specified URL using the requests library. Returns the response object from the API
    delete_proxycache(): Deletes the proxycache configuration from the specified Quay organization
    get_data(): This method fetches data from the Quay API. It returns a dictionary containing the JSON response from the API.
    get_tag_info(): This method gets information about tags in a Quay repository. It returns a list of dictionaries, each representing a tag in the repository.
    get_proxycache(): Retrieves proxycache information from the API. Returns the JSON response from the API
    get_robot_acct(): Retrieves the robot account from the url specified. Returns the JSON response from the API
    post_data(): Posts data to a specified URL using the requests library. Returns the JSON response from the API
    put_data(): Uses the PUT method instead of the POST method to interact with the API. Returns the response object from the API

This class can be used to automate tasks such as creating new organizations, checking if objects exist, and getting information about tags. It can also be used to develop tools that interact with the Quay API.

### QuayOperations/ImageMover:

This class is used to move images between Quay servers. It has the following methods:

    load_config(): This method loads the configuration from the specified file. It returns a dictionary containing the configuration data.
    login_to_quay(): This method logs in to Quay on the specified server.
    podman_operations(): This method performs a Podman operation on an image.

### QuayOperations/QuayManagement

This is a general class that is used for managing Quay outside of API calls. This calls may call methods from QuayAPI in order to fulfill its' requirements. This is a catchall class for actions that don't make sense to have their own class.

    add_proxycache(): This method processes the configuration related to the proxycache before calling the QuayAPI class to actually create the object.
    add_robot_acct(): This method processes configuration for robot accounts before calling the QuayAPI class to create the object
    delete_robot(): This method processes the configuration and will remove all robot accounts found within by calling the QuayAPI class
    get_robot(): Gets the information about all robot accounts in the configuration. Returns a dict with the robot name and a bool of True if the account exists or False if not
    parse_robot_acct_info(): Parse robot account information for a given key in the quay_config dictionary. Returns an instance of the QuayAPI class specific to that robot account

### OpenshiftOperations

This class deals with running OpenShift commands. However, it DOES NOT use the OpenShift API python library. Instead it uses `subprocess` to call the `oc` command. This was done for both brevity and ease of reading. In the future this may change.

    does_secret_exist(): Checks to see if a secret exists in the cluster. Returns a True if the object exists
    openshift_apply_file(): Uses the `oc apply` command to create or modify OpenShift objects
    openshift_create_secret(): Creates a secret from a file. The initial intent is to create the `init-config-bundle-secret`
    openshift_get_infrastructure_name(): Returns the current infrastructure ID of an OpenShift Cluster
    openshift_get_object(): Handles getting objects from OpenShift and returning the results
    openshift_generic_wait(): Handles the sleep timer, number of iterations and messages related to the wait loop
    openshift_login(): Logs into the OpenShift cluster with username and password. In the future tokens or kubeconfig support may be added
    openshift_object_ready(): Takes a dictionary and loops over it to see if all the key/value pairs are "True", if they are return True, otherwise return False
    openshift_ready_check(): Parses the output from `oc get` commands. Builds a dict of objects with the object name as the key and the value of True/False depending on whether they have a 'Ready' state
    openshift_waitfor_pods(): This function is different from the others because it is not checking the status of a single object but rather multiple objects. In addition, pods need to use ['status']['phase'] because there will be completed pods that have a 'Ready': False, because they have completed.
    openshift_waitfor_storage(): Wait for PV or PVCs to become bound. Unfortunately their status is in a different section compared to most objects requiring its own method
    openshift_waitfor_object(): Similar to waitfor_storage() except that it can be more broadly applied many objects in OpenShift
