import logging
import requests
import json 
class QuayAPI:
    def __init__(self, base_url: str = None, api_token: str = None, robot_acct: dict = None) -> None:
        """
        Description: 
            Initialize a new instance of the QuayAPI class.
        Args:
            base_url (str, optional): The base URL of the Quay API. Defaults to None.
            api_token (str, optional): The API token for authentication. Defaults to None.
            robot_user (str, optional): Whether the robot account should be part of an org or attached to a user
        Returns:
            None
        """
        self.api_token = api_token
        self.base_url = base_url
        self.repo_endpoint = f"{self.base_url}/api/v1/find/repositories"
        self.org_endpoint = "/api/v1/organization/"
        self.org_member_list_endpoint = f"{self.org_endpoint}/<org>/members"
        self.org_list_endpoint = "/api/v1/superuser/organizations/"
        self.org_member_add_endpoint = "/api/v1/organization/<org>/team/<team_name>/members/<new_member>"
        # The <org> is a placeholder so that it can be replaced as needed
        self.proxycache_url = f"{self.base_url}/api/v1/organization/<org>/proxycache"
        self.initialize_url = f"{self.base_url}/api/v1/user/initialize"
        self.headers = {'Authorization': f'Bearer {self.api_token}'}
        self.admin_application_name = "quaysync"
        self.oauth_application_url = (
            f"{self.base_url}/api/v1/organization/<org>/applications"
        )
        if isinstance(robot_acct, dict):     
                try:
                    if robot_acct["type"] == "org":
                        robot_url = f"{self.base_url}/api/v1/organization/{robot_acct['org_name']}/robots/{robot_acct['name']}"
                    elif robot_acct["type"] == "personal":
                        robot_url = f"{self.base_url}/api/v1/user/robots/{robot_acct['name']}"
                    robot_acct['url'] = robot_url
                except:
                    logging.error("Invalid input for robot account")
        elif robot_acct is None:
            # If robot_acct is None, assume we are not creating a robot account
            robot_url = ""
        else:
            robot_url = ""
            logging.error(f"Expected robot acct to be a dict... got {type(robot_acct)}")

        self.robot_acct = robot_acct


    def assemble_org_url(self, org_name: str = None, url_to_replace: str = None) -> str:
        """
        Description: 
            Assembles the proxycache URL, basic find/replace function
        Args:
            org_name (str, optional): Name of the organization where proxycache is to reside. Defaults to None.

        Returns:
            str: A full url to the proxycache endpoint
        """

        url = url_to_replace.replace("<org>", org_name)
        return url

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
    
    def create_proxycache(self, org_name: str = None, json_data: dict = None) -> None:
        """
        Description: 
            Uses the QuayAPI to create a proxycache setting under a specific organization
        Args:
            org_name (str, optional): Name of the organization where proxycache is to reside. Defaults to None.
            json_data (dict, optional): A JSON object describing the proxycache configuration. Defaults to None.
        """
        url = self.assemble_org_url(org_name=org_name, url_to_replace=self.proxycache_url)
        proxy_create_response = self.post_data(url=url, data=json_data)
        if proxy_create_response.status_code != 201:
            logging.warning("----> Failed to create proxy cache")
            cleaned_text = json.loads(proxy_create_response.text)
            logging.warning(cleaned_text)
            logging.warning(f'Status code: {proxy_create_response.status_code}')

    def create_robot_acct(self):
        """
        Description:
            Creates a robot account in quay
        """
        data= f"{self.robot_acct}"
        logging.info(f"Creating robot account {self.robot_acct}")
        response = self.put_data(url=self.robot_acct['url'])
        return(response)

    def create_oauth_application(self, org_name: str = None, application_name: str = None):
        """
        Description:
            Quay ties an oauth token to an application. Creates the base application in Quay
        Args:
            org_name (str, optional): Which organization the oauth application should be tied to. Defaults to None.
            application_name (str, optional): A name given to identify the oauth token. Defaults to None.
        """
        url = self.assemble_org_url(org_name=org_name, url_to_replace=self.oauth_application_url)
        data = {"name": application_name}
        response = self.post_data(url=url, data=data)
        return(response)

    def create_org(self, org_name: str = None, override_headers: bool = False, additional_api_key: str = None):
        """
        Description: 
            Create a new organization on Quay.
        Args:
            org_name (str): The name of the organization to create.
        Returns:
            bool: True if the organization was created successfully, False otherwise.
        """
        data = {
            'name': org_name
        }
        if override_headers:
            headers = {'Authorization': f'Bearer {additional_api_key}'}
        else:
            headers = self.headers
        logging.info(f"Attempting to create organization: {org_name}")
        url = f'{self.base_url}{self.org_endpoint}'
        response = self.post_data(url=url, headers=headers, data=data)
        if response.status_code == 201:
            logging.info(f"Organization created successfully: {org_name}")
            return
        else:
            logging.critical("Error creating organization")
            logging.debug(response.text)
            return False

    def create_org_member(self, org_name: str = None, new_member: str = None, team_name: str = None) -> dict:
        """
        Description:
            Adds a user as a member of a specific team
        Args:
            org_name (str, optional): The name of the orgnaization where the new membership should reside
            new_member (str, optional): The name of the user to add a membership for
            team_name (str, optional): The name of the team to add the user to
        Returns:
            (dict): The API response as a dict
        """
        url = f'{self.base_url}{self.org_member_add_endpoint}'
        url = self.assemble_org_url(org_name=org_name, url_to_replace=url)
        url = url.replace("<team_name>", team_name)
        url = url.replace("<new_member>", new_member)
        response = self.put_data(url=url)
        return(response)
        
    def create_initial_user(self, user_info: dict = None) -> dict:
        """
        Description:
            Uses the Quay initialize endpoint to create the first user in Quay
        Args:
            user_info (dict, optional): JSON object containing the data required to initialize the user. Defaults to None.
                                        {"username"}

        Returns:
            dict: Response object from the API
        """
        response = self.post_data(url=self.initialize_url, data=user_info, headers_required=False)
        return response

    def delete_org(self, org_name: str = None, override_headers: bool = False, additional_api_key: str = None):
        """
        Description: 
            Deletes an organization on Quay.
        Args:
            org_name (str): The name of the organization to delete.
        Returns:
            bool: True if the organization was deleted successfully, False otherwise.
        """
        data = {
            'name': org_name
        }
        if override_headers:
            headers = {'Authorization': f'Bearer {additional_api_key}'}
        else:
            headers = self.headers
        logging.info(f"Attempting to delete organization: {org_name}")
        url = f'{self.base_url}{self.org_endpoint}'
        response = self.delete_data(data=data, url=url, headers=headers)
        if response.status_code == 201:
            logging.info(f"Organization deleted successfully: {org_name}")
            return
        else:
            logging.critical("Error delete organization")
            logging.debug(response.text)
            return False


    def delete_robot_acct(self):
        """
        Description:
            Deletes a robot account if it exists
        """
        logging.info(f"Deleting robot account {self.robot_acct['name']}")
        self.delete_data(url=self.robot_url)

    def delete_data(self, data: dict = None, url: str = None, headers_required=True, headers: str = None) -> dict:
        """
        Description:
            Deletes data from a specified URL using the requests library.
        Args:
            data (dict): The data to be deleted.
            url (str): The URL to delete the data from.
            headers_required (bool): Whether or not headers are required for the request.
        Returns:
            dict: The response from the server.
        """
        if not headers:
            headers = self.headers
        if headers_required:
            return(requests.delete(f'{url}', headers=headers, json=data))
        else:
            return(requests.delete(f'{url}', json=data))

    def delete_proxycache(self, org_name: str = None):
        """
        Description:
            Deletes the proxycache configuration from the specified Quay organization
        Args:
            org_name (str, optional): The organization where the proxycache config resides. Defaults to None.
        """
        url = self.assemble_org_url(org_name=org_name, url_to_replace=self.proxycache_url)
        proxy_delete_response = self.delete_data(url=url)
        if proxy_delete_response.status_code != 201:
            logging.warning("----> Failed to delete proxy cache")
            cleaned_text = json.loads(proxy_delete_response.text)
            logging.warning(cleaned_text['detail'])
            logging.warning(f'Status code: {proxy_delete_response.status_code}')

    def get_oauth_client_id(self, admin_org_name: str = None, override_headers: bool = False, additional_api_key: str = None) -> str:
        """
        Description:
            Get the OAuth client ID for the specified admin organization.
        Args:
            admin_org_name (str, optional): The name of the admin organization.
            override_headers (bool, optional):  Whether to override the headers. Defaults to False.
            additional_api_key (str, optional): An additional API key. Defaults to None.

        Returns:
            str: The OAuth client ID
        """
        client_id_endpoint = self.base_url + self.org_endpoint + admin_org_name + "/applications"
        current_applications = self.get_data(client_id_endpoint, override_headers=override_headers, additional_api_key=additional_api_key)
        if current_applications is None:
            return
        create_app_required = True
        client_id = None
        for current_app in current_applications["applications"]:
            if self.admin_application_name in current_app['name']:
                create_app_required = False
                client_id = current_app['client_id']
                logging.info("Application name already found... retreiving ID...")
        if create_app_required:
            data = {"name": self.admin_application_name, "description": "test-app"}
            response = self.post_data(url=client_id_endpoint, data=data)
            response_dict = json.loads(response.content)
            client_id = response_dict['client_id']
        return client_id

    def get_data(self, url: str = None, override_headers: bool = False, additional_api_key: str = None) -> dict:
        """
        Description: 
            Fetches data from the Quay API.
        Args:
            url (str): The URL to fetch data from. If not specified, uses the default Quay repository URI.
        Returns:
            dict: A dictionary containing the JSON response from the API.
        """
        if url is None:
            url = self.repo_endpoint
        if override_headers:
            headers = {'Authorization': f'Bearer {additional_api_key}'}
        else:
            headers = self.headers
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
        working_url = f"{self.base_url}/api/v1{href}/tag"
        tag_info = self.get_data(url=working_url)
        tag_list = []
        for tag in tag_info['tags']:
            tag_list.append(tag['name'])
        return tag_list
    
    def get_org(self, override_headers: bool = False, additional_api_key: str = None) -> dict:
        """
        Description:
            Gets a list of all the organizations in Quay
        Args:
            override_headers (bool, optional): There may be cases where you need to override the headers
                                                because you want to use a different API key.
            additional_api_key (str, optional): If you need to change the API key for some reason
                                                use this key instead
        Returns:
            (dict): Returns the API response as a dict
        """
        if override_headers:
            headers = {'Authorization': f'Bearer {additional_api_key}'}
        else:
            headers = self.headers
        url = f'{self.base_url}{self.org_list_endpoint}'
        return self.get_data(url=url)
    
    def get_org_members(self, org_name: str = None) -> dict:
        """
        Description:
            Gets the current members of the specified organization
        Args:
            org_name (str, optional): The name of the Quay organization to get a member list from. 
        Returns:
            (dict): The response object from the API
        """
        url = f'{self.base_url}{self.org_member_list_endpoint}'
        url = self.assemble_org_url(org_name=org_name, url_to_replace=url)
        return self.get_data(url=url)
        
        
    def get_proxycache(self, org_name: str = None) -> dict:
        """
        Description:
            Retrieves proxycache information from the API
        Args:
            org_name (str, optional): The organization in which the proxycache information resides. Defaults to None.

        Returns:
            dict: The response data from the API
        """
        
        url = self.assemble_org_url(org_name=org_name, url_to_replace=self.proxycache_url)
        proxy_cache_info = self.get_data(url=url)
        if not proxy_cache_info:
            return None
        return proxy_cache_info

    def get_robot_acct(self) -> dict:
        """
        Description:
            Retrieves the robot account from the url specified
        Returns:
            dict: Response JSON from the API
        """
        response = self.get_data(url=self.robot_acct['url'])
        logging.info(f"Retrieving robot account {self.robot_acct['name']}")
        return(response)

    def post_data(self, data: dict = None, url: str = None, headers_required=True, headers: str = None ) -> dict:
        """
        Description: 
            Posts data to a specified URL using the requests library.
        Args:
            data (dict): The data to be posted.
            url (str): The URL to post the data to.
            headers_required (bool): Whether or not headers are required for the request.
        Returns:
            dict: The response from the server.
        """
        if not data:
            data = {}
        if not headers:
            headers = self.headers
        if headers_required:
            output = requests.post(f'{url}', headers=headers, json=data)
        else:
            output = requests.post(f'{url}', json=data)
        return(output)
 
    def put_data(self, data: dict = None, url: str = None, headers_required=True ) -> dict:
        """
        Description:
            Uses the PUT method instead of the POST method to interact with the API
        Args:
            data (dict, optional): JSON object to send to the API endpoint. Defaults to None.
            url (str, optional): The API endpoint to put the data. Defaults to None.
            headers_required (bool, optional): In some cases the header might not be required. Defaults to True.

        Returns:
            dict: Returns the response object from the API
        """
        if not data:
            data = {}
        return(requests.put(f'{url}', headers=self.headers, json=data))
