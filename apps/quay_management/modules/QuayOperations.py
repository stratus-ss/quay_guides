from .BaseOperations import BaseOperations
import subprocess
import logging
from .QuayAPI import QuayAPI
from random import SystemRandom as Random

class ImageMover(BaseOperations):

    def login_to_quay(self, server: str, username: str, password: str, args=None) -> None:
        """
        Description: 
            Logs in to Quay on the specified server.
        Args:
            server: The server to log in to.
            username: The Quay username.
            password: The Quay password.
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
    def podman_operations(cls, operation, image_source=None, image_destination=None, image_and_tag=None, args=None):
        """
        Description: 
            Performs a Podman operation on an image.
        Args:
            operation (str): The Podman operation to perform (e.g., "tag", "push", "pull").
            image_source (str): The source image for the operation.
            image_destination (str): The destination image for the operation.
            image_and_tag (str): The image and tag to use for the operation.
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
        
    def add_robot_acct(self, robot_exists: dict = None, username: str = None, quay_api_object: object = None):
        """
        Description:
            Add a new robot account to the quay configuration.
        Args:
            robot_exists: A dictionary containing information about existing robots.
            username: The username of the robot to add.
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
            key: The key to look up in the quay_config dictionary.
        Returns:
            A dictionary containing information about the robot account.
        """
        return QuayAPI(base_url=self.quay_url, api_token=api_token, robot_acct=self.quay_config.robot_config[key])

    
