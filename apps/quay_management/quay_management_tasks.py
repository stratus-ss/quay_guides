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

logging.basicConfig(level=logging.INFO)
parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('--username', help='Quay Username')
parser.add_argument('--password', help='Quay Password')
parser.add_argument('--config-file', help="The full path to the config file", required=True)
parser.add_argument("--skip-tls-verify", action="store_true", help="Ignore self signed certs on registries", default=False)
parser.add_argument("--add-proxycache", action="store_true", help="Add ProxyCache to an organization", default=False)
parser.add_argument("--overwrite-proxycache", action="store_true", help="Should any current proxycache be overridden?")
parser.add_argument("--add-robot-account", action="store_true", help="Adds robot accounts to a personal account or an organization", default=False)
parser.add_argument("--setup-quay-openshift", action="store_true", help="Have the management script apply OpenShift Quay configs")
parser.add_argument("--openshift-yaml-dir", help="The full path to the YAML files to apply to the cluster. They should be prefixed with the a number associated with the order to apply them.")
parser.add_argument("--initialize-user", action="store_true", help="Create the first user for Quay")
parser.add_argument("--initialize-oauth", action="store_true", help="Create the first OAUTH token for Quay")
parser.add_argument("--add-admin-org", action="store_true", help="Create the administrative organization")
parser.add_argument("--destination-quay-install", action="store_true", help="If this flag is set, assume that you are installing a quay mirror. The quay sync program will activate assuming this server is the destination.")
args = parser.parse_args()



if __name__ == "__main__":
    logging.info(f"----> Starting at {datetime.datetime.now()}")
    start_time = time.perf_counter()
    quay_config = BaseOperations(args.config_file)

    if not quay_config.failover:
        source_server = quay_config.source_server
        destination_server = quay_config.destination_server
    else:
        source_server = quay_config.destination_server
        destination_server = quay_config.source_server

   # Create an instance of QuayAPI for the source server
    source_quay_api = QuayAPI(base_url=source_server, api_token=quay_config.source_token)

    # Create an instance of the QuayAPI class for the destination server
    destination_quay_api = QuayAPI(base_url=destination_server, api_token=quay_config.destination_token)

    if args.destination_quay_install:
        action_this_cluster = destination_quay_api
    else:
        action_this_cluster = source_quay_api

    user_info = {"username": quay_config.destination_quay_user, "password": quay_config.destination_quay_password, "email": quay_config.destination_quay_email, "access_token": "true"}
           
    # {"org_name": <name>, "upstream_registry": <url>, "upstream_registry_password": <password>, "upstream_registry_username": <user>}
    
    quay_management = QuayManagement(source_url=source_server, quay_config=quay_config)
    
    if args.setup_quay_openshift:
        if quay_config.quay_init_config:
            OpenShiftCommands.openshift_login(api_url=quay_config.openshift_api, username=quay_config.openshift_username, passwd=quay_config.openshift_password)
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
                        OpenShiftCommands.openshift_create_secret(namespace="quay", file_path=quay_config.quay_init_config)
                        OpenShiftCommands.openshift_apply_file(yaml_file)
                        OpenShiftCommands.openshift_waitfor_object(
                                                                    openshift_object="quayregistry", 
                                                                    iterations=10, 
                                                                    delay_between_checks=60, 
                                                                    namespace="quay", 
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
                    OpenShiftCommands.openshift_waitfor_object(
                                                                openshift_object="node", 
                                                                iterations=20, 
                                                                delay_between_checks=60, 
                                                                label="cluster.ocs.openshift.io/openshift-storage", 
                                                                replicas=number_of_replicas
                                                                )
                elif which_yaml_file['kind'] == "StorageCluster":
                    OpenShiftCommands.openshift_apply_file(yaml_file)
                    OpenShiftCommands.openshift_waitfor_storage(namespace="openshift-storage", openshift_object="pvc", iterations=35, delay_between_checks=60)
                else:           
                    OpenShiftCommands.openshift_apply_file(yaml_file)
                if delay:
                        time.sleep(700)
    
    if args.initialize_user:
        new_config_line = {}
        user_info = {"username": quay_config.destination_quay_user, "password": quay_config.destination_quay_password, "email": quay_config.destination_quay_email, "access_token": "true"}
        destination_quay_api = QuayAPI(base_url=quay_config.destination_server)
        initial_user_response = destination_quay_api.create_initial_user(user_info=user_info)
        access_token = ast.literal_eval(initial_user_response.text.strip("\n"))
        with open("/tmp/initial_user", "w") as f:
            f.write(initial_user_response.content.decode())
            f.close()
        new_config_line['init_token'] = api_token=access_token['access_token']
        quay_config.add_to_config(args.config_file, new_config_line)
        # reread the config file
        quay_config = BaseOperations(args.config_file)

    if args.add_admin_org:
        if args.initialize_user:
            api_token = quay_config.init_token
        elif not args.destination_quay_install:
            api_token = quay_config.source_token
        else:
            api_token = quay_config.destination_token
        destination_quay_api = QuayAPI(base_url=quay_config.destination_server, api_token=api_token)
        destination_quay_api.create_org(org_name=quay_config.quay_admin_org)
        response = destination_quay_api.create_oauth_application(org_name=quay_config.quay_admin_org)
        print()
    if args.initialize_oauth:
        OpenShiftCommands.openshift_login(api_url=quay_config.openshift_api, username=quay_config.openshift_username, passwd=quay_config.openshift_password)
        pod_response = yaml.load(OpenShiftCommands.openshift_get_object(**{"namespace": "quay", 
                                                                        "label": "quay-component=quay-app", 
                                                                        "object_type": "pods"}), Loader=yaml.FullLoader)
        select = "SELECT * FROM public.oauthapplication"
        all_quay_secrets = yaml.load(OpenShiftCommands.openshift_get_object(**{"namespace": "quay", 
                                                                            "label": "quay-operator/quayregistry=central", 
                                                                            "object_type": "secret"}), Loader=yaml.FullLoader)
        db_secret_dict = {}
        for secret in all_quay_secrets['items']:
            if "central-postgres-config-secret" in secret['metadata']['name']:
                db_secret_dict = secret
        db_info = OpenShiftCommands.openshift_process_secret(secret=db_secret_dict)
        quay_db_service = yaml.load(OpenShiftCommands.openshift_get_object(**{"namespace": "quay", 
                                                                            "label": "quay-component=postgres", 
                                                                            "object_type": "svc"}), Loader=yaml.FullLoader)['items'][0]['metadata']['name']
        db_info['database-svc'] = quay_db_service
        oauthapplication_script_location = quay_config.create_db_info_script(select_statement=select, db_info=db_info)
        OpenShiftCommands.openshift_transfer_file(filename=oauthapplication_script_location,  
                                                pod_name=pod_response['items'][0]['metadata']['name'], 
                                                namespace="quay")
        oauthapplication_output = ast.literal_eval(OpenShiftCommands.openshift_exec_pod(pod_name=pod_response['items'][0]['metadata']['name'], 
                                                                                        namespace="quay",
                                                                                        command=["/usr/bin/python", "/tmp/generic.py"]).decode().strip("\n").strip("\r"))


        select = "SELECT * FROM public.oauthaccesstoken"
        oauthaccesstoken_script_location = quay_config.create_db_info_script(select_statement=select, db_info=db_info)
        OpenShiftCommands.openshift_transfer_file(filename=oauthaccesstoken_script_location, 
                                                pod_name=pod_response['items'][0]['metadata']['name'], 
                                                namespace="quay")
        oauthaccesstoken_output = ast.literal_eval(OpenShiftCommands.openshift_exec_pod(pod_name=pod_response['items'][0]['metadata']['name'], 
                                                                                        namespace="quay",
                                                                                        command=["/usr/bin/python", "/tmp/generic.py"]).decode().strip("\n").strip("\r"))

        oauth_app_database_id = ""
        oauth_app_org_id = ""
        oauth_access_uid = ""
        oauth_access_app_id = ""
        for key in oauthapplication_output:
            if oauthapplication_output[key]['oauth_name'] == "automation":
                oauth_app_database_id = key
                oauth_app_org_id = oauthapplication_output[key]['org_id']

        for key in oauthaccesstoken_output:
            if oauthaccesstoken_output[key]['app_id'] == oauth_app_database_id:
                oauth_access_uid = oauthaccesstoken_output[key]['user_id']
                oauth_access_app_id = oauthaccesstoken_output[key]['app_id']

        initialize_oauth_script, oauth_token = quay_config.create_initial_oauth_script(user_id=oauth_access_uid, 
                                            app_id=oauth_access_app_id, 
                                            db_info=db_info)
        OpenShiftCommands.openshift_transfer_file(filename=initialize_oauth_script, 
                                                pod_name=pod_response['items'][0]['metadata']['name'], 
                                                namespace="quay")
        oauthaccesstoken_output = ast.literal_eval(OpenShiftCommands.openshift_exec_pod(pod_name=pod_response['items'][0]['metadata']['name'], 
                                                                                        namespace="quay",
                                                                                        command=["/usr/bin/python", "/tmp/generic.py"]).decode().strip("\n").strip("\r"))
        
        if args.destination_quay_install:
            new_line = {"destination_token": oauth_token}
        else:
            new_line = {"source_token": oauth_token}
        quay_config.add_to_config(config_path=args.config_file, insert_dict=new_line)
        # reread the config file because it should have new information in it
        quay_config = BaseOperations(args.config_file)
        # regenerate api session
        if args.destination_quay_install:
            action_this_cluster = QuayAPI(base_url=destination_server, api_token=quay_config.destination_token)
        else:
            action_this_cluster = QuayAPI(base_url=source_server, api_token=quay_config.source_token)
        # Refresh the config in the quay_management class instantiation
        quay_management = QuayManagement(source_url=source_server, quay_config=quay_config)
    if args.add_proxycache:
        quay_management.add_proxycache(source_quay_api=action_this_cluster, overwrite=args.overwrite_proxycache)

    if args.add_robot_account:
        robots_exist = quay_management.get_robot(username=quay_config.source_quay_user)
        quay_management.add_robot_acct(robot_exists=robots_exist, username=quay_config.source_quay_user, quay_api_object=source_quay_api)
    end_time = time.perf_counter()
    total_time = math.ceil((end_time - start_time)/60)
    logging.info(f"Total run time ---> {total_time} minutes <---")
    logging.info(f"----> Finished at {datetime.datetime.now()}")