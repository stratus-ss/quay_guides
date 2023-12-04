from .BaseOperations import BaseOperations
import yaml
import subprocess
import logging
import time
import base64

class OpenShiftCommands:
    def __init__(self) -> None:
        pass
    
    @staticmethod
    def does_secret_exist(secret_name: str = None, namespace: str = None) -> bool:
        """
        Description:
            Checks to see if a secret exists in the cluster
        Args:
            secret_name (str, optional): The name of the secret to look for. Defaults to None.
            namespace (str, optional): The namespace to look for the secret within. Defaults to None.

        Returns:
            bool: True if the secret exists, false if it does not
        """
        if namespace is None:
            secret_command = ["oc", "get", "secret", secret_name]
        else:
            secret_command = ["oc", "get", "secret", secret_name, "-n", namespace]
        try:
            subprocess.check_output(secret_command)
            return True
        except:
            return False

    @staticmethod
    def openshift_apply_file(file_path: str = None, namespace: str = None):
        """
        Description:
            Uses the `oc apply` command to create or modify OpenShift objects
        Args:
            file_path (str, optional): The full path to the file to apply to the cluster. Defaults to None.
            namespace (str, optional): Which namespace to apply the resources to. Defaults to None.
        """
        if namespace:
            apply_command = ["oc", "apply", "-f", file_path, "-n", namespace]
        else:
            apply_command = ["oc", "apply", "-f", file_path]
        try:
            subprocess.check_output(apply_command)
        except:
            logging.critical(f"Failed to apply ---> {file_path}")
            logging.critical("Aborting")
            exit(1)


    @staticmethod
    def openshift_create_secret(file_path: str, namespace: str = None, secret_name: str = "init-config-bundle-secret", secret_type: str = "generic" ):
        """
        Description:
            Creates a secret from a file. The initial intent is to create the `init-config-bundle-secret`
        Args:
            file_path (str): The full path to the file to apply to the cluster
            namespace (str, optional): Which namespace to apply the resources to. Defaults to None.
            secret_name (str, optional): Name of the secret. Defaults to init-config-bundle-secret.
            secret_type (str, optional): The type of secret to be created. Defaults to generic.
        """
        secret_command = ["oc", "create", "secret", secret_type, secret_name, f"--from-file={file_path}"]
        if secret_name == "init-config-bundle-secret":
            secret_command = ["oc", "create", "secret", secret_type, secret_name, f"--from-file=config.yaml={file_path}"]
        if namespace:
            secret_command.extend(["-n", namespace])
            output = OpenShiftCommands.does_secret_exist(secret_name=secret_name, namespace=namespace)  
        else:
            output = OpenShiftCommands.does_secret_exist(secret_name=secret_name)
        # If output is false, the secret doesn't exist, go ahead and create it
        if not output:
            logging.info(f"The secret {secret_name} does not currently exist... creating")
            subprocess.check_output(secret_command)
        else:
            logging.error(f"The secret {secret_name} already exists!")

    @staticmethod
    def openshift_get_infrastructure_name(command_output):
        """
        Returns the current infrastructure ID of an OpenShift Cluster
        """
        command_output = yaml.load(command_output.decode(), Loader=yaml.FullLoader)
        get_infraID_cmd = command_output['status']['infrastructureName']
        return(get_infraID_cmd)

    @classmethod
    def openshift_get_object(cls, **kwargs):
        """
        Description: 
            Gets an object from openshift and returns the yaml output

        Args:
            Takes **kwargs but current expects
            object_type: usually pod, node, secret etc
            object_name: the name of the object if required/known
            label: A label used to identify the correct object
            namespace: The namespace where the object resides (if any)
        """
        check_command = ["oc", "get", kwargs["object_type"]]
        if kwargs.get("object_name"):
            check_command.extend([kwargs["object_name"]])
        if kwargs.get("namespace"):
            check_command.extend(["-n", kwargs["namespace"]])
        if kwargs.get("label"):
            check_command.extend(["-l", kwargs["label"]])
        check_command.extend(["-o", "yaml"])        
        return(subprocess.check_output(check_command))

    @classmethod
    def openshift_generic_wait(cls, counter: int = None, iterations: int = 10, delay_between_checks: int = 60, openshift_object: str = None):
        """
        Description:
            Provides a generic wait function which provides logging and sleep
        Args:
            counter (int, optional): _description_. Defaults to None.
            iterations (int, optional): _description_. Defaults to 10.
            delay_between_checks (int, optional): _description_. Defaults to 60.
            openshift_object (str, optional): _description_. Defaults to None.
        """
        remaining_time = (iterations-counter) * delay_between_checks /60
        logging.info(f"Not all {openshift_object} are ready.")
        logging.info(f"{(iterations-counter)} iterations remaining.")
        logging.info(f"{remaining_time} minutes remaining before timing out")
        time.sleep(delay_between_checks)
        
    @staticmethod
    def openshift_login(api_url: str, username: str, passwd: str) -> None:
        """
        Description:
            Logs into the OpenShift Cluster with username and password
        Args:
            api_url (str): The url including protocol (http/https) and port are expected
            username (str): OpenShift cluster admin user
            passwd (str): OpenShift cluster admin password
        """
        openshift_login_command = ["oc", "login", "-u", username, "-p", passwd, api_url]
        openshift_login_command = BaseOperations.do_i_skip_tls(openshift_login_command)
        try:
            subprocess.check_output(openshift_login_command)
        except:
            logging.critical(f"Failed to log into {api_url}")
            exit(1)

    @staticmethod
    def openshift_object_ready(object_dict: dict = None, openshift_object: str = None):
        if all(value == True for value in object_dict.values()):
            logging.info(f"All of the {openshift_object} are reporting ready")
            logging.info("Continuing to the next step...")
            return True
        else:
            return False

    @staticmethod
    def openshift_ready_check(output: dict = None, status: str = "conditions", crd: str = None):
        object_ready = {}
        if crd:
            try:
                if output['items'][0]:
                    object_name = output['items'][0]['metadata']['name']
                    object_ready[object_name] = True
                else:
                    object_ready[crd] = False
            except:
                # If it errors its likely the items are empty because it hasnt finished initializing
                pass
        else:
            for x in output['items']:         
                object_name = x['metadata']['name']
                if status == "phase":
                    if x['status'][status] == "Succeeded":
                        # Assuming any pod that has succeeded shouldn't be running anyways 
                        # as it is likely a job pod
                        continue
                    elif x['status'][status] == "Running":
                        object_ready[object_name] = True
                    else:
                        object_ready[object_name] = False
                else:
                    object_ready[object_name] = False
                    for y in x['status'][status]:
                        if y['type'] == "Ready":
                            if y['status'] == "True":
                                object_ready[object_name] = True
        return(object_ready)

    @staticmethod
    def openshift_replace_quay_init_secret(full_path_to_file: str = None, secret_name: str = None, namespace: str = "quay"):
        """
        Description:
            Uses 'oc replace' in order to update a secret in OpenShift
        Args:
            full_path_to_file (str, optional): The path to the secret file with updated contents
            secret_name (str, optional): The name of the secret in OpenShift to replace
        Returns: 
            Nothing. This method performs an action with no returns
        """
        openshift_create_secret_cmd = ["oc", "create", "secret", "generic", secret_name, f"--from-file=config.yaml={full_path_to_file}", "--dry-run=client", "-o", "yaml"]
        new_secret_file_path = "/tmp/quay_new_secret.yaml"
        try:
            secret_output = subprocess.check_output(openshift_create_secret_cmd)
        except Exception as e:
            copy_command = ", ".join(openshift_create_secret_cmd).replace(",", "")
            logging.error(f"Could not process {full_path_to_file} attempted to run {copy_command} but it failed")
            logging.error(e)
            exit(1)
        
        with open(new_secret_file_path, "w") as file:
            file.write(yaml.dump(yaml.load(secret_output, Loader=yaml.FullLoader)))
            file.close()
        openshift_replace_secret_cmd = ["oc", "replace", "-f", new_secret_file_path, "-n", namespace]
        try:
            output = (subprocess.check_output(openshift_replace_secret_cmd))
        except:
            logging.critical(f"Failed to use this file {openshift_replace_secret_cmd} to replace object")
            exit(1)

    @staticmethod 
    def openshift_waitfor_pods(namespace: str = None, 
            openshift_object: str = "pods", 
            iterations: int = None, 
            delay_between_checks: int = None,
            number_of_pods: int = None
            ):
        """
        Description:
            Wait for pods to become bound. We want to make sure they are all ready before proceeding
        Args:
            namespace (str, optional): Which namespace (if any) the object resides in. Defaults to None.
            openshift_object (str, optional): What type of object is this. Defaults to pods.
            iterations (int, optional): Number of checks to run . Defaults to None.
            delay_between_checks (int, optional): The amount of time in seconds between each check. Defaults to None.
        """
        openshift_cmd_arguments = {
            "object_type": openshift_object,
            "namespace": namespace,
        }
        object_ready = {}
        counter = 0
        while counter <= iterations:
            OpenShiftCommands.openshift_generic_wait(
                                                    counter=counter, 
                                                    iterations=iterations, 
                                                    delay_between_checks=delay_between_checks, 
                                                    openshift_object=openshift_object
                                                    )
            try:
                output = OpenShiftCommands.openshift_get_object(**openshift_cmd_arguments)
            except subprocess.CalledProcessError:
                # The error already gets printed to the screen
                # We don't need to capture the exit code
                counter += 1
            output = yaml.load(output, Loader=yaml.FullLoader)
            object_ready = OpenShiftCommands.openshift_ready_check(output=output, status="phase")
            if len(object_ready) >= number_of_pods:
                move_on = OpenShiftCommands.openshift_object_ready(object_dict=object_ready, openshift_object=openshift_object)
                if move_on:
                    return
            counter +=1
    

    @staticmethod
    def openshift_waitfor_object(
            namespace: str = None, 
            openshift_object: str = None, 
            iterations: int = None, 
            delay_between_checks: int = None, 
            label: str = None, 
            crd: str = None,
            replicas: int = None
            ):
        """
        Description:
            Waits for an object to become Ready for a given number of iterations
        Args:
            namespace (str, optional): Which namespace (if any) the object resides in. Defaults to None.
            openshift_object (str, optional): What type of object is this. Defaults to None.
            iterations (int, optional): Number of checks to run . Defaults to None.
            delay_between_checks (int, optional): The amount of time in seconds between each check. Defaults to None.
        """
        openshift_cmd_arguments = {
            "object_type": openshift_object,
            "namespace": namespace,
            "label": label
        }
        object_ready = {}
        counter = 0
        while counter <= iterations:
            OpenShiftCommands.openshift_generic_wait(counter=counter, iterations=iterations, delay_between_checks=delay_between_checks, openshift_object=openshift_object)
            try:
                output = OpenShiftCommands.openshift_get_object(**openshift_cmd_arguments)
            except subprocess.CalledProcessError:
                # The error already gets printed to the screen
                # We don't need to capture the exit code
                counter += 1
                continue
            output = yaml.load(output, Loader=yaml.FullLoader)
            object_ready = OpenShiftCommands.openshift_ready_check(output=output, crd=crd)
            if object_ready:
                if replicas:
                    if len(object_ready) == replicas:
                         complete = OpenShiftCommands.openshift_object_ready(object_dict=object_ready, openshift_object=openshift_object)
                         counter += 1
                         if complete:
                             return
                else:
                    complete = OpenShiftCommands.openshift_object_ready(object_dict=object_ready, openshift_object=openshift_object)
                    counter += 1
                    if complete:
                        return
            else:
                if crd:
                    logging.info(f"{crd} exists... continuing to the next step")
                    return
                counter +=1
        logging.critical(f"{openshift_object} did not become ready after {(iterations*delay_between_checks/60)} minutes")
        exit(1)

    @staticmethod
    def openshift_waitfor_storage(
            namespace: str = None, 
            openshift_object: str = None, 
            iterations: int = None, 
            delay_between_checks: int = None,
            label: str = None
            ):
        """
        Description:
            Wait for PV or PVCs to become bound. Unfortunately their status is in a different 
            section compared to most objects requiring its own method
        Args:
            namespace (str, optional): Which namespace (if any) the object resides in. Defaults to None.
            openshift_object (str, optional): What type of object is this (pv or pvc). Defaults to None.
            iterations (int, optional): Number of checks to run . Defaults to None.
            delay_between_checks (int, optional): The amount of time in seconds between each check. Defaults to None.
        """
        openshift_cmd_arguments = {
            "object_type": openshift_object,
            "namespace": namespace,
            "label": label
        }
        object_ready = {}
        counter = 0
        while counter <= iterations:
            OpenShiftCommands.openshift_generic_wait(counter=counter, iterations=iterations, delay_between_checks=delay_between_checks, openshift_object=openshift_object)
            output = OpenShiftCommands.openshift_get_object(**openshift_cmd_arguments)
            output = yaml.load(output, Loader=yaml.FullLoader)
            for x in output['items']:
                object_name = x['metadata']['name']
                object_ready[object_name] = False
                if x['status']['phase'] == "Bound":
                    object_ready[object_name] = True
            if all(value == True for value in object_ready.values()):
                logging.info(f"All of the {openshift_object} are reporting ready")
                logging.info("Continuing to the next step...")
                return
            else:
                counter +=1
        logging.critical(f"{openshift_object} did not become ready after {(iterations*delay_between_checks/60)} minutes")
        exit(1)

    @staticmethod
    def openshift_transfer_file(remote_filename: str = "/tmp/generic.py", 
                                filename: str = None, 
                                namespace: str = None, 
                                pod_name: str = None):
        """
        Description: 
            Transfers a file to a pod

        Args:
            remote_filename (str, optional): The location within the pod to create the file. Defaults to "/tmp/generic.py".
            filename (str, optional): The path to the local file you intend to transfer. Defaults to None.
            namespace (str, optional): Namespace where the pod resides. Defaults to None.
            pod_name (str, optional): Name of the pod to transfer files to. Defaults to None.
        """
        ocp_cmd = ["oc", "cp", filename, f"{namespace}/{pod_name}:{remote_filename}"]
        return(subprocess.check_output(ocp_cmd))
    
    @staticmethod
    def openshift_exec_pod(command: list = None, pod_name: str = None, namespace: str = None):
        """
        Description: 
            Execs into a pod to run a command

        Args:
            command (list, optional): A command broken into a list that subprocess can recognize. Defaults to None.
            pod_name (str, optional): Name of the pod to exec into. Defaults to None.
            namespace (str, optional): Namespace where the pod resides. Defaults to None.
        
        Returns: 
            the response from subprocess
        """
        ocp_cmd = ["oc", "exec", "-n", namespace, "-it", pod_name, "--"]
        ocp_cmd.extend(command)
        return(subprocess.check_output(ocp_cmd))
    
    @staticmethod
    def openshift_process_secret(secret: dict = None) -> dict:
        """
        Description:  
            loops over the 'data' section of the secret to build a decoded dict

        Args:
            secret (dict, optional): takes a dict, presumably from a YAML. Defaults to None.

        Returns:
            dict: key/value dict of decoded secrets
        """
        secret_values = {}
        for key in secret['data']:
           secret_values[key] = base64.b64decode(secret['data'][key]).decode()
        return(secret_values)
        