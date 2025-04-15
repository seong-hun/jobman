import uuid
import requests
import itertools
from flask import Flask, jsonify, request

app = Flask(__name__)
AGENTS = [{"name": "worker1", "url": "http://10.0.0.1:5000"}]
JOBS = {}
agent_cycle = itertools.cycle(AGENTS)  # Round-robin agent selection

def choose_agent():
    for _ in range(len(AGENTS)):
        agent = next(agent_cycle)
        try:
            r = requests.get(agent["url"] + "/status", timeout=1)
            r.raise_for_status()
            return agent
        except requests.RequestException as e:
            print(f"Agent {agent['name']} is unavailable: {e}")
    return None

def choose_agent_for_job(job):
    for _ in range(len(AGENTS)):
        agent = next(agent_cycle)
        try:
            status = requests.get(agent["url"] + "/status", timeout=1).json()
            if (
                status["cpu_free"] >= job["resources"]["cpu"]
                and status["mem_free"] >= job["resources"]["memory"]
                and status["gpu_free"] >= job["resources"]["gpu"]
            ):
                return agent
        except requests.RequestException as e:
            print(f"Error checking agent {agent['name']} status: {e}")
    return None

@app.route("/submit", methods=["POST"])
def submit():
    code = request.json["code"]
    job_id = str(uuid.uuid4())
    agent = choose_agent()
    if not agent:
        return jsonify({"error": "No available agent"}), 503
    try:
        resp = requests.post(
            agent["url"] + "/run", json={"script": code, "job_id": job_id}, timeout=5
        )
        resp.raise_for_status()
        JOBS[job_id] = {"agent": agent["url"], "status": "submitted"}
        return jsonify({"job_id": job_id})
    except requests.RequestException as e:
        print(f"Error submitting job to agent {agent['name']}: {e}")
        return jsonify({"error": "Failed to submit job"}), 500

@app.route("/job/<job_id>/status")
def job_status(job_id):
    job = JOBS.get(job_id)
    if not job:
        return jsonify({"error": "not found"}), 404
    try:
        resp = requests.get(job["agent"] + f"/status?id={job_id}", timeout=5)
        resp.raise_for_status()
        return jsonify(resp.json())
    except requests.RequestException as e:
        print(f"Error fetching status for job {job_id}: {e}")
        return jsonify({"error": "Failed to fetch job status"}), 500

@app.route("/job/<job_id>/result")
def job_result(job_id):
    job = JOBS.get(job_id)
    if not job:
        return jsonify({"error": "not found"}), 404
    try:
        resp = requests.get(job["agent"] + f"/result?id={job_id}", timeout=5)
        resp.raise_for_status()
        return jsonify(resp.json())
    except requests.RequestException as e:
        print(f"Error fetching result for job {job_id}: {e}")
        return jsonify({"error": "Failed to fetch job result"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=6000)
