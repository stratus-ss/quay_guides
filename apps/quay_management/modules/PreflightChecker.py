import socket
import logging

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
        if "//" in server:
            # If there is http:// or https:// we need to strip that to do dns lookups
            server = server.split("//")[1:][0]
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
        if "//" in server:
            # If there is http:// or https:// we need to strip that to do dns lookups
            server = server.split("//")[1:][0]
        quay_port = 443
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((server, quay_port))
            logging.info(f"{server} is listening on port {quay_port}")
            return True
        except ConnectionRefusedError:
            logging.critical("%s refused the connection on port %s" % quay_port)
            exit(1)
