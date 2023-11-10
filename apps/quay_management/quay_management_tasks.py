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
    
    # Set the base URL for the destination server
    destination_url = "https://%s/" % destination_server

    # Set the base URL for the source server
    source_url = "https://%s/" % source_server

   # Create an instance of QuayAPI for the source server
    source_quay_api = QuayAPI(base_url=source_url, api_token=quay_config.source_token)
#    source_quay_api = QuayAPI(base_url=source_url)

    # Create an instance of the QuayAPI class for the destination server
    destination_quay_api = QuayAPI(base_url=destination_url, api_token=quay_config.destination_token)

    user_info = {"username": quay_config.destination_quay_user, "password": quay_config.destination_quay_password, "email": quay_config.destination_quay_email, "access_token": "true"}
           
    # {"org_name": <name>, "upstream_registry": <url>, "upstream_registry_password": <password>, "upstream_registry_username": <user>}
    
    quay_management = QuayManagement(source_url=source_url, quay_config=quay_config)

    if args.add_proxycache:
        quay_management.add_proxycache(source_quay_api=source_quay_api, overwrite=args.overwrite_proxycache)

    if args.add_robot_account:
        robots_exist = quay_management.get_robot(username=args.username)
        quay_management.add_robot_acct(robot_exists=robots_exist, username=args.username)
    
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
                                                                iterations=25, 
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
                    OpenShiftCommands.openshift_waitfor_storage(namespace="openshift-storage", openshift_object="pvc", iterations=20, delay_between_checks=60)
                else:           
                    OpenShiftCommands.openshift_apply_file(yaml_file)
                if delay:
                        time.sleep(700)
    end_time = time.perf_counter()
    total_time = math.ceil((end_time - start_time)/60)
    logging.info(f"Total run time ---> {total_time} minutes <---")
    logging.info(f"----> Finished at {datetime.datetime.now()}")