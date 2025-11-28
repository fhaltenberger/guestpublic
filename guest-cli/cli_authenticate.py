import requests
import time
import sys
import json
import os

def load_config():
    with open("config.json", "r") as config_file:
        config = json.load(config_file)
    return config

config = load_config()

# Configuration
KEYCLOAK_BASE_URL = config["server"]["url"]+"/auth"
CLIENT_ID = config["keycloak"]["client_id"]
REALM = config["keycloak"]["realm"]
TOKEN_FILE_PATH = config["paths"]["token_file_path"]

DEVICE_ENDPOINT = f"{KEYCLOAK_BASE_URL}/realms/{REALM}/protocol/openid-connect/auth/device"
TOKEN_ENDPOINT = f"{KEYCLOAK_BASE_URL}/realms/{REALM}/protocol/openid-connect/token"

def store_token_json(token_json):
    # Add expiration timestamp
    token_json["expires_at"] = time.time() + token_json["expires_in"]
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(TOKEN_FILE_PATH), exist_ok=True)
    
    # Save token to file
    with open(TOKEN_FILE_PATH, "w") as token_file:
        json.dump(token_json, token_file)
    
    print(f"Token stored at {TOKEN_FILE_PATH}")

def load_token_json():
    # Check if token file exists
    if os.path.exists(TOKEN_FILE_PATH):
        with open(TOKEN_FILE_PATH, "r") as token_file:
            token_json = json.load(token_file)
            return token_json
    else:
        return None

def check_token():
    token_json = load_token_json()
    
    if token_json is None:
        print("No existing token found. Starting device flow authentication...")
        return False
    elif token_json['expires_at'] - time.time() < 60:
        print("Token expires in less than 60 seconds, fetching new one...")
        return False
    else:
        print(f"Valid access token found at {TOKEN_FILE_PATH}.")
        return True

def authenticate_device_flow():
    # Step 1: Request device code
    device_resp = requests.post(DEVICE_ENDPOINT, 
                                data={
                                    "client_id": CLIENT_ID,
                                    "scope": "openid"},
                                verify=True)
    device_resp.raise_for_status()
    device_data = device_resp.json()

    print("\nPlease authenticate:")
    print(f"Visit: {device_data['verification_uri_complete']}")
    print(f"If needed, enter code: {device_data['user_code']}")
    print(f"You have {device_data['expires_in']} seconds to complete authentication.\n")

    # Step 2: Poll the token endpoint
    interval = device_data.get("interval", 5)
    start_time = time.time()

    while True:
        time.sleep(interval)
        token_resp = requests.post(TOKEN_ENDPOINT, 
                                data={
                                        "client_id": CLIENT_ID,
                                        "device_code": device_data["device_code"],
                                        "grant_type": "urn:ietf:params:oauth:grant-type:device_code"
                                        },
                                    verify=True)

        if token_resp.status_code == 200:
            token_json = token_resp.json()
            expires_in = token_json["expires_in"]
            print("\nAuthentication successful!")
            print(f"Access token expires in {expires_in // 60} minutes")
            
            # Store the token
            store_token_json(token_json)
            return token_json

        elif token_resp.status_code == 400:
            error = token_resp.json().get("error")
            if error == "authorization_pending":
                continue
            elif error == "slow_down":
                interval += 2
                continue
            else:
                print(f"\nError: {error}")
                sys.exit(1)
        else:
            print(f"\nUnexpected status code: {token_resp.status_code}")
            sys.exit(1)

def main():
    if not check_token():
        authenticate_device_flow()

if __name__ == "__main__":
    main()
