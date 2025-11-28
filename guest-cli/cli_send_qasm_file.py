import requests
import json
import time
import argparse
import click

def load_config():
    with open("config.json", "r") as config_file:
        config = json.load(config_file)
    return config

config = load_config()

TOKEN_FILE_PATH = config["paths"]["token_file_path"]

def send_qasm_file(qasm_file_path, access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    
    with open(qasm_file_path, "rb") as qasm_file:
        response = requests.post(
            f"{config['server']['url']}/api/simulate_qasm", 
            headers=headers, 
            files={"qasm_file": qasm_file},
            verify=True
        )

    try:
        result = response.json()
        if 'task_id' in result:
            click.echo(f"QASM simulation submitted successfully with ID: {result['task_id']}")
            click.echo(f"Status: {result.get('status', 'unknown')}")
            click.echo(f"Use 'guest job-status {result['task_id']}' to check the status and retrieve results")
        else:
            click.echo(response.text)
    except ValueError:
        click.echo(response.text)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Send a QASM file to the Keycloak server for simulation.")
    parser.add_argument(
        '--qasm_file', 
        type=str, 
        required=True, 
        help="Path to the QASM file to send."
    )
    
    args = parser.parse_args()
    qasm_file_path = args.qasm_file

    config = load_config()
    TOKEN_FILE_PATH = config["paths"]["token_file_path"]

    token = load_token()
    
    if token is None:
        raise FileNotFoundError("token.json not found.")
    elif token['expires_at'] - time.time() < 60:
        raise Exception("Token expires in less than 60 seconds, please get a new one.")
    else: 
        print(f"Valid access token found at {TOKEN_FILE_PATH}.")

    access_token = token["access_token"]
    
    send_qasm_file(qasm_file_path, access_token)
