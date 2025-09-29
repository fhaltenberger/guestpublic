import requests
import json
import click
import os

def load_config():
    with open("config.json", "r") as config_file:
        config = json.load(config_file)
    return config

config = load_config()

def get_job_status(token, job_id):
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(
            f"{config['server']['url']}/api/tasks/{job_id}", 
            headers=headers,
            verify="./guest.crt"
        )
        response.raise_for_status()
        
        result = response.json()
        
        click.echo(f"Job ID: {result['task_id']}")
        click.echo(f"Status: {result['status']}")
        
        if result['status'] == 'SUCCESS':
            click.echo("\nResults:")
            if 'result' in result:
                # Format the results nicely
                formatted_results = json.dumps(result['result'], indent=2)
                click.echo(formatted_results)   
            else:
                click.echo("No result data available")
        elif result['status'] == 'FAILURE':
            click.echo(f"\nError: {result.get('error', 'Unknown error')}")
        elif result['status'] == 'PENDING':
            click.echo("\nJob is still pending in the queue")
        elif result['status'] == 'STARTED':
            click.echo("\nJob is currently running")
            if 'progress' in result:
                click.echo(f"Progress: {result['progress']}")
        
    except requests.exceptions.RequestException as e:
        click.echo(f"Error: {str(e)}")
        if hasattr(e, 'response') and e.response:
            try:
                error_detail = e.response.json()
                click.echo(f"Server response: {json.dumps(error_detail, indent=2)}")
            except ValueError:
                click.echo(f"Server response: {e.response.text}")

def list_jobs(token, limit=10):
    """List all jobs with their submission times"""
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(
            f"{config['server']['url']}/api/tasks?limit={limit}", 
            headers=headers,
            verify="./guest.crt"
        )
        response.raise_for_status()
        
        result = response.json()
        
        if not result.get('tasks'):
            click.echo("No jobs found.")
            return
            
        click.echo("\nYour Jobs:")
        click.echo("-" * 90)
        click.echo(f"{'ID':<36} {'Type':<20} {'Status':<10} {'Submitted At'}")
        click.echo("-" * 90)
        
        for task in result.get('tasks', []):
            task_id = task.get('task_id', 'Unknown')
            task_type = task.get('task_type', 'Unknown')
            status = task.get('status', 'Unknown')
            submitted_at = task.get('submitted_at', 'Unknown')
            
            click.echo(f"{task_id:<36} {task_type:<20} {status:<10} {submitted_at}")
        
    except requests.exceptions.RequestException as e:
        click.echo(f"Error: {str(e)}")
        if hasattr(e, 'response') and e.response:
            try:
                error_detail = e.response.json()
                click.echo(f"Server response: {json.dumps(error_detail, indent=2)}")
            except ValueError:
                click.echo(f"Server response: {e.response.text}")

def download_job_result(token, job_id, output_path=None):
    """Download the result file for a completed job"""
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        # First check if the job is completed
        status_response = requests.get(
            f"{config['server']['url']}/api/tasks/{job_id}",
            headers=headers,
            verify="./guest.crt"
        )
        status_response.raise_for_status()
        
        job_status = status_response.json()
        if job_status.get('status') != 'SUCCESS':
            click.echo(f"Job {job_id} is not completed yet. Current status: {job_status.get('status')}")
            return False
        
        # Download the result file
        download_response = requests.get(
            f"{config['server']['url']}/api/tasks/{job_id}/download",
            headers=headers,
            verify="./guest.crt",
            stream=True  # Stream the response for large files
        )
        download_response.raise_for_status()
        
        # Determine output filename
        if not output_path:
            task_type = job_status.get('task_type', 'unknown')
            output_path = f"results/{task_type}_{job_id}.json"
        
        # Save the file
        with open(output_path, 'wb') as f:
            for chunk in download_response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        click.echo(f"Results saved to {output_path}")
        return True
        
    except requests.exceptions.RequestException as e:
        click.echo(f"Error: {str(e)}")
        if hasattr(e, 'response') and e.response:
            try:
                error_detail = e.response.json()
                click.echo(f"Server response: {json.dumps(error_detail, indent=2)}")
            except ValueError:
                click.echo(f"Server response: {e.response.text}")
        return False