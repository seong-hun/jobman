import os
import subprocess
import threading

import psutil
from flask import Flask, jsonify, request

app = Flask(__name__)

running_jobs = {}
threads = {}  # Track running threads

@app.route("/status", methods=["GET"])
def status():
    total_cpu = psutil.cpu_count()
    total_mem = psutil.virtual_memory().total
    used_cpu = sum(j["cpu"] for j in running_jobs.values())
    used_mem = sum(j["mem"] for j in running_jobs.values())
    used_gpus = [g for j in running_jobs.values() for g in j["gpu"]]
    all_gpus = list(range(get_gpu_count()))
    free_gpus = list(set(all_gpus) - set(used_gpus))
    return jsonify(
        {
            "cpu_free": total_cpu - used_cpu,
            "mem_free": (total_mem - used_mem) // (1024**2),
            "gpu_free": len(free_gpus),
            "gpu_available": free_gpus,
        }
    )

@app.route("/run", methods=["POST"])
def run():
    data = request.json
    script = data["script"]
    job_id = data.get("job_id", "job")
    path = f"/tmp/jobs/{job_id}.py"
    with open(path, "w") as f:
        f.write(script)

    def worker():
        try:
            subprocess.run(["python", path], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error running job {job_id}: {e}")

    thread = threading.Thread(target=worker)
    thread.start()
    threads[job_id] = thread  # Track the thread
    return jsonify({"status": "started", "job_id": job_id})

def get_free_gpu_memory():
    try:
        output = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=memory.free", "--format=csv,nounits,noheader"]
        )
        return [int(mem) for mem in output.decode().strip().split("\n")]
    except Exception as e:
        print(f"Error fetching GPU memory: {e}")
        return []

def get_gpu_count():
    try:
        output = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=index", "--format=csv,nounits,noheader"]
        )
        return len(output.decode().strip().split("\n"))
    except Exception as e:
        print(f"Error fetching GPU count: {e}")
        return 0

if __name__ == "__main__":
    os.makedirs("/tmp/jobs", exist_ok=True)
    app.run(host="0.0.0.0", port=5000)
