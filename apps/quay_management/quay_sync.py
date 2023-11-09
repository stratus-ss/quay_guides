#!/usr/bin/env python
import yaml
import subprocess
import logging
import socket
import argparse
import requests
import time
import json
from modules.BaseOperations import BaseOperations
from modules.PreflightChecker import PreflightChecker
from modules.QuayAPI import QuayAPI
from modules.QuayOperations import ImageMover

logging.basicConfig(level=logging.INFO)
parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('--username', help='Quay Username')
parser.add_argument('--password', help='Quay Password')
parser.add_argument('--config-file', help="The full path to the config file", required=True)
parser.add_argument("--skip-tls-verify", action="store_true", help="Ignore self signed certs on registries")
parser.add_argument("--skip-broken-images", action="store_true", help="Don't stop because of broken image pull/push")
parser.add_argument("--auto-discovery", action="store_true", help="Attempt to auto discover any repositories present in organizations")

args = parser.parse_args()

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
    
