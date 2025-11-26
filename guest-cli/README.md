# Quick Start Guide for the CLI

Assuming that GUEST is already running on a server, you can interact with the application using the CLI for tasks like simulating QASM files or interacting with the API. 
If you want to set up a Q-AIM server yourself, check the [server quick start guide](https://github.com/fhaltenberger/q-aim/tree/main/qaim-server#readme).

## Before you get started
Before you can perform tasks on the GUEST server, you need to set up a few things.

1. Make sure that you can reach the server. Try `ping <SERVER IP>`. If there is no response, you may have to add a route to the server's IP address.

2. Ask your server admin to set up an account for you and get the username and password. Also, the server admin needs to send you the `client secret`, which is a short encrypted string which you need to paste into your local `guest/guest-cli/config.json`at `"keycloak"/"client_secret"`.

3. Install the necessary packages: 
 ```bash
cd qaim-cli
 pip install -r requirements.txt
 ```

4. You're ready to go!

## Get access token

In order to perform tasks on the Q-AIM server, you will need an access token. To get this, run:
 ```bash
 python3 get_access_token.py
 ```

Using `python` instead of `python3` should also work, depending on your setup.

(**Important note**: At the moment, this connects to the Q-AIM server via `https`, but ignores the server's certificate, which could pose a security threat. You will also be warned about this. Only use this if you understand this risk.)

Next, you will be prompted to enter your username and password. If everything works, a valid token will be stored at `q-aim/qaim-cli/keycloak_token/token.json`. 
This token is only valid for a limited time, and once it has expired you will need to get a new token via the same python script. 
When using the other functions from the Q-AIM CLI, this token will automatically be used for authentication and grant you permission to the ressources your user's rights are authorized to use.

## Simulating your first quantum circuit on the server

You can send a "test" circuit to the Q-AIM server, which it then sets up and executes with Qiskit's `Aer` simulator. To do this, run:
 ```bash
 python3 send_qasm_file.py --qasm_file test.qasm
 ```

`test.qasm` is an **OpenQASM** file which is included in `q-aim/qaim-cli`, and contains instructions to setup a basic quantum circuit. 
You can write your own OpenQASM files and send them instead, by specifying the `--qasm_file` argument of `send_qasm_file.py` accordingly. 
For now, if everything works, this script returns a string containing the result of the simulation in the form of the counts of each measured state, and 64-bit encoded version of an image depicting the circuit visually.

## Submitting two-qubit experiment batches

Use the CLI command:
```bash
guest submit-tq-batch
```

By default the CLI submits the experiment definitions stored in `tq_experiments/default_tq_experiment.json`. You can now point the command to any custom experiment definition JSON by passing `--experiment-path` (or `-e`):
```bash
guest submit-tq-batch --experiment-path ./tq_experiments/demo_experiment.json
```

The CLI forwards the provided JSON to the backend and stores the resulting task info file under `experiment_infos/` for later batch result downloads.

## Working with the job queue

`guest list-jobs` queries the scheduler and now filters the response locally to only show entries created by the currently authenticated user (based on the user id embedded in the access token). Use the `--limit` option to control how many of your own submissions are displayed at once.


