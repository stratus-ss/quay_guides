import yaml
import logging
import os
import tempfile
from random import SystemRandom as Random
import bcrypt
import string
from uuid import uuid4;
        
class BaseOperations:
    def __init__(self, config_file, args: dict = None):
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
                        "quay_admin_org": {"type": "string", "desc": "The name of the organization where the initial OAUTH token will reside"},
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
            self.source_quay_user = self.config["source_quay_user"]
            self.source_quay_password = self.config["source_quay_password"]
            try:
                self.quay_init_config = self.config['quay_init_config']
            except:
                pass
            
            try:
                self.openshift_api = self.config['openshift_api_url']
            except:
                pass
            try: 
                self.quay_admin_org = self.config['quay_admin_org']
            except:
                pass
            try:
                self.init_token = self.config['init_token']
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

    @staticmethod
    def create_initial_oauth_script(user_id: str = None, app_id: str = None, db_info: dict = None) -> str:
        """
        Description:
            Creates a small script that makes some database inserts to manually create an oauth token. 
            This is a workaround because Quay does not allow you to programmatically create an oauth 
            token without first having an oauth token.
        Args:
            user_id (str, optional): _description_. Defaults to None.
            app_id (str, optional): _description_. Defaults to None.
            org_id (int, optional): _description_. Defaults to None.
        Returns:
            The path to the file that was written
        """
        local_file_location = "/tmp/generic.py"
        random = Random()
        token = ''.join([random.choice(string.ascii_uppercase + string.digits) for _ in range(40)])
        bcrypt_token = bcrypt.hashpw(token[20:].encode("utf-8"), bcrypt.gensalt())
        short_token = token[:20]
        db_command = f"""INSERT INTO public.oauthaccesstoken " + 
"(uuid, application_id, authorized_user_id, scope, token_type, expires_at, data, token_code, token_name) " +
f"VALUES ('{str(uuid4())}', {app_id}, {user_id}, 'super:user org:admin user:admin user:read repo:create repo:admin repo:write repo:read', " +
f"'Bearer', '2033-12-15 00:00:00.0', '', '{bcrypt_token.decode()}', '{short_token}') RETURNING public.oauthaccesstoken.id;"""
        connection_string = f"dbname='{db_info['database-name']}' user='{db_info['database-username']}' host='{db_info['database-svc']}' password='{db_info['database-password']}'"

        python_script = """#!/usr/bin/python
import psycopg2;
conn = psycopg2.connect(\"%s\") ;
cur = conn.cursor();
cur.execute(\"%s\");
print(cur.fetchall())
conn.commit()
cur.close()
""" % (connection_string, db_command)
        with open(local_file_location, "w") as f:
            f.write(python_script)
            f.close()
        return(local_file_location, token)
    
    @staticmethod
    def create_db_info_script(select_statement: str = None, db_info: dict = None) -> str:
        """
        Description:
            Creates a script that retrieves oauthapplication and oauthaccesstoken tables from the Quay database
        Args:
            select_statement (str, optional): A SELECT statement for sql getting all entries for a give table. Defaults to None.
            db_info (dict, optional): This is the processed output from the openshift secret that has database connection info. Defaults to None.
        Returns:
            Full path to the script to transfer
        """
        local_file_location = "/tmp/generic.py"
        connection_string = f"dbname='{db_info['database-name']}' user='{db_info['database-username']}' host='{db_info['database-svc']}' password='{db_info['database-password']}'"
        if "oauthapplication" in select_statement:
            while_loop = """
while counter < list_length:
    id = list(output[counter])[0]
    client_id = list(output[counter])[1]
    org_id = list(output[counter])[4]
    name = list(output[counter])[5]
    app_info_dict[id] = {'client_id': client_id, 'org_id': org_id, "oauth_name": name}
    counter +=1
"""
        elif "oauthaccesstoken" in select_statement:
            while_loop = """
while counter < list_length:
    database_id = list(output[counter])[0]
    uuid = list(output[counter])[1]
    app_id = list(output[counter])[2]
    user_id = list(output[counter])[3]
    app_info_dict[database_id] = {'uuid': uuid, 'app_id': app_id, 'user_id': user_id}
    counter +=1
"""
        else:
            pass
        python_script = """#!/usr/bin/python
import psycopg2;
conn = psycopg2.connect(\"%s\") ;
cur = conn.cursor();
cur.execute(\"%s\");
counter = 0
app_info_dict = {}
output = cur.fetchall()
list_length = len(output)
%s
print(app_info_dict)
""" % (connection_string, select_statement, while_loop)
        with open(local_file_location, "w") as f:
            f.write(python_script)
            f.close()
        return(local_file_location)
    
    @staticmethod
    def add_to_config(config_path: str = None, insert_dict: dict = None):
        logging.info(f"Reading {config_path}...")
        with open(config_path, "r") as file:
            yaml_dict = file.read()
        yaml_dict = yaml.load(yaml_dict, Loader=yaml.FullLoader)
        if not isinstance(insert_dict, dict):
            logging.error(f"Cannot add {insert_dict} to config file. It is not a dict")
            exit(1)   
        for key in insert_dict:
            yaml_dict[key] = insert_dict[key]
        file.close()
        logging.info(f"Writing new contents to {config_path}")
        with open(config_path, "w") as file:
            file.write(yaml.dump(yaml_dict))
            file.close()