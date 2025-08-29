import requests
import json
import click
import os
from pathlib import Path
from datetime import datetime

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
        
        # Show execution time for successful jobs
        if result['status'] == 'SUCCESS':
            duration = result.get('duration')
            if duration:
                if duration < 60:
                    execution_time = f"{duration:.1f} seconds"
                elif duration < 3600:
                    minutes = int(duration // 60)
                    seconds = duration % 60
                    execution_time = f"{minutes} minutes {seconds:.1f} seconds"
                else:
                    hours = int(duration // 3600)
                    minutes = int((duration % 3600) // 60)
                    execution_time = f"{hours} hours {minutes} minutes"
                click.echo(f"Execution Time: {execution_time}")
            
            click.echo("\nResults:")
            if 'result' in result:
                # Format the results nicely
                formatted_results = json.dumps(result['result'], indent=2)
                click.echo(formatted_results)   
            else:
                click.echo("No result data available")
        elif result['status'] == 'FAILURE':
            error_msg = result.get('error', 'Unknown error')
            failure_type = result.get('failure_type', 'UNKNOWN_ERROR')
            retries = result.get('retries', '0')
            
            click.echo(f"\nError: {error_msg}")
            click.echo(f"Failure Type: {failure_type}")
            click.echo(f"Retries Attempted: {retries}")
            
            # Provide helpful information based on failure type
            if failure_type == 'QUDI_MODULES_BUSY':
                click.echo("Note: QUDI modules are currently busy. The job will be retried automatically.")
            elif failure_type == 'QUDI_SERVER_UNREACHABLE':
                click.echo("Note: QUDI server is unreachable. The job will be retried automatically.")
            elif failure_type == 'TIMEOUT':
                click.echo("Note: The operation timed out. The job will be retried automatically.")
            elif failure_type == 'CONNECTION_ERROR':
                click.echo("Note: Connection error occurred. The job will be retried automatically.")
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
    """List all jobs with their submission times and execution duration for successful jobs"""
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
        click.echo("-" * 140)
        click.echo(f"{'ID':<36} {'Type':<20} {'Status':<10} {'Submitted At':<25} {'Execution Time':<15} {'Failure Info'}")
        click.echo("-" * 140)
        
        for task in result.get('tasks', []):
            task_id = task.get('task_id', 'Unknown')
            task_type = task.get('task_type', 'Unknown')
            status = task.get('status', 'Unknown')
            submitted_at = task.get('submitted_at', 'Unknown')
            
            # Calculate execution time for successful jobs
            execution_time = ""
            if status == 'SUCCESS':
                duration = int(float(task.get('duration')))
                if duration:
                    # Convert seconds to human readable format
                    if duration < 60:
                        execution_time = f"{duration:.1f}s"
                    elif duration < 3600:
                        minutes = int(duration // 60)
                        seconds = duration % 60
                        execution_time = f"{minutes}m {seconds:.1f}s"
                    else:
                        hours = int(duration // 3600)
                        minutes = int((duration % 3600) // 60)
                        execution_time = f"{hours}h {minutes}m"
                else:
                    execution_time = "N/A"
            
            # Get failure information for failed jobs
            failure_info = ""
            if status == 'FAILURE':
                failure_type = task.get('failure_type', 'UNKNOWN')
                retries = task.get('retries', '0')
                if failure_type == 'QUDI_MODULES_BUSY':
                    failure_info = "QUDI busy"
                elif failure_type == 'QUDI_SERVER_UNREACHABLE':
                    failure_info = "QUDI unreachable"
                elif failure_type == 'TIMEOUT':
                    failure_info = "Timeout"
                elif failure_type == 'CONNECTION_ERROR':
                    failure_info = "Connection error"
                else:
                    failure_info = f"Error (retries: {retries})"
            
            click.echo(f"{task_id:<36} {task_type:<20} {status:<10} {submitted_at:<25} {execution_time:<15} {failure_info}")
        
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

def batch_download_results(token, experiment_info_json, output_dir=None):
    """Batch download all results from an experiment info file"""
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        experiment_info_path = f"./experiment_infos/{experiment_info_json}"
        
        with open(experiment_info_path, 'r') as f:
            experiment_data = json.load(f)

        experiment_data_filename = os.path.basename(experiment_info_path)
        subfolder = experiment_data_filename[:experiment_data_filename.find('_')]

        click.echo(f"Loading experiment info from: {experiment_info_path}")
        
        # Create output directory if specified
        if output_dir:
            Path(output_dir).mkdir(parents=True, exist_ok=True)
        else:
            # Use the same directory as the experiment info file
            output_dir = f"./batch_results/{subfolder}"
            Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Extract task IDs from the experiment data
        task_ids = list(experiment_data.keys())
        click.echo(f"Found {len(task_ids)} tasks to download")
        
        successful_downloads = 0
        failed_downloads = 0
        
        for task_id in task_ids:
            
            try:
                # First check if the job is completed
                status_response = requests.get(
                    f"{config['server']['url']}/api/tasks/{task_id}",
                    headers=headers,
                    verify="./guest.crt"
                )
                status_response.raise_for_status()
                
                job_status = status_response.json()
                if job_status.get('status') != 'SUCCESS':
                    click.echo(f"WARNING: Job {task_id} is not completed yet. Status: {job_status.get('status')}")
                    failed_downloads += 1
                    continue
                
                # Download the result file
                download_response = requests.get(
                    f"{config['server']['url']}/api/tasks/{task_id}/download",
                    headers=headers,
                    verify="./guest.crt",
                    stream=True
                )
                download_response.raise_for_status()
                
                output_filename = f"{task_id}.json"
                output_path = os.path.join(output_dir, output_filename)
                
                # Save the file
                with open(output_path, 'wb') as f:
                    for chunk in download_response.iter_content(chunk_size=8192):
                        f.write(chunk)

                successful_downloads += 1
                
            except requests.exceptions.RequestException as e:
                click.echo(f"Failed to download {task_id}: {str(e)}")
                failed_downloads += 1
                continue
        
        # Summary
        click.echo(f"\nDownload Summary:")
        click.echo(f"Successful:       {successful_downloads}")
        click.echo(f"Failed:           {failed_downloads}")
        click.echo(f"Output directory: {output_dir}")
        
        return successful_downloads, failed_downloads
        
    except FileNotFoundError as e:
        click.echo(f"Experiment info file not found: {e}")
        return 0, 0
    except json.JSONDecodeError as e:
        click.echo(f"Invalid JSON in experiment info file: {str(e)}")
        return 0, 0
    except Exception as e:
        click.echo(f"Unexpected error: {str(e)}")
        return 0, 0