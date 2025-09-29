#!/usr/bin/env python3
import click
import os
import requests
import json

# Import our modules
from cli_authenticate import authenticate_device_flow, check_token, load_token_json
from cli_send_qasm_file import send_qasm_file
from cli_qudi_commands import run_rabi, run_calibration, run_two_qubit_circuit, submit_two_qubit_batch
from cli_userinfo import get_user_info
from cli_scheduling import get_job_status, list_jobs, download_job_result, batch_download_results, resubmit_job, job_details, check_availability

def load_config():
    with open("config.json", "r") as config_file:
        config = json.load(config_file)
    return config

config = load_config()

@click.group()
def cli():
    """GUEST CLI - Command line interface for GUEST services"""
    pass

@cli.command()
def auth():
    """Authenticate with the GUEST service using Keycloak's device flow"""
    if not check_token():
        authenticate_device_flow()
    else:
        click.echo("You are already authenticated.")

@cli.command()
def userinfo():
    """Get information about the authenticated user"""
    token = load_token_json()["access_token"]
    if token:
        get_user_info(token)
    else:
        click.echo("You are not authenticated. Please authenticate using the 'auth' command.")

# ----------------- ACTUAL COMMANDS -----------------------------------------------------------        

@cli.command()
@click.argument('qasm_file', type=click.Path(exists=True))
def submit(qasm_file):
    """Submit a QASM file to the GUEST backend service"""
    token = load_token_json()["access_token"]
    if not token:
        click.echo("You are not authenticated. Please authenticate using the 'auth' command.")
    send_qasm_file(qasm_file, token)

@cli.command()
def rabi():
    """Run a Rabi oscillation experiment on the remote qudi server"""
    token = load_token_json()["access_token"]
    if not token:
        click.echo("You are not authenticated. Please authenticate using the 'auth' command.")
    run_rabi(token)

@cli.command()
def calibrate():
    """Run a calibration experiment on the remote qudi server"""
    token = load_token_json()["access_token"]
    if not token:
        click.echo("You are not authenticated. Please authenticate using the 'auth' command.")
    run_calibration(token)

@cli.command()
def two_qubit_circuit():
    """Run a two qubit circuit with readout of all 4 states"""
    token = load_token_json()["access_token"]
    if not token:
        click.echo("You are not authenticated. Please authenticate using the 'auth' command.")
    run_two_qubit_circuit(token)

@cli.command('submit-tq-batch')
def submit_tq_batch():
    """Submit a batch of experiments to be run as two qubit circuits"""
    token = load_token_json()["access_token"]
    if not token:
        click.echo("You are not authenticated. Please authenticate using the 'auth' command.")
    submit_two_qubit_batch(token)

# ------------ QUEUE MANAGEMENT STUFF ---------------------

@cli.command('job-status')
@click.argument('job_id')
def job_status(job_id):
    """Check the status of a job and retrieve results if complete"""
    token = load_token_json()["access_token"]
    if not token:
        click.echo("You are not authenticated. Please authenticate using the 'auth' command.")
    get_job_status(token, job_id)

@cli.command('list-jobs')
@click.option('--limit', type=int, default=30, help='Maximum number of jobs to list')
def jobs_list(limit):
    """List your recent jobs"""
    token = load_token_json()["access_token"]
    if not token:
        click.echo("You are not authenticated. Please authenticate using the 'auth' command.")
        return
    
    list_jobs(token, limit)

@cli.command('job-details')
@click.option('--limit', type=int, default=30, help='Maximum number of jobs to list')
def jobs_details(limit):
    """List your recent jobs with detailed information"""
    token = load_token_json()["access_token"]
    if not token:
        click.echo("You are not authenticated. Please authenticate using the 'auth' command.")
        return
    
    job_details(token, limit)

@cli.command('resubmit')
@click.argument('job_id')
def resubmit(job_id):
    """Resubmit a failed job with the same parameters"""
    token = load_token_json()["access_token"]
    if not token:
        click.echo("You are not authenticated. Please authenticate using the 'auth' command.")
        return
    
    resubmit_job(token, job_id)

@cli.command('download-result')
@click.argument('job_id')
@click.option('--output', '-o', help='Output file path')
def download_result(job_id, output):
    """Download the result file for a completed job"""
    token = load_token_json()["access_token"]
    if not token:
        click.echo("You are not authenticated. Please authenticate using the 'auth' command.")
        return
    
    download_job_result(token, job_id, output)

@cli.command('batch-download')
@click.argument('experiment_info_json')
@click.option('--output-dir', '-o', help='Output directory for downloaded files')
def batch_download(experiment_info_json, output_dir):
    """Batch download all results from an experiment info file"""
    token = load_token_json()["access_token"]
    if not token:
        click.echo("You are not authenticated. Please authenticate using the 'auth' command.")
        return
    
    batch_download_results(token, experiment_info_json, output_dir)

@cli.command('check-availability')
def check_availability_cmd():
    """Check if the server is reachable and get quantum computer module states"""
    token = load_token_json()["access_token"]
    if not token:
        click.echo("You are not authenticated. Please authenticate using the 'auth' command.")
        return
    
    check_availability(token)
    
if __name__ == '__main__':
    # Ensure we're in the correct directory
    script_dir = os.path.dirname(os.path.realpath(__file__))
    os.chdir(script_dir)
    
    cli() 