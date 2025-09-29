from authenticate import load_token_json

import requests
import json
import time

def load_config():
    with open("config.json", "r") as config_file:
        config = json.load(config_file)
    return config

config = load_config()

TOKEN_FILE_PATH = config["paths"]["token_file_path"]

def get_user_info(access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.post(
        f"{config['server']['url']}/auth/realms/{config['keycloak']['realm']}/protocol/openid-connect/userinfo", 
        headers=headers,
        verify = './guest.crt'
    )

    print(response.text)

if __name__ == "__main__":
    token = load_token_json()
    
    if token is None:
        raise FileNotFoundError("token.json not found.")
    elif token['expires_at'] - time.time() < 60:
        raise Exception("Token expires in less than 60 seconds, please get a new one.")
    else: 
        print(f"Valid access token found at {TOKEN_FILE_PATH}.")

    access_token = token["access_token"]
    get_user_info(access_token)