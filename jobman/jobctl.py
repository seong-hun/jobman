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


def set_config(key, value, global_config=True):
    config = load_config(global_config)
    config[key] = value
    save_config(config, global_config)
    scope = "global" if global_config else "local"
    print(f"Set {key} to {value} in {scope} configuration.")


def get_config(key, global_config=True):
    config = load_config(global_config)
    return config.get(key, None)


def get_effective_config():
    """Merge global and local configurations, with local taking precedence."""
    global_config = load_config(global_config=True)
    local_config = load_config(global_config=False)
    effective_config = global_config.copy()
    effective_config.update(local_config)  # Local config overwrites global config
    return effective_config


def get_host():
    config = get_effective_config()
    host = config.get("host", "http://localhost:8000")
    host = host.removeprefix("http://")
    host = host.removeprefix("https://")
    host = "http://" + host
    return host


def set_host(host):
    set_config("host", host, global_config=True)
    print(f"Host set to {host}")


def submit(script_path, cpu, memory, gpu, host=None):
    if not host:
        host = get_host()
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


def status(job_id):
    try:
        resp = requests.get(f"{get_host()}/job/{job_id}/status")
        resp.raise_for_status()
        print(resp.json())
    except requests.RequestException as e:
        print(f"Error fetching job status: {e}")


def result(job_id):
    try:
        resp = requests.get(f"{get_host()}/job/{job_id}/result")
        resp.raise_for_status()
        print(resp.json())
    except requests.RequestException as e:
        print(f"Error fetching job result: {e}")


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
                    f"- ID: {job['id']}, Status: {job['status']}, Resources: {job['resources']}"
                )
    except requests.RequestException as e:
        print(f"Error fetching jobs: {e}")


def apply_yaml(file_path):
    with open(file_path, "r") as f:
        documents = yaml.safe_load_all(f)
        for doc in documents:
            kind = doc.get("kind")
            spec = doc.get("spec", {})

            if kind == "Scheduler":
                port = spec.get("port", 8000)
                subprocess.run(["docker-compose", "up", "-d", "scheduler"], check=True)

            elif kind == "Agent":
                name = spec.get("name", "agent")
                port = spec.get("port", 8001)
                subprocess.run(["docker-compose", "up", "-d", name], check=True)

            elif kind == "Job":
                script = spec.get("script")
                resources = spec.get("resources", {})
                cpu = resources.get("cpu", 1)
                memory = resources.get("memory", 512)
                gpu = resources.get("gpu", 0)

                if script:
                    subprocess.run(
                        [
                            "jobctl",
                            "submit",
                            script,
                            "--cpu",
                            str(cpu),
                            "--memory",
                            str(memory),
                            "--gpu",
                            str(gpu),
                        ],
                        check=True,
                    )


def run_agent(port):
    print(f"Starting agent on port {port}...")
    # Logic to start the agent service
    subprocess.run(["python", "-m", "jobman.agent", "--port", str(port)], check=True)


def apply_scheduler(config_path):
    print(f"Applying scheduler configuration from {config_path}...")
    # Logic to apply scheduler configuration
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
        print(f"Scheduler configuration: {config}")
        # Start the scheduler with the given configuration
        subprocess.run(
            ["python", "-m", "jobman.scheduler", "--config", config_path], check=True
        )


def main():
    parser = argparse.ArgumentParser(
        description="JobCTL CLI for managing jobs and services."
    )
    sub = parser.add_subparsers(dest="command")

    p1 = sub.add_parser("submit")
    p1.add_argument("script")
    p1.add_argument("--cpu", type=int, default=2, help="Number of CPUs")
    p1.add_argument("--memory", type=int, default=4096, help="Memory in MB")
    p1.add_argument("--gpu", type=int, default=1, help="Number of GPUs")
    p1.add_argument("--host", type=str, help="Scheduler host URL")

    p2 = sub.add_parser("status")
    p2.add_argument("job_id")

    p3 = sub.add_parser("result")
    p3.add_argument("job_id")

    p4 = sub.add_parser("apply")
    p4.add_argument("file", help="Apply a YAML configuration file.")

    p5 = sub.add_parser("config")
    p5.add_argument("key", help="Configuration key.")
    p5.add_argument("value", nargs="?", help="Configuration value.")
    p5.add_argument(
        "--global",
        action="store_true",
        help="Set global configuration.",
        dest="global_config",
    )
    p5.add_argument("--local", action="store_true", help="Set local configuration.")

    p6 = sub.add_parser("agent")
    agent_sub = p6.add_subparsers(dest="agent_command")

    p6_run = agent_sub.add_parser("run", help="Run the agent service.")
    p6_run.add_argument(
        "--port", type=int, default=5000, help="Port to run the agent on."
    )

    p7 = sub.add_parser("scheduler")
    scheduler_sub = p7.add_subparsers(dest="scheduler_command")

    p7_apply = scheduler_sub.add_parser("apply", help="Apply a scheduler configuration.")
    p7_apply.add_argument("config", type=str, help="Path to the scheduler configuration file.")

    p8 = sub.add_parser("jobs")
    jobs_sub = p8.add_subparsers(dest="jobs_command")

    p8_ls = jobs_sub.add_parser("ls", help="List running jobs.")

    args = parser.parse_args()
    if args.command == "submit":
        submit(args.script, args.cpu, args.memory, args.gpu, args.host)
    elif args.command == "status":
        status(args.job_id)
    elif args.command == "result":
        result(args.job_id)
    elif args.command == "apply":
        if os.path.exists(args.file):
            apply_yaml(args.file)
        else:
            print(f"File {args.file} does not exist.")
    elif args.command == "config":
        if args.value:
            if args.global_config:
                set_config(args.key, args.value, global_config=True)
            elif args.local:
                set_config(args.key, args.value, global_config=False)
            else:
                print("Specify either --global or --local.")
        else:
            if args.global_config:
                value = get_config(args.key, global_config=True)
            elif args.local:
                value = get_config(args.key, global_config=False)
            else:
                print("Specify either --global or --local.")
                exit(1)
            if value is not None:
                print(f"{args.key}: {value}")
            else:
                print(f"Key {args.key} not found.")
    elif args.command == "agent" and args.agent_command == "run":
        run_agent(args.port)
    elif args.command == "scheduler" and args.scheduler_command == "apply":
        apply_scheduler(args.config)
    elif args.command == "jobs" and args.jobs_command == "ls":
        list_jobs()


if __name__ == "__main__":
    main()
