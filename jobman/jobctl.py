import argparse
import os
import subprocess
import requests
import yaml

CONFIG_FILE = os.path.expanduser("~/.jobmanrc.yaml")
LOCAL_CONFIG_FILE = os.path.join(os.getcwd(), ".jobmanrc.yaml")


def load_config(global_config=True):
    config_file = CONFIG_FILE if global_config else LOCAL_CONFIG_FILE
    if os.path.exists(config_file):
        with open(config_file, "r") as f:
            return yaml.safe_load(f)
    return {}


def save_config(config, global_config=True):
    config_file = CONFIG_FILE if global_config else LOCAL_CONFIG_FILE
    with open(config_file, "w") as f:
        yaml.safe_dump(config, f)


def get_effective_config():
    global_config = load_config(global_config=True)
    local_config = load_config(global_config=False)
    effective_config = {**global_config, **local_config}  # Local overwrites global
    return effective_config


def get_host():
    config = get_effective_config()
    host = config.get("host", "http://localhost:8000")
    host = host.removeprefix("http://")
    host = host.removeprefix("https://")
    host = "http://" + host
    return host


def set_config(key, value, global_config=True):
    config = load_config(global_config)
    config[key] = value
    save_config(config, global_config)
    scope = "global" if global_config else "local"
    print(f"Set {key} to {value} in {scope} configuration.")


def submit_job(script_path, cpu, memory, gpu, host=None):
    host = host or get_host()
    try:
        with open(script_path) as f:
            code = f.read()
        resp = requests.post(
            f"{host}/submit",
            json={
                "code": code,
                "resources": {"cpu": cpu, "memory": memory, "gpu": gpu},
            },
        )
        resp.raise_for_status()
        print(resp.json())
    except requests.RequestException as e:
        print(f"Error submitting job: {e}")


def list_jobs():
    try:
        resp = requests.get(f"{get_host()}/jobs")
        resp.raise_for_status()
        jobs = resp.json()
        if not jobs:
            print("No running jobs.")
        else:
            print("Running Jobs:")
            for job in jobs:
                print(
                    f"- ID: {job['job_id']}, Status: {job['status']}, Agent: {job['agent']}"
                )
    except requests.RequestException as e:
        print(f"Error fetching jobs: {e}")


def apply_scheduler(config_path):
    print(f"Applying scheduler configuration from {config_path}...")
    try:
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
        print(f"Scheduler configuration: {config}")
    except FileNotFoundError:
        print(f"Configuration file {config_path} not found.")


def run_agent(port):
    print(f"Starting agent on port {port}...")
    subprocess.run(["python", "-m", "jobman.agent", "--port", str(port)], check=True)


def main():
    parser = argparse.ArgumentParser(
        description="JobCTL CLI for managing jobs and services."
    )
    subparsers = parser.add_subparsers(dest="command")

    # Submit command
    submit_parser = subparsers.add_parser("submit", help="Submit a job.")
    submit_parser.add_argument("script", help="Path to the job script.")
    submit_parser.add_argument("--cpu", type=int, default=2, help="Number of CPUs.")
    submit_parser.add_argument("--memory", type=int, default=4096, help="Memory in MB.")
    submit_parser.add_argument("--gpu", type=int, default=1, help="Number of GPUs.")
    submit_parser.add_argument("--host", type=str, help="Scheduler host URL.")

    # Config command
    config_parser = subparsers.add_parser("config", help="Manage configuration.")
    config_parser.add_argument("key", help="Configuration key.")
    config_parser.add_argument("value", nargs="?", help="Configuration value.")
    config_parser.add_argument(
        "--global",
        action="store_true",
        help="Set global configuration.",
        dest="global_config",
    )
    config_parser.add_argument(
        "--local", action="store_true", help="Set local configuration."
    )

    # Agent command
    agent_parser = subparsers.add_parser("agent", help="Manage agents.")
    agent_subparsers = agent_parser.add_subparsers(dest="agent_command")
    agent_run_parser = agent_subparsers.add_parser("run", help="Run the agent service.")
    agent_run_parser.add_argument(
        "--port", type=int, default=5000, help="Port to run the agent on."
    )

    # Scheduler command
    scheduler_parser = subparsers.add_parser("scheduler", help="Manage scheduler.")
    scheduler_subparsers = scheduler_parser.add_subparsers(dest="scheduler_command")
    scheduler_apply_parser = scheduler_subparsers.add_parser(
        "apply", help="Apply a scheduler configuration."
    )
    scheduler_apply_parser.add_argument(
        "config", help="Path to the scheduler configuration file."
    )

    # Jobs command
    jobs_parser = subparsers.add_parser("jobs", help="Manage jobs.")
    jobs_subparsers = jobs_parser.add_subparsers(dest="jobs_command")
    jobs_ls_parser = jobs_subparsers.add_parser("ls", help="List running jobs.")

    args = parser.parse_args()

    if args.command == "submit":
        submit_job(args.script, args.cpu, args.memory, args.gpu, args.host)
    elif args.command == "config":
        if args.value:
            set_config(args.key, args.value, global_config=args.global_config)
        else:
            print(f"{args.key}: {get_effective_config().get(args.key, 'Not set')}")
    elif args.command == "agent" and args.agent_command == "run":
        run_agent(args.port)
    elif args.command == "scheduler" and args.scheduler_command == "apply":
        apply_scheduler(args.config)
    elif args.command == "jobs" and args.jobs_command == "ls":
        list_jobs()


if __name__ == "__main__":
    main()
