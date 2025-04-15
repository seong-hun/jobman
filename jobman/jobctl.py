import argparse
import requests

SCHEDULER_URL = "http://central-scheduler:6000"

def submit(script_path, cpu, memory, gpu):
    try:
        with open(script_path) as f:
            code = f.read()
        resp = requests.post(
            f"{SCHEDULER_URL}/submit",
            json={"code": code, "resources": {"cpu": cpu, "memory": memory, "gpu": gpu}},
        )
        resp.raise_for_status()
        print(resp.json())
    except requests.RequestException as e:
        print(f"Error submitting job: {e}")

def status(job_id):
    try:
        resp = requests.get(f"{SCHEDULER_URL}/job/{job_id}/status")
        resp.raise_for_status()
        print(resp.json())
    except requests.RequestException as e:
        print(f"Error fetching job status: {e}")

def result(job_id):
    try:
        resp = requests.get(f"{SCHEDULER_URL}/job/{job_id}/result")
        resp.raise_for_status()
        print(resp.json())
    except requests.RequestException as e:
        print(f"Error fetching job result: {e}")

def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command")

    p1 = sub.add_parser("submit")
    p1.add_argument("script")
    p1.add_argument("--cpu", type=int, default=2, help="Number of CPUs")
    p1.add_argument("--memory", type=int, default=4096, help="Memory in MB")
    p1.add_argument("--gpu", type=int, default=1, help="Number of GPUs")

    p2 = sub.add_parser("status")
    p2.add_argument("job_id")

    p3 = sub.add_parser("result")
    p3.add_argument("job_id")

    args = parser.parse_args()
    if args.command == "submit":
        submit(args.script, args.cpu, args.memory, args.gpu)
    elif args.command == "status":
        status(args.job_id)
    elif args.command == "result":
        result(args.job_id)

if __name__ == "__main__":
    main()
