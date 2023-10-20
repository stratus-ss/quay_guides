#!/usr/bin/env python
import yaml
import subprocess
import logging
import socket
import argparse
import requests
import time
import json

logging.basicConfig(level=logging.INFO)
parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('--username', help='Quay Username')
parser.add_argument('--password', help='Quay Password')
parser.add_argument('--config-file', help="The full path to the config file", required=True)
parser.add_argument("--skip-tls-verify", action="store_true", help="Ignore self signed certs on registries")
parser.add_argument("--skip-broken-images", action="store_true", help="Don't stop because of broken image pull/push")
parser.add_argument("--auto-discovery", action="store_true", help="Attempt to auto discover any repositories present in organizations")

args = parser.parse_args()

class BaseOperations:
    def __init__(self, config_file):
        self.config = self.load_config(self, config_file=config_file)
        self.repositories = self.config["repositories"]
        self.source_server = self.config["source_server"]
        self.destination_server = self.config["destination_server"]
        self.failover = self.config["failover"]
        self.destination_token = self.config["destination_token"]
        self.source_token = self.config["source_token"]
    
    @staticmethod
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
    def do_i_skip_tls(cls, command: list[str]) -> list[str]:
        """
        Description: 
            Adds the `--tls-verify=false` flag to the specified command if `args.skip_tls_verify` is True.
        Args:
            command: The command to add the flag to.
        Returns:
            The updated command.
        """

        if args.skip_tls_verify:
            command.append("--tls-verify=false")
        return(command)

class PreflightChecker:
    def __init__(self):
        pass

    def check_dns(self, server: str) -> bool:
        """
        Description: 
            Checks if the specified server can be resolved by DNS.
        Args:
            server: The server to check.
        Returns:
            True if the server can be resolved, False otherwise.
        """

        try:
            ip_address = socket.gethostbyname(server)
            logging.info(f"{server} resolves to --> {ip_address} <--")
            return True
        except socket.gaierror:
            logging.critical(f"--> DNS lookup failed for host {server} <----")
            exit(1)

    def check_port(self, server: str) -> bool:
        """
        Description:
            Checks if the specified server is listening on the specified port.
        Args:
            server: The server to check.
            port: The port to check.
        Returns:
            True if the server is listening on the specified port, False otherwise.
        """

        quay_port = 443
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((server, quay_port))
            logging.info(f"{server} is listening on port {quay_port}")
            return True
        except ConnectionRefusedError:
            logging.critical("%s refused the connection on port %s" % quay_port)
            exit(1)


class ImageMover(BaseOperations):

    def login_to_quay(self, server: str, username: str, password: str) -> None:
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
            podman_login_command = self.do_i_skip_tls(podman_login_command)
            subprocess.check_output(podman_login_command)
        except subprocess.CalledProcessError as e:
            logging.critical("--> Error logging in to Quay:")
            exit(1)
        logging.info(f"Logged in to: {server}")
 
    @classmethod
    def podman_operations(cls, operation, image_source=None, image_destination=None, image_and_tag=None):
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
        if operation == "tag":
            podman_command = ["podman", operation, image_source, image_destination]
            log_msg = f"Image tagged: {image_destination} <---"
        elif operation == "push":
            podman_command = ["podman", operation, image_source, image_destination]
            podman_command = cls.do_i_skip_tls(podman_command)
            log_msg = f"Image pushed from {image_source} to {image_destination} <---"
        elif operation == "pull":
            podman_command = ["podman", operation, image_source]
            podman_command = cls.do_i_skip_tls(podman_command)
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

class QuayAPI:
    def __init__(self, base_url: str = None, api_token: str = None) -> None:
        """
        Description: 
            Initialize a new instance of the QuayAPI class.
        Args:
            base_url (str, optional): The base URL of the Quay API. Defaults to None.
            api_token (str, optional): The API token for authentication. Defaults to None.
        Returns:
            None
        """

        self.api_token = api_token
        self.base_url = base_url
        self.repo_endpoint="api/v1/find/repositories"
        self.org_endpoint = "api/v1/organization/"
        self.quay_repo_uri = self.base_url + self.repo_endpoint

    def check_if_object_exists(self, repo_name: str = None, org_name: str = None) -> bool:
        """
        Description: 
            Check if an object (repository or organization) exists in a GitHub repository.
        Args:
            repo_name (str, optional): The name of the repository to check. Defaults to None.
            org_name (str, optional): The name of the organization to check. Defaults to None.
        Returns:
            bool: True if the object exists, False otherwise.
        """
        # If both repo_name and org_name are None, raise a ValueError
        if not repo_name and not org_name:
            raise ValueError("Either repo_name or org_name must be provided.")

        # Set the endpoint and object_type based on whether org_name is set
        if org_name:
            endpoint = self.org_endpoint + org_name
            object_type = "organization"
        else:
            endpoint = f"api/v1/repository/{org_name}/{repo_name}"
            object_type = "repository"

        working_url = f'{self.base_url}{endpoint}'
        search_for_object = self.get_data(url=working_url)
        if search_for_object is None:
            return True

        try:
            if search_for_object['name'] == org_name:
                logging.info(f"Organization already exists in destination: {org_name} <---\n")
                return False
        except:
            logging.error(f"Error getting {object_type} from {working_url}")
            return True
        
        if search_for_object.get('error_type') is None:
            logging.info(f"{object_type} exists")
            return(False)
        else:
            logging.error(f"error getting {object_type}: ")
            return(True)


    def create_org(self, org_name):
        """
        Description: 
            Create a new organization on Quay.
        Args:
            org_name (str): The name of the organization to create.
        Returns:
            bool: True if the organization was created successfully, False otherwise.
        """
        headers = {'Authorization': f'Bearer {self.api_token}'}
        data = {
            'name': org_name
        }
        logging.info(f"Attempting to create organization: {org_name}")
        response = requests.post(f'{self.base_url}{self.org_endpoint}', headers=headers, json=data)
        if response.status_code == 201:
            logging.info(f"Organization created successfully: {org_name}")
            return
        else:
            logging.critical("Error creating organization")
            logging.debug(response.text)
            return False

    def get_data(self, url: str = None) -> dict:
        """
        Description: 
            Fetches data from the Quay API.
        Args:
            url (str): The URL to fetch data from. If not specified, uses the default Quay repository URI.
        Returns:
            dict: A dictionary containing the JSON response from the API.
        """
        if url is None:
            url = self.quay_repo_uri
        headers = {'Authorization': f'Bearer {self.api_token}'}
        response = requests.get(f'{url}', headers=headers)
        # Check the response status code
        if response.status_code != 200:
            logging.error("Error getting data from %s: %s", url, response.status_code)
            return None
        elif response.content:
            output = json.loads(response.content)
            if "results" in output:
                if not bool(output["results"]):
                    logging.critical("Problem getting information from the API... Check that your API key is correct")
                    exit(1)

        try:
            return response.json()
        except:
            return None
        
    def get_tag_info(self, href: str) -> list:
        """
        Description: 
            Gets information about tags in a Quay repository.
        Args:
            href (str): The href of the repository to fetch tag information for.
        Returns:
            list: A list of dictionaries, each representing a tag in the repository.
        """
        working_url = f"{self.base_url}api/v1{href}/tag"
        tag_info = self.get_data(url=working_url)
        return [tag['name'] for tag in tag_info['tags']]

if __name__ == "__main__":
    def add_key(dictionary, key, value):
        for k, v in dictionary.items():
            if isinstance(v, dict):
                add_key(v, key)
            else:
                v[key] = None
    quay_config = BaseOperations(args.config_file)
    mover= ImageMover(args.config_file)
    preflight = PreflightChecker()

    if not quay_config.failover:
        source_server = quay_config.source_server
        destination_server = quay_config.destination_server
    else:
        source_server = quay_config.destination_server
        destination_server = quay_config.source_server

    try:
        preflight.check_dns(source_server)
        preflight.check_dns(destination_server)
        preflight.check_port(source_server)
        preflight.check_port(destination_server)
        print()
        mover.login_to_quay(source_server, args.username, args.password)
        mover.login_to_quay(destination_server, args.username, args.password)
        print("")
    except Exception as e:
        logging.error("Error executing script: {}".format(e))
        exit(1)

    # Set the base URL for the destination server
    destination_url = "https://%s/" % destination_server

    # Set the base URL for the source server
    source_url = "https://%s/" % source_server

    # Create an instance of QuayAPI for the source server
    source_quay_api = QuayAPI(base_url=source_url, api_token=quay_config.source_token)

    # Create an instance of the QuayAPI class for the destination server
    destination_quay_api = QuayAPI(base_url=destination_url, api_token=quay_config.destination_token)

    # Call the functions and pass in the token as an argument
    source_data = source_quay_api.get_data()

    # Initialize variables
    index = 0
    source_orgs = []
    source_repositories = []
    orgs_to_be_created = []

    # Loop through the results in the source data
    for result in source_data['results']:
        # Extract the namespace and href from each result
        if source_data['results'][index]['namespace']['name'] not in source_orgs:
            source_orgs.append(source_data['results'][index]['namespace']['name'])
        source_repositories.append(source_data['results'][index]['href'])
        index += 1

    # Loop through the source organizations
    for org in source_orgs:
        # Check if the organization exists on the destination server
        destination_data = source_quay_api.get_data()
        if not destination_data:
            logging.info("Doesn't exist")
            continue
        # Check if the organization needs to be created on the destination server
        create_org = destination_quay_api.check_if_object_exists(org_name=org)
        if create_org:
            logging.info(f"Organization does not exist: {org} <---")
            destination_quay_api.create_org(org)
            time.sleep(3)
    
    if args.auto_discovery:
        # Create a dictionary to store the images and tags
        image_dict = {}

        # Loop through the source repositories
        for repo in source_repositories:
            # Get the list of tags for each repository
            tag_list = source_quay_api.get_tag_info(repo)
            # Loop through the tags and add them to the image_dict
            for tag in tag_list:
                organization = repo.split("/")[-2]
                image_and_tag = repo.split("/")[-1] + ":" + tag

                # If the organization already exists in the image_dict, append the image and tag to the list
                if organization in image_dict:
                    if not image_and_tag in image_dict[organization]:
                        image_dict.setdefault(organization, []).append(image_and_tag)
                # Otherwise, set the default value for the organization key to an empty list and append the image and tag
                else:
                    image_dict.setdefault(organization, []).append(image_and_tag)
        # Loop through the image_dict and print the podman pull commands
        for org in image_dict:
            for repo_and_tag in image_dict[org]:
                source_image_name = source_quay_api.base_url.strip("https://")+ "/" + org + "/" + repo_and_tag
                destination_image_name = destination_quay_api.base_url.strip("https://") + "/" + org + "/" + repo_and_tag
                print("")
                ImageMover.podman_operations(operation="pull", image_source=source_image_name, image_and_tag=repo_and_tag)
                ImageMover.podman_operations(operation="tag", image_source=source_image_name, image_destination=destination_image_name, image_and_tag=repo_and_tag)
                time.sleep(1)
                print("")
                ImageMover.podman_operations(operation="push", image_source=source_image_name, image_destination=destination_image_name, image_and_tag=repo_and_tag)
    else:
        try:
            for repository in quay_config.repositories:
                image_source_name = source_server + "/" + repository
                image_destination_name = destination_server + "/" + repository
                print("")
                ImageMover.podman_operations(operation="pull", image_source=image_source_name, image_and_tag=repository)
                ImageMover.podman_operations(operation="tag", image_source=image_source_name, image_destination=image_destination_name, image_and_tag=repository)
                time.sleep(1)
                print("")
                ImageMover.podman_operations(operation="push", image_source=image_source_name, image_destination=image_destination_name, image_and_tag=repository)
                print("")
        except Exception as e:
            logging.error("Error executing script: {}".format(e))
            exit(1)
    
