#!/usr/bin/env python
import logging
import argparse
from modules.QuayAPI import QuayAPI
from modules.BaseOperations import BaseOperations
from modules.QuayOperations import QuayManagement
from modules.OpenShiftOperations import OpenShiftCommands
import time
import math
import datetime
import ast
import yaml
import base64

parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument("--add-admin-org", action="store_true", help="Create the administrative organization")
parser.add_argument("--add-proxycache", action="store_true", help="Add ProxyCache to an organization", default=False)
parser.add_argument("--add-robot-account", action="store_true", help="Adds robot accounts to a personal account or an organization", default=False)
parser.add_argument("--add-super-user", action="store_true", help="Whether or not to add the super user for Quay", default=False)
parser.add_argument('--config-file', help="The full path to the config file", required=True)
parser.add_argument("--configure-secondary-quay-server", action="store_true", help="If this flag is set, assume that you are installing a quay mirror. The quay sync program will activate assuming this server is the secondary.")
parser.add_argument("--debug", action="store_true", help="Should debug be turned on. Files will be written to disk and not cleaned up")
parser.add_argument("--initialize-user", action="store_true", help="Create the first user for Quay")
parser.add_argument("--initialize-oauth", action="store_true", help="Create the first OAUTH token for Quay")
parser.add_argument("--manage-orgs", action="store_true", help="Whether or not this program should create/remove orgs in the config.yaml")
parser.add_argument("--openshift-yaml-dir", help="The full path to the YAML files to apply to the cluster. They should be prefixed with the a number associated with the order to apply them.")
parser.add_argument("--overwrite-proxycache", action="store_true", help="Should any current proxycache be overridden?")
parser.add_argument("--setup-quay-openshift", action="store_true", help="Have the management script apply OpenShift Quay configs")
parser.add_argument("--skip-tls-verify", action="store_true", help="Ignore self signed certs on registries", default=False)
parser.add_argument("--take-ownership", action="store_true", help="Ensure that the quay user used in the automation has ownership over all orgs")
parser.add_argument("--take-ownership-all-super-users", action="store_true", help="Referencing the OpenShift secret, ensure all super users own all orgs")
args = parser.parse_args()

if args.debug:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)



if __name__ == "__main__":
    logging.info(f"----> Starting at {datetime.datetime.now()}")
    start_time = time.perf_counter()
    quay_config = BaseOperations(args.config_file, args=args)
    
    check_quay_options = True
    openshift_logged_in = False
    if args.add_super_user:
        # There may be cases where the Quay information is not required
        # It is likely that the config file and only one other argument are passed in 
        # Adding super users only requires editing the secret in OpenShift assuming that you are using central auth
        number_of_args_passed_in = 0
        for user_args in vars(args):
            if getattr(args, user_args):
                # Debug options should not be counted as it doesn't influence the required options
                if user_args == "debug":
                    continue
                number_of_args_passed_in +=1
        # If there are only the config file and a single option probably can skip the quay info parsing
        if number_of_args_passed_in <= 2:
            check_quay_options = False
    if check_quay_options:
        # The sync runs in a different process so we should only be taking actions on a single host
        # Therefore we can collapse the variables and just change the inputs for clarity
        if args.configure_secondary_quay_server:
            quay_server = "secondary_server"
            quay_token = "secondary_token"
            quay_user = "secondary_quay_user"
            quay_secret_config = "seconday_quay_init_config"
        else:
            quay_server = "primary_server"
            quay_token = "primary_token"
            quay_user = "primary_quay_user"
            quay_secret_config = "primary_quay_init_config"
        
        # These options don't need Quay Information
        dont_need_quay = ["initialize_oauth", "setup_quay_openshift", "add_super_user"]
        
        # We want to capture any arguments passed in by the user
        # which will be True
        active_args = []
        for arg in vars(args):
            if arg == "skip_tls_verify" :
                continue
            if arg == "debug":
                continue
            if eval(f"args.{arg}") == True:
                active_args.append(arg)
        need_quay_info = False
        if active_args:
            for arg in active_args:
                if arg not in dont_need_quay:
                    need_quay_info = True
                    break
        
        if need_quay_info:
            quay_url = eval("quay_config.%s" % quay_server)
            quay_username = eval("quay_config.%s" %  quay_user)
            quay_api_token = eval("quay_config.%s" % quay_token)
            quay_server_api = QuayAPI(base_url=quay_url, api_token=quay_api_token)    
            quay_management = QuayManagement(quay_url=quay_url, quay_config=quay_config)

    if args.add_super_user or args.setup_quay_openshift or args.initialize_oauth or args.take_ownership_all_super_users:
        quay_namespace = quay_config.primary_quay_namespace
        if args.configure_secondary_quay_server:
            quay_namespace = quay_config.secondary_quay_namespace

    # The order might matter. We need to make sure quay is setup first, if that option is passed in
    # After quay is setup, if we are initializing a user that has to happen next
    # If neither of these options are passed in, we assume that we have a valid username and token
    # as well as the appropriate permissions to make modifications to Quay (i.e. we are a super user)
    if args.setup_quay_openshift:
        quay_init_config = eval("quay_config.%s" % quay_secret_config)
        quay_config.primary_quay_init_config
        OpenShiftCommands.openshift_login(api_url=quay_config.openshift_api_url, username=quay_config.openshift_username, passwd=quay_config.openshift_password)
        openshift_logged_in = True
        yaml_list = BaseOperations.yaml_file_list(quay_config.openshift_yaml_dir)
        for yaml_file in yaml_list:
            delay = False
            logging.info(f"Apply ---> {yaml_file} \n")
            which_yaml_file = BaseOperations.load_config(config_file=yaml_file)
            try:
                number_of_replicas = which_yaml_file['spec']['replicas']
            except:
                # Its possible that the yaml doesn't have replicas, so ignore that error
                pass
            if which_yaml_file['kind'] == "Subscription":
                if which_yaml_file['metadata']['name'] == "quay-operator":
                    # We need to strip out LDAP in order to initialize the user
                    ldap_in_config = any("ldap" in key.lower() for key in BaseOperations.load_config(config_file=quay_init_config))
                    if ldap_in_config:
                        quay_init_config_origin = quay_init_config
                        # This config file has the LDAP bits removed as it is a copy of the original config
                        quay_init_config = BaseOperations.strip_ldap_from_config(quay_init_config)
                    OpenShiftCommands.openshift_create_secret(namespace=quay_namespace, file_path=quay_init_config)
                    OpenShiftCommands.openshift_apply_file(yaml_file)
                    logging.debug("----> Waiting for the Quay Registry to be created...")
                    OpenShiftCommands.openshift_waitfor_object(
                                                                openshift_object="quayregistry", 
                                                                iterations=10, 
                                                                delay_between_checks=100, 
                                                                namespace=quay_namespace, 
                                                                crd="quayregistry"
                                                                )
                elif which_yaml_file['metadata']['name'] == "odf-operator":
                    OpenShiftCommands.openshift_apply_file(yaml_file)
                    namespace: str = None, 
                    OpenShiftCommands.openshift_waitfor_pods(
                                                            openshift_object="pods", 
                                                            iterations=15, 
                                                            delay_between_checks=60, 
                                                            number_of_pods=7,
                                                            namespace="openshift-storage"
                                                            )     
                else:
                    delay = True
                    OpenShiftCommands.openshift_apply_file(yaml_file)
            elif which_yaml_file['kind'] == "MachineSet":
                infraID_output = OpenShiftCommands.openshift_get_object(object_type="infrastructure", object_name="cluster")
                current_infraID = OpenShiftCommands.openshift_get_infrastructure_name(command_output=infraID_output)
                new_machineset_location = BaseOperations.replace_infraID(path_to_original_file=yaml_file, new_infra_id=current_infraID)
                
                OpenShiftCommands.openshift_apply_file(new_machineset_location)
                logging.debug("----> Waiting for the nodes to be created")
                OpenShiftCommands.openshift_waitfor_object(
                                                            openshift_object="node", 
                                                            iterations=20, 
                                                            delay_between_checks=60, 
                                                            label="cluster.ocs.openshift.io/openshift-storage", 
                                                            replicas=number_of_replicas
                                                            )
            elif which_yaml_file['kind'] == "StorageCluster":
                OpenShiftCommands.openshift_apply_file(yaml_file)
                logging.debug("----> Waiting for the ODF PVCs to be ready...")
                OpenShiftCommands.openshift_waitfor_storage(namespace="openshift-storage", openshift_object="pvc", iterations=35, delay_between_checks=60)
            else:           
                OpenShiftCommands.openshift_apply_file(yaml_file)
            if delay:
                    time.sleep(700)
        # Introduce a small delay after the quay registry object is detected to make sure that the deployment objects are created
        time.sleep(60)
        quay_deployment = yaml.load(OpenShiftCommands.openshift_get_object(namespace=quay_namespace, object_type="deployment", label="quay-component=quay"), Loader=yaml.FullLoader)
        number_of_replicas = quay_deployment['items'][0]['spec']['replicas']
        logging.debug("----> Waiting for the Quay Pods with the label 'quay-component=quay' to become ready ...")
        OpenShiftCommands.openshift_waitfor_object(
                                                        openshift_object="pod", 
                                                        iterations=20, 
                                                        delay_between_checks=90, 
                                                        label="quay-component=quay-app", 
                                                        replicas=number_of_replicas,
                                                        namespace=quay_namespace
                                                        )
        # Just because the container says running doesn't mean its warmed up so give it another bit of time
        time.sleep(90)

    if args.initialize_user:
        # Do we create the first user via the one-time use API endpoint Quay has?
        new_config_line = {}
        user_info = {"username": quay_config.initialize_username, "password": quay_config.initialize_password, "email": quay_config.initialize_email, "access_token": "true"}
        logging.debug(f"Establishing connection to {quay_url}")
        quay_server_api = QuayAPI(base_url=quay_url)
        logging.info("Attempting to create the intiale user")
        initial_user_response = quay_server_api.create_initial_user(user_info=user_info)
        logging.debug(f"The initial user request response: {initial_user_response}")
        access_token = ast.literal_eval(initial_user_response.text.strip("\n"))
        token_name = "primary_init_token"
        if args.configure_secondary_quay_server:
            token_name = "secondary_init_token"
        if args.debug:
            logging.debug("Writing the initial user information to /tmp/initial_user. File contents below:")
            logging.debug(initial_user_response.content.decode())
            with open("/tmp/initial_user", "w") as f:
                f.write(initial_user_response.content.decode())
                f.close()
        new_config_line[token_name] = access_token['access_token']
        logging.debug(f"Writing initial user config to {args.config_file}")
        quay_config.add_to_config(args.config_file, new_config_line)
        # reread the config file
        quay_config = BaseOperations(args.config_file, args=args)
        init_config_token_name = eval("quay_config.%s" % token_name)
        if args.setup_quay_openshift:
            # The thought is that if we are setting up Quay on Openshift at the same time as we initialize the user
            # We have removed the LDAP info in order to initialize the user (can't initialize a user if LDAP is present)
            # now that the initialization has completed, add the LDAP information back in
            quay_init_config = eval("quay_config.%s" % quay_secret_config)
            ldap_in_config = any("ldap" in key.lower() for key in BaseOperations.load_config(config_file=quay_init_config))
            if ldap_in_config:
                # dig out the secret name from the quay registry object incase the cluster was installed values other than defaults
                quay_registry_object = yaml.load(OpenShiftCommands.openshift_get_object(**{"namespace": quay_namespace,  
                                                                                "object_type": "quayregistry"}), Loader=yaml.FullLoader)
                registry_object_secret = quay_registry_object['items'][0]['spec']['configBundleSecret']
                # Regenerate the original secret with LDAP information
                OpenShiftCommands.openshift_replace_quay_init_secret(full_path_to_file=quay_init_config, secret_name=registry_object_secret, namespace=quay_namespace)
                logging.info("Pausing to let the secret rotate fully")
                time.sleep(15)
                # Roll the pods automatically so that the ldap stuff gets picked up again
                quay_deployment = yaml.load(OpenShiftCommands.openshift_get_object(namespace=quay_namespace, object_type="deployment", label="quay-component=quay"), Loader=yaml.FullLoader)
                number_of_replicas = quay_deployment['items'][0]['spec']['replicas']
                OpenShiftCommands.openshift_delete_object(object_type="pods", namespace=quay_namespace, label="quay-component=quay-app", grace_period="0")
                time.sleep(60)
                OpenShiftCommands.openshift_waitfor_pods(namespace=quay_namespace, iterations=10, delay_between_checks=90, number_of_pods=number_of_replicas)
                # just becasue the pods are ready doesn't mean they are warmed up
                time.sleep(90)

    if args.add_super_user:
        # If we haven't logged into OpenShift yet, do so now
        if not openshift_logged_in:
            logging.debug(f"Attempting to login into {quay_config.openshift_api_url} as {quay_config.openshift_username}")
            OpenShiftCommands.openshift_login(api_url=quay_config.openshift_api_url, username=quay_config.openshift_username, passwd=quay_config.openshift_password)
            openshift_logged_in = True
        logging.info("Attempting to add super users to OpenShift secret")
        quay_registry_object = yaml.load(OpenShiftCommands.openshift_get_object(**{"namespace": quay_namespace,  
                                                                            "object_type": "quayregistry"}), Loader=yaml.FullLoader)
        registry_object_name = quay_registry_object['items'][0]['metadata']['name']
        registry_object_secret = quay_registry_object['items'][0]['spec']['configBundleSecret']
        quay_init_secret = yaml.load(OpenShiftCommands.openshift_get_object(**{"namespace": quay_namespace, 
                                                                                    "object_name": registry_object_secret, 
                                                                                    "object_type": "secret"}), Loader=yaml.FullLoader)
        quay_init_secret_decoded = QuayManagement.process_quay_secret(quay_init_secret=quay_init_secret, quay_config=quay_config, quay_secret_section="SUPER_USERS")
        if args.debug:
            logging.debug("The contents of the Quay Secret is:")
            print(quay_init_secret_decoded)
        with open("/tmp/quay_init_bundle.yaml", "w" ) as file:
            file.write(yaml.dump(quay_init_secret_decoded))
            file.close()
        logging.info(f"Replacing the secret {registry_object_secret}")
        output = OpenShiftCommands.openshift_replace_quay_init_secret(full_path_to_file="/tmp/quay_init_bundle.yaml", secret_name=registry_object_secret)
    
    def create_admin_org(quay_api_token):
        """
        Description:
            Local function that creates an admin org. This may be needed in both
            initialize_oauth and add_admin_org.
        Args:
            quay_api_token (_type_): Quay api token
        """
        time.sleep(10)
        quay_server_api = QuayAPI(base_url=quay_url, api_token=quay_api_token)
        logging.info(f"Attempting to create {quay_config.quay_admin_org}")
        quay_server_api.create_org(org_name=quay_config.quay_admin_org)
        response = quay_server_api.create_oauth_application(org_name=quay_config.quay_admin_org, application_name="oauth-automation")
        logging.debug(response)
        print()
    
    
    if args.add_admin_org:
        if args.initialize_user:
            quay_api_token = init_config_token_name
        create_admin_org(quay_api_token=quay_api_token)
        
        
    if args.initialize_oauth:
        # If we haven't logged into OpenShift yet, do so now
        if not openshift_logged_in:
            logging.debug(f"Attempting to login into {quay_config.openshift_api_url} as {quay_config.openshift_username}")
            OpenShiftCommands.openshift_login(api_url=quay_config.openshift_api_url, username=quay_config.openshift_username, passwd=quay_config.openshift_password)
            openshift_logged_in = True
        token = quay_config.primary_init_token
        if args.configure_secondary_quay_server:
            token = quay_config.secondary_init_token
        # We want to ensure an admin org exists so we can tie an oauth application to it
        create_admin_org(quay_api_token=token)
        
        pod_response = yaml.load(OpenShiftCommands.openshift_get_object(**{"namespace": quay_namespace, 
                                                                        "label": "quay-component=quay-app", 
                                                                        "object_type": "pods"}), Loader=yaml.FullLoader)
        select = "SELECT * FROM public.oauthapplication"
        
        logging.debug("Attempting get database information from the postgres-config-secret")
            
        all_quay_secrets = yaml.load(OpenShiftCommands.openshift_get_object(**{"namespace": quay_namespace, 
                                                                            "label": "quay-operator/quayregistry=central", 
                                                                            "object_type": "secret"}), Loader=yaml.FullLoader)
        db_secret_dict = {}
        for secret in all_quay_secrets['items']:
            if "postgres-config-secret" in secret['metadata']['name']:
                db_secret_dict = secret
        db_info = OpenShiftCommands.openshift_process_secret(secret=db_secret_dict)
        quay_db_service = yaml.load(OpenShiftCommands.openshift_get_object(**{"namespace": quay_namespace, 
                                                                            "label": "quay-component=postgres", 
                                                                            "object_type": "svc"}), Loader=yaml.FullLoader)['items'][0]['metadata']['name']
        db_info['database-svc'] = quay_db_service
        logging.debug(f"The database secret is:")
        logging.debug(db_info)
        oauthapplication_script_location = quay_config.create_db_info_script(select_statement=select, db_info=db_info)
        OpenShiftCommands.openshift_transfer_file(filename=oauthapplication_script_location,  
                                                pod_name=pod_response['items'][0]['metadata']['name'], 
                                                namespace=quay_namespace)
        
        logging.debug("Retrieving current records from public.oauthapplication")
        logging.debug(f"Running /tmp/generic.py in the {pod_response['items'][0]['metadata']['name']} pod")
        if args.debug:
            logging.debug("The contents of the database script is:")
            with open(oauthapplication_script_location) as file:
                print(file.read())
        oauthapplication_select_output = ast.literal_eval(OpenShiftCommands.openshift_exec_pod(pod_name=pod_response['items'][0]['metadata']['name'], 
                                                                                        namespace=quay_namespace,
                                                                                        command=["/usr/bin/python", "/tmp/generic.py"]).decode().strip("\n").strip("\r"))
        

        select = "SELECT * FROM public.oauthaccesstoken"
        oauthaccesstoken_script_location = quay_config.create_db_info_script(select_statement=select, db_info=db_info)
        OpenShiftCommands.openshift_transfer_file(filename=oauthaccesstoken_script_location, 
                                                pod_name=pod_response['items'][0]['metadata']['name'], 
                                                namespace=quay_namespace)

        logging.debug("Retrieving current records from public.oauthaccesstoken")
        logging.debug(f"Running /tmp/generic.py in the {pod_response['items'][0]['metadata']['name']} pod")
        if args.debug:
            logging.debug("The contents of the database script is:")
            with open(oauthaccesstoken_script_location) as file:
                print(file.read())    
        oauthaccesstoken_select_output = ast.literal_eval(OpenShiftCommands.openshift_exec_pod(pod_name=pod_response['items'][0]['metadata']['name'], 
                                                                                        namespace=quay_namespace,
                                                                                        command=["/usr/bin/python", "/tmp/generic.py"]).decode().strip("\n").strip("\r"))
        
        oauth_app_database_id = ""
        oauth_app_org_id = ""
        oauth_access_uid = ""
        oauth_access_app_id = ""
        for key in oauthapplication_select_output:
            if oauthapplication_select_output[key]['oauth_name'] == "automation":
                logging.debug("Found the 'automation' OAUTH application")
                logging.debug("This is being used to tie the OAUTH key to")
                logging.debug(oauthapplication_select_output[key])
                oauth_app_database_id = key
                oauth_app_org_id = oauthapplication_select_output[key]['org_id']


        for key in oauthaccesstoken_select_output:
            if oauthaccesstoken_select_output[key]['app_id'] == oauth_app_database_id:
                logging.debug("Found the oauth database records")
                logging.debug(oauthaccesstoken_select_output[key])
                oauth_access_uid = oauthaccesstoken_select_output[key]['user_id']
                oauth_access_app_id = oauthaccesstoken_select_output[key]['app_id']

        initialize_oauth_script, oauth_token = quay_config.create_initial_oauth_script(user_id=oauth_access_uid, 
                                            app_id=oauth_access_app_id, 
                                            db_info=db_info)
        if args.debug:
            logging.debug(f"Attempting to transfer {initialize_oauth_script} to {pod_response['items'][0]['metadata']['name']}")
            logging.debug("The contents of the database script is:")
            with open(initialize_oauth_script) as file:
                print(file.read())  
        OpenShiftCommands.openshift_transfer_file(filename=initialize_oauth_script, 
                                                pod_name=pod_response['items'][0]['metadata']['name'], 
                                                namespace=quay_namespace)
        oauthaccesstoken_db_output = ast.literal_eval(OpenShiftCommands.openshift_exec_pod(pod_name=pod_response['items'][0]['metadata']['name'], 
                                                                                        namespace=quay_namespace,
                                                                                        command=["/usr/bin/python", "/tmp/generic.py"]).decode().strip("\n").strip("\r"))
        if args.debug: 
            logging.debug(f"Database activities respose: {oauthaccesstoken_db_output}")
            logging.debug(f"The generated token is: {oauth_token}")
        if not args.debug:
            OpenShiftCommands.openshift_exec_pod(pod_name=pod_response['items'][0]['metadata']['name'], 
                                                                                        namespace=quay_namespace,
                                                                                        command=["/usr/bin/rm", "/tmp/generic.py"])
        
        new_line = {"primary_token": oauth_token}
        if args.configure_secondary_quay_server:
            new_line = {"secondary_token": oauth_token}
    
        if args.debug:
            logging.debug("Rereading the config files and regenerating API sessions with new token...")
        quay_config.add_to_config(config_path=args.config_file, insert_dict=new_line)
        # reread the config file because it should have new information in it
        quay_config = BaseOperations(args.config_file, args=args)

    if args.manage_orgs:
        if args.initialize_user:
            quay_api_token = init_config_token_name
        quay_server_api = QuayAPI(base_url=quay_url, api_token=quay_api_token)
        for key in quay_config.organizations:
            if quay_config.organizations[key]['present']:
                quay_server_api.create_org(org_name=key)
            else:
                quay_server_api.delete_org(org_name=key)

    if args.add_proxycache:
        quay_management.add_proxycache(quay_api=quay_server_api, overwrite=args.overwrite_proxycache)

    if args.add_robot_account:
        robots_exist = quay_management.get_robot(username=quay_username)
        quay_management.add_robot_acct(robot_exists=robots_exist, username=quay_username, quay_api_object=quay_server_api)
    
    if args.take_ownership:
        quay_server_api = QuayAPI(base_url=quay_url, api_token=quay_api_token)
        orgs = quay_server_api.get_org()
        QuayManagement.take_org_ownership(quay_username=quay_username, orgs=orgs, quay_server_api=quay_server_api)
    
    if args.take_ownership_all_super_users:
        quay_server_api = QuayAPI(base_url=quay_url, api_token=quay_api_token)
        orgs = quay_server_api.get_org()
        quay_registry_object = yaml.load(OpenShiftCommands.openshift_get_object(**{"namespace": quay_namespace,  
                                                                            "object_type": "quayregistry"}), Loader=yaml.FullLoader)
        registry_object_name = quay_registry_object['items'][0]['metadata']['name']
        registry_object_secret = quay_registry_object['items'][0]['spec']['configBundleSecret']
        quay_init_secret = yaml.load(OpenShiftCommands.openshift_get_object(**{"namespace": quay_namespace, 
                                                                                    "object_name": registry_object_secret, 
                                                                                    "object_type": "secret"}), Loader=yaml.FullLoader)
        quay_init_secret_decoded = yaml.load(base64.b64decode(quay_init_secret['data']['config.yaml']), Loader=yaml.FullLoader)  
        user_list = quay_init_secret_decoded['SUPER_USERS']
        QuayManagement.take_org_ownership(quay_username=user_list, orgs=orgs, quay_server_api=quay_server_api)
    end_time = time.perf_counter()
    total_time = math.ceil((end_time - start_time)/60)
    logging.info(f"Total run time ---> {total_time} minutes <---")
    logging.info(f"----> Finished at {datetime.datetime.now()}")