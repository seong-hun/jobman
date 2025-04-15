import argparse
import requests
import yaml
import subprocess
import os

CONFIG_FILE = os.path.expanduser("~/.jobmanrc.yaml")


def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return yaml.safe_load(f)
    return {}


def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        yaml.safe_dump(config, f)


def set_host(host):
    config = load_config()
    config["host"] = host
    save_config(config)
    print(f"Host set to {host}")


def get_host():
    config = load_config()
    return config.get("host", "http://localhost:8000")


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
    p5.add_argument("host", help="Set the default scheduler host URL")

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
        set_host(args.host)


if __name__ == "__main__":
    main()
