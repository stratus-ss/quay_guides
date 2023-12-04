from .BaseOperations import BaseOperations
import subprocess
import logging
from .QuayAPI import QuayAPI
from random import SystemRandom as Random
import yaml
import base64
from typing import Union

class ImageMover(BaseOperations):

    def login_to_quay(self, server: str, username: str, password: str, args=None) -> None:
        """
        Description: 
            Logs in to Quay on the specified server.
        Args:
            server: The server to log in to.
            username: The Quay username.
            password: The Quay password.
            args: An instance of arg parse so we know what options we are dealing with
        Returns:
            None
        """

        try:
            podman_login_command = [
                "podman",
                "login",
                f"-u={username}",
                f"-p={password}",
                server,
            ]
            podman_login_command = BaseOperations.do_i_skip_tls(podman_login_command, skip_tls_verify=args.skip_tls_verify)
            subprocess.check_output(podman_login_command)
        except subprocess.CalledProcessError as e:
            logging.critical("--> Error logging in to Quay:")
            exit(1)
        logging.info(f"Logged in to: {server}")
 
    @classmethod
    def podman_operations(cls, operation: str, image_source: str=None, image_destination: str=None, image_and_tag: str=None, args=None):
        """
        Description: 
            Performs a Podman operation on an image.
        Args:
            operation (str): The Podman operation to perform (e.g., "tag", "push", "pull").
            image_source (str): The source image for the operation.
            image_destination (str): The destination image for the operation.
            image_and_tag (str): The image and tag to use for the operation.
            args: An instance of arg parse so we know what options we are dealing with
        Returns:
            None
        """
        if image_source:
            if "//" in image_source:
                # If there is http:// or https:// we need to strip that because this is illegal for images
                image_source = image_source.split("//")[1:][0]
        if image_destination:
            if "//" in image_destination:
                # If there is http:// or https:// we need to strip that because this is illegal for images
                image_destination = image_destination.split("//")[1:][0]
            
        if operation == "tag":
            podman_command = ["podman", operation, image_source, image_destination]
            log_msg = f"Image tagged: {image_destination} <---"
        elif operation == "push":
            podman_command = ["podman", operation, image_source, image_destination]
            podman_command = cls.do_i_skip_tls(podman_command, skip_tls_verify=args.skip_tls_verify)
            log_msg = f"Image pushed from {image_source} to {image_destination} <---"
        elif operation == "pull":
            podman_command = ["podman", operation, image_source]
            podman_command = cls.do_i_skip_tls(podman_command, skip_tls_verify=args.skip_tls_verify)
            log_msg = f"Image pulled from {image_source} <---"
        try:        
            subprocess.check_output(podman_command)
            logging.info(log_msg) 
        except subprocess.CalledProcessError as e:
            if operation == "push":
                subprocess.check_output(podman_command)
            logging.critical(
                f"Error while attempting to {operation} the image: {image_and_tag} <---"
            )
            if not args.skip_broken_images:
                exit(1)

class QuayManagement():
    def __init__(self, quay_url: str = None, quay_config: dict = None) -> None:
        """
        Description:
            Initialize a QuayManagement object.
        Args:
            quay_url: The URL of the Quay API to use.
            quay_config: A dictionary containing configuration information for the Quay API.
        """
        self.quay_url = quay_url
        self.quay_config = quay_config
 
    def add_proxycache(self, quay_api: QuayAPI, overwrite: bool = False):
        """
        Descirption:
            Add a proxy cache to the quay configuration.
        Args:
            source_quay_api: The Quay API object to use.
            overwrite: Whether or not to overwrite existing proxy caches (default is False).
        """
        for key in self.quay_config.proxycache:
            proxy_data = self.quay_config.proxycache[key]
            # Since there can only be a single proxycache definition per org, go through and delete the proxycache first if it exists
            proxy_info = quay_api.get_proxycache(org_name=proxy_data["org_name"])
            if proxy_info is not None:
                if overwrite:
                    logging.info(f" existing proxycache found in the organization ----> {proxy_data['org_name']} <----")
                    logging.info(f" --overwrite-proxycache option found... deleting existing proxycache config for ----> {proxy_info['upstream_registry']} <----")
                    quay_api.delete_proxycache(org_name=proxy_data["org_name"])
                else:
                    logging.warning("Proxy cache already exists and --overwrite-proxycache was not used")
                    logging.warning("NOT deleting existing proxycache")
                    break
            
            logging.info(f"Creating the proxy cache for ---> {proxy_data['upstream_registry']} <--- in the organization ---> {proxy_data['org_name']} <---")
            quay_api.create_proxycache(org_name=proxy_data["org_name"], json_data=proxy_data)       
        
    def add_robot_acct(self, robot_exists: dict = None, username: str = None, quay_api_object: QuayAPI = None):
        """
        Description:
            Add a new robot account to the quay configuration.
        Args:
            robot_exists: A dictionary containing information about existing robots.
            username: The username of the robot to add.
            quay_api_object: An instantiation of the QuayAPI object likely done with QuayAPI(base_url=quay_url, api_token=quay_api_token)
        """
        for key in self.quay_config.robot_config:
            robot_api = self.parse_robot_acct_info(key, api_token=quay_api_object.api_token)
            if robot_api.robot_acct['type'] == 'personal':
                robot_name = f"{username}+{robot_api.robot_acct['name']}"
            else:
                robot_name = f"{robot_api.robot_acct['org_name']}+{robot_api.robot_acct['name']}"
            if robot_exists[robot_name]:
                logging.info(f"The robot account {robot_name} already exists")
            else:
                if username:
                    robot_api.create_robot_acct()
          
    def delete_robot(self):
        """
        Description:
            Delete all robot accounts from the quay configuration.
        """
        for key in self.quay_config.robot_config:
            robot_api = self.parse_robot_acct_info(key)
            QuayAPI.delete_robot_acct()
            
    def get_robot(self, username: str = None) -> dict:
        """
        Description:
            Get information about all existing robots in the quay configuration.
        Args:
            username: The username of the robot to look up (optional).
        Returns:
            A dictionary containing information about each robot account.
        """
        existing_robot_dict = {}
        for key in self.quay_config.robot_config:
            robot_api = self.parse_robot_acct_info(key)
            robot_exists = robot_api.get_robot_acct()
            if robot_exists:
                # The quay api creates a robot account with <org>+<name> so to store the name correctly, we need to use the object returned from the API
                existing_robot_dict[(robot_exists['name'])] = True
            else:
                if robot_api.robot_acct['type'] == 'org':
                    robot_name = f"{robot_api.robot_acct['org_name']}+{robot_api.robot_acct['name']}"
                elif robot_api.robot_acct['type'] == 'personal':
                    # There is no robot object returning from the API so 
                    if username is not None:
                        robot_name = f"{username}+{robot_api.robot_acct['name']}"
                else:
                    robot_name = robot_api.robot_acct['name']
                existing_robot_dict[robot_name] = False
        return(existing_robot_dict)
            
    def parse_robot_acct_info(self, key: str, api_token: str = None) -> dict:
        """
        Description:
            Parse robot account information for a given key in the quay_config dictionary.
        Args:
            key (str): The key to look up in the quay_config dictionary.
            api_token (str): The api token to use for Quay api calls 
        Returns:
            A dictionary containing information about the robot account.
        """
        return QuayAPI(base_url=self.quay_url, api_token=api_token, robot_acct=self.quay_config.robot_config[key])

    @staticmethod
    def process_quay_secret(quay_init_secret: dict = None, quay_config: BaseOperations = None, quay_secret_section: str = "SUPER_USERS") -> dict:
        """
        Description: This staticmethod takes in a secret file yaml assuming the data section has already been base64 encoded.
                    The quay secret should be in a section called "config.yaml". Decodes the config.yaml, modifies it and returns
                    the result of the modified file. The intent is to write this out to disk so that `oc create ... |oc replace` 
                    can be used to recreate the secret in place
        Args:
            quay_init_secret (dict, optional): The entire yaml file as a dict object. 
            quay_config (dict, optional): An instantiation of the BaseOperations likely created like this: BaseOperations(args.config_file, args=args)
            quay_secret_section (str, optional): The section of the config.yaml that should be edited. Defaults to "SUPER_USERS".

        Returns:
            dict: Returns the full quay config.yaml file so it can be used in another process
        """
        quay_init_secret_decoded = yaml.load(base64.b64decode(quay_init_secret['data']['config.yaml']), Loader=yaml.FullLoader)
        if quay_secret_section == "SUPER_USERS":
            for user in quay_config.quay_secret_options['super_users']:
                if user in quay_init_secret_decoded[quay_secret_section]:
                    logging.info(f"User {user} was already in the Quay SUPER_USERS secret... skipping")
                else:
                    quay_init_secret_decoded[quay_secret_section].append(user)
            return(quay_init_secret_decoded)
     
    @staticmethod
    def take_org_ownership(orgs: dict = None, quay_server_api: QuayAPI = None, quay_username: Union[str,list[str]] = "quayadmin") -> None:
        """
        Description: This staticmethod checks each of the organizations in quay. By default there is
                    a "owners" team on each org. If the {quay_username} is not in the owners team, it is added.
        Args:
            orgs (dict, optional): A dict with organization attributes probably generated from quay_server_api.get_org(). Defaults to None.
            quay_server_api (QuayAPI, optional): An instantiation of the QuayAPI class probably done with 
                                                QuayAPI(base_url=quay_url, api_token=quay_api_token). Defaults to None.
            quay_username (str or list, optional): A username (or list of usernames) which you want to ensure is the owner of all orgs. 
                                                Defaults to quayadmin.
        """
        
        def is_not_member(user, members):
            for member in members:
                if member['name'] == user:
                    return False
            return True
        
        if isinstance(quay_username, str):
            quay_username = [quay_username]
        for org in orgs['organizations']:
            # Start by assuming we are not the owner of the org
            members = quay_server_api.get_org_members(org['name'])
            for user in quay_username:
                if is_not_member(user, members):
                    logging.info(f"Adding {user} as an owner of --> {org['name']} <--")
                    quay_server_api.create_org_member(org_name=org['name'], new_member=user, team_name="owners")
                else:
                    logging.info(f"{user} is already an owner of {org['name']}")
            # for member in members['members']:
            #     for user in quay_username:
            #         if user == member['name']:
            #             not_org_owner = True
            #             for team in member['teams']:
            #                 # Make sure that if the user is an owner we set the flag to false
            #                 if team['name'] == "owners":
            #                     not_org_owner = False
            #                     break
            #             if not_org_owner:
            #                 logging.info(f"Adding {member['name']} as an owner of --> {org['name']} <--")
            #                 quay_server_api.create_org_member(org_name=org['name'], new_member=member['name'], team_name="owners")
            #             else:
            #                 logging.info(f"{member['name']} is already an owner of {org['name']}")
            