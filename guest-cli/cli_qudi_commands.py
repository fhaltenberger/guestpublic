import requests
import json
import click
from pathlib import Path
from datetime import datetime

def load_config():
    with open("config.json", "r") as config_file:
        config = json.load(config_file)
    return config

config = load_config()

TOKEN_FILE_PATH = config["paths"]["token_file_path"]

def run_rabi(access_token):
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    response = requests.post(
        f"{config['server']['url']}/api/run_remote_rabi", 
        headers=headers,
        verify=True
    )

    try:
        result = response.json()
        if 'task_id' in result:
            click.echo(f"Job submitted successfully with ID: {result['task_id']}")
            click.echo(f"Status: {result.get('status', 'unknown')}")
            click.echo(f"Use 'guest job-status {result['task_id']}' to check the status")
        else:
            click.echo(response.text)
    except ValueError:
        click.echo(response.text)

def run_calibration(access_token):
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    response = requests.post(
        f"{config['server']['url']}/api/run_calibration", 
        headers=headers,
        verify=True
    )

    try:
        result = response.json()
        if 'task_id' in result:
            click.echo(f"Job submitted successfully with ID: {result['task_id']}")
            click.echo(f"Status: {result.get('status', 'unknown')}")
            click.echo(f"Use 'guest job-status {result['task_id']}' to check the status")
        else:
            click.echo(response.text)
    except ValueError:
        click.echo(response.text)

def run_two_qubit_circuit(access_token):
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    response = requests.post(
        f"{config['server']['url']}/api/run_two_qubit_circuit", 
        headers=headers,
        verify=True
    )

    try:
        result = response.json()
        if 'task_id' in result:
            click.echo(f"Job submitted successfully with ID: {result['task_id']}")
            click.echo(f"Status: {result.get('status', 'unknown')}")
            click.echo(f"Use 'guest job-status {result['task_id']}' to check the status")
        else:
            click.echo(response.text)
    except ValueError:
        click.echo(response.text)

def submit_two_qubit_batch(access_token, path=None):
    
    if path is None:
        path = "./tq_experiments/default_tq_experiment.json"

    with open(path, "r") as f:
        experiment_data = json.load(f)
        
    headers = {"Authorization": f"Bearer {access_token}"}
    
    response = requests.post(
        f"{config['server']['url']}/api/submit_two_qubit_batch", 
        headers=headers,
        json=experiment_data,
        verify=True
    )

    try:
        result = response.json()
        if 'task_infos' in result:
            click.echo(result["message"])
            task_infos = result["task_infos"]

            timestamp = datetime.now().isoformat(timespec='seconds').replace(":", "-")
            save_path = Path(f"./experiment_infos/{timestamp}_tq_experiment.json")
            save_path.parent.mkdir(parents=True, exist_ok=True)

            with open(save_path, "w") as f:
                json.dump(task_infos, f, indent=2)
            click.echo(f"Saved task_infos to {save_path}")
        else:
            click.echo(response.text)
    except ValueError:
        click.echo(response.text)