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
        expected_config_values = {}
        def build_dict(add_these_options: list[dict[str, str]] = None, incoming_dict: dict = None) -> dict:
            """
            Description:
                Creates or updates a dict to keep a running list of the required options depending on
                which args are passed into the script
            Args:
                add_these_options (list[dict[str, str]], optional): This is a list of dicts. It is expected to 
                        be nested. {"key": {"type": "value", "desc": "value"}} Defaults to None.
                incoming_dict (dict, optional): Either an empty or a pre-populated dict in the format as above. Defaults to None.

            Returns:
                dict: A dict with the name of the config option, a type and a description
            """
            if incoming_dict is None:
                incoming_dict = {}
            for item in add_these_options:
                for key, value in item.items():
                    incoming_dict[key] = value
            return incoming_dict
        ###############
        # This section is for options that arg parse may be looking for
        # The purpose is to show only the items required for a given flag
        all_options = {
                        "secondary_quay_user": {"type": "string", "desc": "Username for target quay instance" },
                        "secondary_quay_password": {"type": "string", "desc": "Password for target instance quay user"},
                        "secondary_token": {"type": "string", "desc": "OAUTH token for target quay instance. Should have super user permissions"},
                        "secondary_server": {"type": "string", "desc": "URL for the secondary quay instance"},
                        "secondary_init_token": {"type": "string", "desc": "The token that is generated by the setup process of this script. It is the hidden token for the initial user"},
                        "secondary_quay_init_config": {"type": "string", "desc": "The path to the quay configuration for secondary site"},
                        "failover": {"type": "string", "desc": "Should the primary and secondary be flipped in the event of a failover"},
                        "initialize_username": {"type": "string", "desc": "username for target instance initial quay user"},
                        "initialize_password": {"type": "string", "desc": "password that will be set for target instance initial quay user"},
                        "initialize_email": {"type": "string", "desc": "email address for target instance initial quay user"},
                        "openshift_api_url": {"type": "string", "desc": "Login URL for OpenShift where Quay will be installed/managed"},
                        "openshift_username": {"type": "string", "desc": "OpenShift cluster admin username"},
                        "openshift_password": {"type": "string", "desc": "OpenShift cluster admin password"},
                        "openshift_yaml_dir": {"type": "string", "desc": "Full path to the directory with YAMLs to be applied to the OpenShift cluster"},
                        "organizations": {"type": "dict", "desc": "A dictionary that tells the program which organizations should or should not exist in quay in the format of {'<org_name>': 'present': 'true/false'}"},
                        "proxycache": {"type": "dict", "desc": "A dictionary of proxy config in the format of {'<org_name>': { 'org_name': '<org_name>', 'upstream_registry_username': '<user>, 'upstream_registry_username': <passwd>}, 'upstream_registry': <url>}"},
                        "quay_admin_org": {"type": "string", "desc": "The name of the organization where the initial OAUTH token will reside"},
                        "repositories": {"type": "list", "desc": "Yaml list of repositories to mirror in the format <org>/<repo>:tag"},
                        "robot_config": {"type": "dict", "desc": "A dictionary that contains the robot information. In the format of {'<bot_name>': { 'type': '<org>', 'org_name': '<org>, 'name': <name>}}"},
                        "primary_server": {"type": "string", "desc": "URL for the primary quay instance"},
                        "primary_token": {"type": "string", "desc": "OAUTH token for primary quay instance. Should have super user permissions"},
                        "primary_quay_password": {"type": "string", "desc": "Password for primary quay"},
                        "primary_quay_user": {"type": "string", "desc": "Username for primary quay"},
                        "primary_quay_init_config": {"type": "string", "desc": "The path to the quay configuration for primary site"},
                        "primary_init_token": {"type": "string", "desc": "The token that is generated by the setup process of this script. It is the hidden token for the initial user"},
                            }
        sync_generic_options = {
                        "repositories": {"type": "list", "desc": "Yaml list of repositories to mirror in the format <org>/<repo>:tag"},
                        "secondary_quay_user": {"type": "string", "desc": "Username for target quay instance" },
                        "secondary_quay_password": {"type": "string", "desc": "Password for target instance quay user"},
                        "secondary_token": {"type": "string", "desc": "OAUTH token for target quay instance. Should have super user permissions"},
                        "secondary_server": {"type": "string", "desc": "URL for the secondary quay instance"},
                        "secondary_init_token": {"type": "string", "desc": "The token that is generated by the setup process of this script. It is the hidden token for the initial user"},
                        #"failover": {"type": "string", "desc": "Should the primary and secondary be flipped in the event of a failover"},
                        "primary_server": {"type": "string", "desc": "URL for the primary quay instance"},
                        "primary_token": {"type": "string", "desc": "OAUTH token for primary quay instance. Should have super user permissions"},
                        "primary_quay_password": {"type": "string", "desc": "Password for primary quay"},
                        "primary_quay_user": {"type": "string", "desc": "Username for primary quay"},
                        "primary_init_token": {"type": "string", "desc": "The token that is generated by the setup process of this script. It is the hidden token for the initial user"},
                            }
        openshift_options = {
                        "openshift_api_url": {"type": "string", "desc": "Login URL for OpenShift where Quay will be installed/managed"},
                        "openshift_username": {"type": "string", "desc": "OpenShift cluster admin username"},
                        "openshift_password": {"type": "string", "desc": "OpenShift cluster admin password"},
                        "openshift_yaml_dir": {"type": "string", "desc": "Full path to the directory with YAMLs to be applied to the OpenShift cluster"},
                        }
        
        quay_super_users = {
                        "quay_secret_options": {"type": "list", "desc": "A list of super users that should exist in the OpenShift Secret"}
                        }
        # End Options
        #################

        if args:                
            # If the arg parser arguments have been passed in we are going to try and map the passed in arguments
            # to their required config.yaml entries.
            # The first line in each try, just checks to see if the value is defined
            # if it is, and it's set to true, then set the required options
            try:
                # if auto_discovery is either true or false, assume we are doing a quay sync
                # This argument is not present in the quay_management_tasks.py so this should
                # only action if a sync is called
                args.auto_discovery
                # Quay username/pass are used for podman pull/tag/push
                # The token is used for the API... they can be different
                add_these_options = [sync_generic_options.copy()]
                expected_config_values = build_dict(add_these_options=add_these_options, incoming_dict=expected_config_values)
            except: 
                pass
            
            try:
                args.add_admin_org
                if args.add_admin_org:
                    try:
                        if args.secondary_quay_config:
                            server_type = "secondary"
                    except: 
                        server_type = "primary"
                    add_these_options = [{"quay_admin_org": all_options["quay_admin_org"]}]
                    for key in sync_generic_options:
                        # Only want the secondary related variables from the config.yaml
                        if server_type in key:
                            add_these_options.append({key: sync_generic_options[key]})
                    expected_config_values = build_dict(add_these_options=add_these_options, incoming_dict=expected_config_values)
            except:
                pass
            try:
                args.add_proxycache
                if args.add_proxycache:
                    add_these_options = [sync_generic_options.copy()]
                    add_these_options.append({"proxycache": all_options["proxycache"]})
                    expected_config_values = build_dict(add_these_options=add_these_options, incoming_dict=expected_config_values)
            except:
                pass
            try:
                args.add_robot_account
                if args.add_robot_account:
                    add_these_options = [sync_generic_options.copy()]
                    add_these_options.append({"robot_config": all_options["robot_config"]})
                    expected_config_values = build_dict(add_these_options=add_these_options, incoming_dict=expected_config_values)
            except:
                pass
            try:
                args.add_super_user
                if args.add_super_user:
                    add_these_options = [openshift_options.copy()]
                    add_these_options.append(quay_super_users)
                    expected_config_values = build_dict(add_these_options=add_these_options, incoming_dict=expected_config_values)
            except:
                pass
            try:
                args.configure_secondary_quay_server
                if args.configure_secondary_quay_server:
                    add_these_options = [all_options.copy()]
                    remove_these = ["primary_init_token", "secondary_init_token", "robot_config", "repositories", "proxycache", "initialize_username", "initialize_password", "initialize_email"]
                    for item in remove_these:
                        add_these_options[0].pop(item, None)
                    expected_config_values = build_dict(add_these_options=add_these_options, incoming_dict=expected_config_values)
            except:
                pass
            try:
                args.initialize_user
                if args.initialize_user:
                    add_these_options = [openshift_options.copy()]
                    token_name = "primary_init_token"
                    quay_user = "primary_quay_user"
                    quay_password = "primary_quay_password"
                    if args.configure_secondary_quay_server:
                        token_name = "secondary_init_token"
                        quay_user = "secondary_quay_user"
                        quay_password = "secondary_quay_password"
                    new_items = [{"initialize_username": all_options["initialize_username"]},
                                {"initialize_password": all_options["initialize_password"]},
                                {"initialize_email": all_options["initialize_email"]},
                                {token_name: all_options[token_name]},
                    ]
                    for item in new_items:
                        add_these_options.append(item)
                    expected_config_values = build_dict(add_these_options=add_these_options, incoming_dict=expected_config_values)
            except:
                pass
            try:
                args.initialize_oauth
                if args.initialize_oauth:
                    add_these_options = [openshift_options.copy()]
                    add_these_options.append({"quay_admin_org": all_options["quay_admin_org"]})
                    expected_config_values = build_dict(add_these_options=add_these_options, incoming_dict=expected_config_values)
            except:
                pass
            try:
                args.manage_orgs
                if args.manage_orgs:
                    try:
                        args.secondary_quay_config
                        server_type = "secondary_server"
                    except: 
                        server_type = "primary_server"
                    add_these_options = [{"organizations": all_options["organizations"]}]
                    for key in sync_generic_options:
                        # Only want the secondary related variables from the config.yaml
                        if server_type in key:
                            add_these_options.append({key: sync_generic_options[key]})
                    expected_config_values = build_dict(add_these_options=add_these_options, incoming_dict=expected_config_values)
            except:
                pass
            try:
                args.setup_quay_openshift
                if args.setup_quay_openshift:
                    add_these_options = [openshift_options.copy()]
                    expected_config_values = build_dict(add_these_options=add_these_options, incoming_dict=expected_config_values)
            except:
                pass
        
        # Catch all of the errors as a list of keys
        errors = []
        for options in expected_config_values:
            try:
                # Attempt to creaate self.{key} names as variables on the class
                setattr(self, options, self.config[options])
            except Exception as e:
                errors.append(e.args[0])
        # If there are errors, loop over any keys that we could not parse and print their
        # options to the screen
        if errors:
            errors.sort()
            for key in errors:
                print(f"""{key}:
                        type: {expected_config_values[key]['type']}
                        description: {expected_config_values[key]['desc']}\n"""
                        )
            exit(1)

    @staticmethod
    def add_to_config(config_path: str = None, insert_dict: dict = None):
        """
        Description:
            Updates the config.yaml for the quay activities in this repo. 
            Does NOT update the Quay config that dictates how Quay behaves
        Args:
            config_path (str, optional): The full path to the sample_config.yaml
            insert_dict (dict, optional): The data to insert into the sample_config.yaml. Right now 
                                        it is assumed you need to write a dict into the
        """
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
f"VALUES ('{str(uuid4())}', {app_id}, {user_id}, 'org:admin repo:admin repo:create repo:read repo:write super:user user:admin user:read', " +
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
    def yaml_file_list(file_directory: str) -> list:
        """
        Description:
            Walks the file system of a given toplevel directory to find all files there. Appends a full path to each file
        Args:
            file_directory (str): The path to the directory with the yaml files to apply to the OpenShift cluster
        Returns:
            (list): A list for files with their full paths
        """
        files_list = []
        for root, dirs, files in os.walk(file_directory):
            for file in files:
                if root:
                    full_file_path = os.path.join(root, file)
                    if full_file_path not in files_list:
                        files_list.append(full_file_path)
        files_list.sort()
        return(files_list)
    