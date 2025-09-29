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
                try:
                    # Convert duration to float first, then to int for calculations
                    duration_float = float(duration)
                    duration_int = int(duration_float)
                    
                    if duration_int < 60:
                        execution_time = f"{duration_float:.1f} seconds"
                    elif duration_int < 3600:
                        minutes = int(duration_int // 60)
                        seconds = duration_int % 60
                        execution_time = f"{minutes} minutes {seconds:.1f} seconds"
                    else:
                        hours = int(duration_int // 3600)
                        minutes = int((duration_int % 3600) // 60)
                        execution_time = f"{hours} hours {minutes} minutes"
                    click.echo(f"Execution Time: {execution_time}")
                except (ValueError, TypeError):
                    click.echo(f"Execution Time: {duration} (could not parse)")
            
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

def list_jobs(token, limit=30):
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

def job_details(token, limit=30):
    """List all jobs with detailed information in a tabular format"""
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
            
        click.echo("\nJob Details:")
        click.echo("-" * 140)
        click.echo(f"{'ID':<36} {'Type':<20} {'Status':<10} {'Submitted At':<25} {'Execution Time':<15} {'Parameters'}")
        click.echo("-" * 140)
        
        for task in result.get('tasks', []):
            task_id = task.get('task_id', 'Unknown')
            task_type = task.get('task_type', 'Unknown')
            status = task.get('status', 'Unknown')
            submitted_at = task.get('submitted_at', 'Unknown')
            
            # Get task parameters
            task_kwargs_str = task.get('task_kwargs', '{}')
            try:
                task_kwargs = json.loads(task_kwargs_str)
            except json.JSONDecodeError:
                task_kwargs = {}
            
            # Format parameters as a compact dict-like string
            if task_kwargs:
                # Filter out None/empty values and format nicely
                filtered_params = {k: v for k, v in task_kwargs.items() if v is not None and v != ''}
                if filtered_params:
                    params_str = str(filtered_params)
                else:
                    params_str = "{}"
            else:
                params_str = "{}"
            
            # Calculate execution time for successful jobs
            execution_time = ""
            if status == 'SUCCESS':
                duration = task.get('duration')
                if duration:
                    try:
                        duration = int(float(duration))
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
                    except (ValueError, TypeError):
                        execution_time = "N/A"
                else:
                    execution_time = "N/A"
            
            click.echo(f"{task_id:<36} {task_type:<20} {status:<10} {submitted_at:<25} {execution_time:<15} {params_str}")
        
    except requests.exceptions.RequestException as e:
        click.echo(f"Error: {str(e)}")
        if hasattr(e, 'response') and e.response:
            try:
                error_detail = e.response.json()
                click.echo(f"Server response: {json.dumps(error_detail, indent=2)}")
            except ValueError:
                click.echo(f"Server response: {e.response.text}")

def resubmit_job(token, job_id):
    """Resubmit a failed job with the same parameters"""
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.post(
            f"{config['server']['url']}/api/resubmit_job/{job_id}",
            headers=headers,
            verify="./guest.crt"
        )
        response.raise_for_status()
        
        result = response.json()
        
        click.echo(f"Job resubmitted successfully!")
        click.echo(f"New Job ID: {result['task_id']}")
        click.echo(f"Status: {result.get('status', 'unknown')}")
        click.echo(f"Resubmitted from: {result.get('resubmitted_from', 'unknown')}")
        click.echo(f"Use 'guest job-status {result['task_id']}' to check the status")
        
        return result['task_id']
        
    except requests.exceptions.RequestException as e:
        click.echo(f"Error: {str(e)}")
        if hasattr(e, 'response') and e.response:
            try:
                error_detail = e.response.json()
                click.echo(f"Server response: {json.dumps(error_detail, indent=2)}")
            except ValueError:
                click.echo(f"Server response: {e.response.text}")
        return None

def check_availability(token):
    """Check if the server is reachable and get module states"""
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        # First check if the main server is reachable
        click.echo("🔍 Checking server availability...")
        
        # Try to reach the main API endpoint
        response = requests.get(
            f"{config['server']['url']}/api/tasks?limit=1",
            headers=headers,
            verify="./guest.crt",
            timeout=10
        )
        response.raise_for_status()
        
        click.echo("✅ Server is reachable")
        
        # Now try to get module states from the quantum computer
        click.echo("\n🔍 Checking quantum computer module states...")
        
        try:
            # Try to reach the quantum computer's module states endpoint
            module_response = requests.get(
                f"{config['server']['url']}/api/get_module_states",
                headers=headers,
                verify="./guest.crt",
                timeout=10
            )
            module_response.raise_for_status()
            
            module_states = module_response.json()
            
            click.echo("✅ Quantum computer is reachable")
            click.echo("\n📊 Module States:")
            click.echo("-" * 50)
            
            if isinstance(module_states, dict):
                for module_name, state in module_states.items():
                    # Color code the states
                    if state == "idle":
                        state_display = f"🟢 {state}"
                    elif state == "locked":
                        state_display = f"🔴 {state}"
                    elif state == "inactive":
                        state_display = f"⚪ {state}"
                    else:
                        state_display = f"❓ {state}"
                    
                    click.echo(f"{module_name:<20} {state_display}")
            else:
                click.echo(f"Module states: {module_states}")
            
            # Summary
            if isinstance(module_states, dict):
                idle_count = sum(1 for state in module_states.values() if state == "idle")
                locked_count = sum(1 for state in module_states.values() if state == "locked")
                inactive_count = sum(1 for state in module_states.values() if state == "inactive")
                
                click.echo("-" * 50)
                click.echo(f"Summary: {idle_count} idle, {locked_count} locked, {inactive_count} inactive")
                
                if locked_count > 0:
                    click.echo("⚠️  Some modules are locked (busy)")
                elif idle_count > 0:
                    click.echo("✅ Modules are available for new jobs")
                else:
                    click.echo("ℹ️  No active modules found")
            
        except requests.exceptions.RequestException as e:
            click.echo("❌ Quantum computer is not reachable")
            click.echo(f"   Error: {str(e)}")
            if hasattr(e, 'response') and e.response:
                try:
                    error_detail = e.response.json()
                    click.echo(f"   Server response: {json.dumps(error_detail, indent=2)}")
                except ValueError:
                    click.echo(f"   Server response: {e.response.text}")
        
    except requests.exceptions.RequestException as e:
        click.echo("❌ Server is not reachable")
        click.echo(f"   Error: {str(e)}")
        if hasattr(e, 'response') and e.response:
            try:
                error_detail = e.response.json()
                click.echo(f"   Server response: {json.dumps(error_detail, indent=2)}")
            except ValueError:
                click.echo(f"   Server response: {e.response.text}")
    except requests.exceptions.Timeout:
        click.echo("❌ Server request timed out")
    except Exception as e:
        click.echo(f"❌ Unexpected error: {str(e)}")