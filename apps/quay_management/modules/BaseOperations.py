import yaml
import logging
import os
import tempfile

class BaseOperations:
    def __init__(self, config_file):
        self.config = BaseOperations.load_config(config_file=config_file)
        expected_config_values = {
                        "destination_quay_user": {"type": "string", "desc": "Username for target quay instance" },
                        "destination_quay_password": {"type": "string", "desc": "Password for target instance quay user"},
                        "destination_quay_email": {"type": "string", "desc": "Email for target instance quay user"},
                        "destination_token": {"type": "string", "desc": "OAUTH token for target quay instance. Should have super user permissions"},
                        "destination_server": {"type": "string", "desc": "URL for the destination quay instance"},
                        "failover": {"type": "string", "desc": "Should the source and destination be flipped in the event of a failover"},
                        "openshift_api_url": {"type": "string", "desc": "Login URL for OpenShift where Quay will be installed/managed"},
                        "openshift_username": {"type": "string", "desc": "OpenShift cluster admin username"},
                        "openshift_password": {"type": "string", "desc": "OpenShift cluster admin password"},
                        "openshift_yaml_dir": {"type": "string", "desc": "Full path to the directory with YAMLs to be applied to the OpenShift cluster"},
                        "respositories": {"type": "list", "desc": "Yaml list of repositories to mirror in the format <org>/<repo>:tag"},
                        "robot_config": {"type": "dict", "desc": "A dictionary that contains the robot information. In the format of {'<bot_name>': { 'type': '<org>', 'org_name': '<org>, 'name': <name>}}"},
                        "proxycache": {"type": "dict", "desc": "A dictionary of proxy config in the format of {'<org_name>': { 'org_name': '<org_name>', 'upstream_registry_username': '<user>, 'upstream_registry_username': <passwd>}, 'upstream_registry': <url>}"},
                        "source_server": {"type": "string", "desc": "URL for the source quay instance"},
                        "source_token": {"type": "string", "desc": "OAUTH token for source quay instance. Should have super user permissions"},
                        "source_quay_password": {"type": "string", "desc": "Password for source quay"},
                        "source_quay_user": {"type": "string", "desc": "Username for source quay"},
                        "quay_init_config": {"type": "string", "desc": "Full path to the Quay settings of the init-config-bundle-secret"},
                            }
        try:
            self.destination_quay_user = self.config["destination_quay_user"]
            self.destination_quay_password = self.config["destination_quay_password"]
            self.destination_quay_email = self.config["destination_quay_email"]
            self.destination_token = self.config["destination_token"]
            self.destination_server = self.config["destination_server"]
            self.failover = self.config["failover"]
            self.openshift_username = self.config['openshift_username']
            self.openshift_password = self.config['openshift_password']
            self.openshift_yaml_dir = self.config['openshift_yaml_dir']
            self.repositories = self.config["repositories"]
            self.robot_config = self.config['robot_config']
            self.proxycache_config = self.config["proxycache"]
            self.source_server = self.config["source_server"]
            self.source_token = self.config["source_token"]
            try:
                self.quay_init_config = self.config['quay_init_config']
            except:
                pass
            
            try:
                self.openshift_api = self.config['openshift_api_url']
            except:
                pass
        except:
            logging.error("Unable to parse the config file. The following are the expected values and format of the config file")    
            for key, value in expected_config_values.items():
                print(f"""{key}:
                type: {expected_config_values[key]['type']}
                description: {expected_config_values[key]['desc']}\n"""
                )
            exit(1)

        
    @classmethod
    def load_config(cls, config_file: str) -> dict[str,str]:
        """
        Description: 
            Loads the configuration from the specified file.
        Args:
            config_file: The path to the configuration file.

        Returns:
            A dictionary containing the configuration data.
        """

        try:
            with open(config_file, 'r') as f:
                data = yaml.load(f, Loader=yaml.FullLoader)
        except FileNotFoundError:
            logging.critical(f"--> Config file not found: {config_file}")
            exit(1)
        except yaml.YAMLError as e:
            logging.critical(f"--> Error parsing config file: {e}")

            exit(1)
        return data

    @classmethod
    def do_i_skip_tls(cls, command: list[str], skip_tls_verify: bool = False ) -> list[str]:
        """
        Description: 
            Adds the `--tls-verify=false` flag to the specified command if `args.skip_tls_verify` is True.
        Args:
            command: The command to add the flag to.

        Returns:
            The updated command.
        """

        if skip_tls_verify:
            command.append("--tls-verify=false")
        return(command)

    @staticmethod
    def yaml_file_list(file_directory):
        files_list = []
        for root, dirs, files in os.walk(file_directory):
            for file in files:
                if root:
                    full_file_path = os.path.join(root, file)
                    if full_file_path not in files_list:
                        files_list.append(full_file_path)
        files_list.sort()
        return(files_list)

    @staticmethod
    def replace_infraID(path_to_original_file: str, new_infra_id: str) -> str:
        """
        Description:
            This is intended adjust a machine config so that it can be templated
        Args:
            path_to_original_file (str): This is the templated machineconfig
            new_infra_id (str): This is the infraID of the current cluster
        Return:
            The location of the temp file
        """
        with open(path_to_original_file, 'r') as read_file:
            filedata = read_file.read()
        filedata = filedata.replace('<INFRAID>', new_infra_id)
        new_machineset_file = tempfile.NamedTemporaryFile(delete=False)
        with open(new_machineset_file.name, 'w') as write_file:
            write_file.write(filedata)
        write_file.close()
        return(new_machineset_file.name)