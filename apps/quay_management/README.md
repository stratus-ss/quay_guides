# Introduction

This directory contains various tools for interacting with Quay Enterprise on OpenShift. Written in python, the programs here use the Quay API as well as `oc` command line tools to accomplish tasks.

Almost all the options that have 'values' are referenced from the application configuration file. The parser should be able to determine if you have all of the options in the config file set based on the actions you are attempting to take on either Quay, the OpenShift cluster or both. If there is an undefined variable or section(s), the program will dump expected headings, types and a description of each heading to the CLI. Everything in the configuration file is in `yaml`.

> [!IMPORTANT]
> For ease of maintenance and code cleanliness, dictionaries in the output of the help are outputted in JSON/Python style dicts. You will have to translate this into a `yaml` dict in order for the parser (which uses Python's stdlib `yaml`) to be able to handle the config file properly. For example
> ```
>    organizations:
>                        type: dict
>                        description: A dictionary that tells the program which >organizations should or should not exist in quay in the format of {'<org_name>': 'present': 'true/false'}
> ```
> 
> Would look like this in YAML:
> ```
> organizations:
>    proxytest:
>        present: true
> ```

## Quay Management Tasks

Currently this program supports the following functionality:

* Install Quay on OpenShift via loading mostly preconfigured YAML files. (Some things like the machineconfig can be templated somewhat... See [machineconfig sampe](https://github.com/stratus-ss/quay_guides/blob/main/apps/quay_management/config/samples/odf_quay_manifests/0001-ODF_machineset.yaml))
* Initialize a Quay User. Assuming the options have been set in your `init-config-bundle-secret`, the first Quay user can be created
* Creates an initial OAUTH token and writes it to the passed in sample_config.yaml file
* Can create an admin organization where automation related objects (oauth tokens, robot accounts etc) can be attached
* Can add super users via the OpenShift secret as specified in the QuayRegistry object
* Can add robot accounts to the speficied organizations
* Can add Proxycaches to the specified organizations
* Can ensure that specified orgs either exist or are removed
* Can ensure that the specified `uay_username` takes ownership of all organizations. This is required for certain automations such as push/pull to repos in an org
* Can ensure that all users specified in the Quay OpenShift secret take ownership of all organizations
* You can specify if you are configuring a secondary server

The intent for each `sample_config.yaml` is that there should be no more than 2 servers that are acting as a primary and secondary. This allows for simplicity in the code.
This can be used in conjuction with `quay_sync.py` in order to keep the two servers in sync. Quay, at the time of writing, does not have an easy way to mirror, on bulk,
a list of repositories, so this functionality is added by the `quay_sync.py` program.

Aside from the path to the `sample_config.yaml` file, all arguments for this program are True/False. False is assumed. If an argument such as `--debug` is added, this is the same as `--debug=True`. The current list of arguments for this program are:

```
optional arguments:
  -h, --help            show this help message and exit
  --add-admin-org       Create the administrative organization
  --add-proxycache      Add ProxyCache to an organization
  --add-robot-account   Adds robot accounts to a personal account or an organization
  --add-super-user      Whether or not to add the super user for Quay
  --config-file CONFIG_FILE
                        The full path to the config file
  --configure-secondary-quay-server
                        If this flag is set, assume that you are installing a quay mirror. The quay sync program will activate assuming this server is the secondary.
  --debug               Should debug be turned on. Files will be written to disk and not cleaned up
  --initialize-user     Create the first user for Quay
  --initialize-oauth    Create the first OAUTH token for Quay
  --manage-orgs         Whether or not this program should create/remove orgs in the config.yaml
  --openshift-yaml-dir OPENSHIFT_YAML_DIR
                        The full path to the YAML files to apply to the cluster. They should be prefixed with the a number associated with the order to apply them.
  --overwrite-proxycache
                        Should any current proxycache be overridden?
  --setup-quay-openshift
                        Have the management script apply OpenShift Quay configs
  --skip-tls-verify     Ignore self signed certs on registries
  --take-ownership      Ensure that the quay user used in the automation has ownership over all orgs
  --take-ownership-all-super-users
                        Referencing the OpenShift secret, ensure all super users own all orgs
```

### Example usages:


#### Installs & Configures Quay From Scratch
Run the installation process, including setting up Quay on OpenShift. This will configure a brand new Quay based on the options set in the `sample_config.yaml`. It creates the initial user, creates an oauth token, adds the admin organization, creates new organizations, creates proxycaches on those organizations and finally adds robot accounts to those organizations 
```
./quay_management_tasks.py  --config-file=/home/ocp/git_projects/quay_guides/apps/quay_management/config/sample_config.yaml --skip-tls-verify --add-admin-org --initialize-user --initialize-oauth --setup-quay-openshift --add-robot-account --add-proxycache --overwrite-proxycache --manage-orgs --debug
```

#### Configure Secondary Quay Instance

The below example will create the admin org, add required organizations, and add a robot & proxy configs
```
./quay_management_tasks.py --config-file=/home/ocp/git_projects/quay_guides/apps/quay_management/config/sample_config.yaml --skip-tls-verify --add-admin-org --add-robot-account  --add-proxycache --overwrite-proxycache --manage-orgs --configure-secondary-quay-server --debug
```

#### Add Super Users To All Orgs

The below example interrogates the OpenShift cluster to figure out which users are currently in the `SUPER_USERS` section of the QuayRegistry secret. It then adds those users to whichever organizations exist in Quay (in this case on the secondary server). Finally it will also ensure the specified organizations have been created or removed based on the options in the configuration file.
```
./quay_management_tasks.py --config-file=/home/ocp/git_projects/quay_guides/apps/quay_management/config/sample_config.yaml --manage-orgs --configure-secondary-quay-server --take-ownership-all-super-users
```

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

If the same prefix is used, such as `0003-odf_og.yaml`, the program falls back to alphabetization.

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

The class also has an `__init__` method that initializes the class object. It takes a `config_file` parameter and loads the configuration data from the file using the `load_config` method. It also sets various attributes based on the loaded configuration data. It also handles how the config is parsed, and what options are required in the config based on which arguments the program is launched with.

    add_to_config(): Updates the config.yaml for the quay activities in this repo. Does NOT update the Quay config that dictates how Quay behaves
    create_db_info_script(): Creates a script that retrieves oauthapplication and oauthaccesstoken tables from the Quay database
    create_initial_oauth_script(): Creates a small script that makes some database inserts to manually create an oauth token. 
            This is a workaround because Quay does not allow you to programmatically create an oauth token without first having an oauth token.
    do_i_skip_tls(): Adds the `--tls-verify=false` flag to the specified podman command if `args.skip_tls_verify` is True. 
    load_config(): Loads the configuration from the specified file. Assumes a yaml file
    replace_infraID(): This is intended to adjust a machine config so that it can be templated. The Machineconfig should have <INFRAID> instead of an actual value.
                        Interrogates OpenShift to determine the correct InfraID and then replaces accordingly
    yaml_file_list(): Walks the file system of a given toplevel directory to find all files there. Appends a full path to each file

### PreflightChecker:

This class is used to check the prerequisites for running the ImageMover class. It has two methods:

    check_dns(): This method checks if the specified server can be resolved by DNS. It returns True if the server can be resolved, False otherwise.
    check_port(): This method checks if the specified server is listening on the specified port. It returns True if the server is listening on the specified port, False otherwise.

### QuayAPI:

This class provides an interface to the Quay API. It can be used to check if an object (repository or organization) exists in Quay, create a new organization, get data from the Quay API, and get information about tags in a Quay repository.

To use this class, you would first need to create an instance of it and pass in the base URL of the Quay API and the API token for authentication. Once you have created an instance of the class, you can call the following methods:

    assemble_org_url(): Assembles the URL, basic find/replace function, replaces <org> with the organization name
    check_if_object_exists() This method checks if an object (repository or organization) exists in Quay. It returns True if the object exists, False otherwise.
    create_initial_user(): Uses the Quay initialize endpoint to create the first user in Quay. Returns the response object from the API
    create_org_member(): Adds a user as a member of a specific team. Returns the response object from the API
    create_org(): This method creates a new organization on Quay. It returns True if the organization was created successfully, False otherwise.
    create_oauth_application(): Quay ties an oauth token to an application. Creates the base application in Quay
    create_proxycache(): Uses the QuayAPI to create a proxycache setting under a specific organization
    create_robot_acct(): Creates a robot account in quay
    delete_data(): Deletes data from a specified URL using the requests library. Returns the response object from the API
    delete_org(): Deletes an organization on Quay.
    delete_proxycache(): Deletes the proxycache configuration from the specified Quay organization
    delete_robot_acct(): Deletes a robot account if it exists
    get_data(): This method fetches data from the Quay API. It returns a dictionary containing the JSON response from the API.
    get_org_members(): Gets the current members of the specified organization. Returns the response object from the API
    get_org(): Gets a list of all the organizations in Quay. Returns the response object from the API
    get_proxycache(): Retrieves proxycache information from the API. Returns the JSON response from the API
    get_robot_acct(): Retrieves the robot account from the url specified. Returns the JSON response from the API
    get_tag_info(): This method gets information about tags in a Quay repository. It returns a list of dictionaries, each representing a tag in the repository.
    post_data(): Posts data to a specified URL using the requests library. Returns the JSON response from the API
    put_data(): Uses the PUT method instead of the POST method to interact with the API. Returns the response object from the API

This class can be used to automate tasks such as creating new organizations, checking if objects exist, and getting information about tags. It can also be used to develop tools that interact with the Quay API.

### QuayOperations/ImageMover:

This class is used to move images between Quay servers. It has the following methods:

    login_to_quay(): This method logs in to Quay on the specified server.
    podman_operations(): This method performs a Podman operation on an image.

### QuayOperations/QuayManagement

This is a general class that is used for managing Quay outside of API calls. This calls may call methods from QuayAPI in order to fulfill its' requirements. This is a catchall class for actions that don't make sense to have their own class.

    add_proxycache(): This method processes the configuration related to the proxycache before calling the QuayAPI class to actually create the object.
    add_robot_acct(): This method processes configuration for robot accounts before calling the QuayAPI class to create the object
    delete_robot(): This method processes the configuration and will remove all robot accounts found within by calling the QuayAPI class
    get_robot(): Gets the information about all robot accounts in the configuration. Returns a dict with the robot name and a bool of True if the account exists or False if not
    parse_robot_acct_info(): Parse robot account information for a given key in the quay_config dictionary. Returns an instance of the QuayAPI class specific to that robot account
    process_quay_secret(): This staticmethod takes in a secret file yaml assuming the data section has already been base64 encoded.
                    Decodes the config.yaml, modifies it and returns the result of the modified file. Simply a text dump of the secret so it can be modified
    take_org_ownership(): This staticmethod checks each of the organizations in quay. By default there is a "owners" team on each org. 
                        If the {quay_username} is not in the owners team, it is added.

### OpenshiftOperations

This class deals with running OpenShift commands. However, it DOES NOT use the OpenShift API python library. Instead it uses `subprocess` to call the `oc` command. This was done for both brevity and ease of reading. In the future this may change.

    does_secret_exist(): Checks to see if a secret exists in the cluster. Returns a True if the object exists
    openshift_apply_file(): Uses the `oc apply` command to create or modify OpenShift objects
    openshift_create_secret(): Creates a secret from a file. The initial intent is to create the `init-config-bundle-secret`
    openshift_exec_pod(): Execs into a pod to run a command
    openshift_generic_wait(): Handles the sleep timer, number of iterations and messages related to the wait loop
    openshift_get_infrastructure_name(): Returns the current infrastructure ID of an OpenShift Cluster
    openshift_get_object(): Handles getting objects from OpenShift and returning the results
    openshift_login(): Logs into the OpenShift cluster with username and password. In the future tokens or kubeconfig support may be added
    openshift_object_ready(): Takes a dictionary and loops over it to see if all the key/value pairs are "True", if they are return True, otherwise return False
    openshift_process_secret(): loops over the 'data' section of the secret to build a decoded dict. Returns decoded data section
    openshift_ready_check(): Parses the output from `oc get` commands. Builds a dict of objects with the object name as the key and the value of True/False depending on whether they have a 'Ready' state
    openshift_replace_quay_init_secret(): Assumes there is a fully formed secret file being passed in. Uses 'oc replace' in order to update a secret in OpenShift
    openshift_waitfor_pods(): This function is different from the others because it is not checking the status of a single object but rather multiple objects. In addition, pods need to use ['status']['phase'] because there will be completed pods that have a 'Ready': False, because they have completed.
    openshift_waitfor_storage(): Wait for PV or PVCs to become bound. Unfortunately their status is in a different section compared to most objects requiring its own method
    openshift_waitfor_object(): Similar to waitfor_storage() except that it can be more broadly applied many objects in OpenShift
