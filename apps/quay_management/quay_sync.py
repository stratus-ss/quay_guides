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
parser.add_argument('--config-file', help="The full path to the config file", required=True)
parser.add_argument("--skip-tls-verify", action="store_true", help="Ignore self signed certs on registries")
parser.add_argument("--skip-broken-images", action="store_true", help="Don't stop because of broken image pull/push")
parser.add_argument("--auto-discovery", action="store_true", help="Attempt to auto discover any repositories present in organizations")
parser.add_argument("--failover", action="store_true", help="If set, the primary and secondary servers are flipped so the secondary is assumed live")

args = parser.parse_args()

if __name__ == "__main__":
    def add_key(dictionary, key, value):
        for k, v in dictionary.items():
            if isinstance(v, dict):
                add_key(v, key)
            else:
                v[key] = None
    quay_config = BaseOperations(args.config_file, args=args)
    mover= ImageMover(args.config_file)
    preflight = PreflightChecker()
    primary_server = quay_config.primary_server
    primary_credentials = {"username": quay_config.primary_quay_user, "password": quay_config.primary_quay_password}
    secondary_server = quay_config.secondary_server
    secondary_credentials = {"username": quay_config.secondary_quay_user, "password": quay_config.secondary_quay_password}
    
    # For now, use the Quay User's init token
    primary_api_token = quay_config.primary_init_token
    secondary_api_token = quay_config.secondary_init_token
    if args.failover:
        primary_server = quay_config.secondary_server
        secondary_server = quay_config.primary_server
        primary_credentials = {"username": quay_config.secondary_quay_user, "password": quay_config.secondary_quay_password}
        secondary_credentials = {"username": quay_config.primary_quay_user, "password": quay_config.primary_quay_password}
        primary_api_token = quay_config.secondary_init_token
        secondary_api_token = quay_config.primary_init_token
        
    try:
        preflight.check_dns(primary_server)
        preflight.check_dns(secondary_server)
        preflight.check_port(primary_server)
        preflight.check_port(secondary_server)
        print()
        mover.login_to_quay(server=primary_server, username=primary_credentials['username'], password=primary_credentials['password'], args=args)
        mover.login_to_quay(server=secondary_server, username=secondary_credentials['username'], password=secondary_credentials['password'], args=args)
        print()
    except Exception as e:
        logging.error("Error executing script: {}".format(e))
        exit(1)


    # Create an instance of QuayAPI for the primary server
    primary_quay_api = QuayAPI(base_url=primary_server, api_token=primary_api_token)

    # Create an instance of the QuayAPI class for the secondary server
    secondary_quay_api = QuayAPI(base_url=secondary_server, api_token=secondary_api_token)

    # Call the functions and pass in the token as an argument
    source_data = primary_quay_api.get_data()

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
        destination_data = primary_quay_api.get_data()
        if not destination_data:
            logging.info("Doesn't exist")
            continue
        # Check if the organization needs to be created on the destination server
        create_org = secondary_quay_api.check_if_object_exists(org_name=org)
        if create_org:
            logging.info(f"Organization does not exist: {org} <---")
            secondary_quay_api.create_org(org)
            time.sleep(3)
    
    if args.auto_discovery:
        # Create a dictionary to store the images and tags
        image_dict = {}

        # Loop through the source repositories
        for repo in source_repositories:
            # Get the list of tags for each repository
            tag_list = primary_quay_api.get_tag_info(repo)
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
                source_image_name = primary_quay_api.base_url.strip("https://")+ "/" + org + "/" + repo_and_tag
                destination_image_name = secondary_quay_api.base_url.strip("https://") + "/" + org + "/" + repo_and_tag
                print("")
                ImageMover.podman_operations(operation="pull", image_source=source_image_name, image_and_tag=repo_and_tag, args=args)
                ImageMover.podman_operations(operation="tag", image_source=source_image_name, image_destination=destination_image_name, image_and_tag=repo_and_tag, args=args)
                time.sleep(1)
                print("")
                ImageMover.podman_operations(operation="push", image_source=source_image_name, image_destination=destination_image_name, image_and_tag=repo_and_tag, args=args)
    else:
        try:
            for repository in quay_config.repositories:
                image_source_name = primary_server + "/" + repository
                image_destination_name = secondary_server + "/" + repository
                print("")
                ImageMover.podman_operations(operation="pull", image_source=image_source_name, image_and_tag=repository, args=args)
                ImageMover.podman_operations(operation="tag", image_source=image_source_name, image_destination=image_destination_name, image_and_tag=repository, args=args)
                time.sleep(1)
                print("")
                ImageMover.podman_operations(operation="push", image_source=image_source_name, image_destination=image_destination_name, image_and_tag=repository, args=args)
                print("")
        except Exception as e:
            logging.error("Error executing script: {}".format(e))
            exit(1)
    
