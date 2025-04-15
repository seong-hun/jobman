# Light Job Manager

Light Job Manager is a lightweight job management system designed to manage and execute distributed jobs efficiently. It provides a simple CLI and REST API for submitting, monitoring, and retrieving job results.

## Features
- Submit Python scripts as jobs to distributed agents.
- Monitor job status and resource usage.
- Retrieve job results upon completion.
- Lightweight and easy to set up.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/seong-hun/jobman.git
   cd jobman
   ```

2. Install the package in editable mode:
   ```bash
   pip install -e .
   ```

## Usage

### CLI

The `jobctl` CLI tool is used to interact with the job manager.

#### Apply a YAML Configuration
```bash
jobctl apply <config_file>
```
Use this command to apply a YAML configuration file that defines schedulers, agents, and jobs.

#### Submit a Job
```bash
jobctl submit <script_path> --cpu <num_cpus> --memory <memory_mb> --gpu <num_gpus>
```

#### Check Job Status
```bash
jobctl status <job_id>
```

#### Retrieve Job Result
```bash
jobctl result <job_id>
```

### YAML Configuration

You can define schedulers, agents, and jobs in a YAML file and apply them using the `jobctl apply` command. Below is an example configuration:

```yaml
kind: Scheduler
spec:
  port: 8000

---
kind: Agent
spec:
  name: agent1
  port: 8001

---
kind: Job
spec:
  script: "example.py"
  resources:
    cpu: 2
    memory: 1024
    gpu: 1
```

Save this configuration to a file (e.g., `config.yaml`) and apply it:
```bash
jobctl apply config.yaml
```

### REST API

The job manager also provides a REST API for programmatic access.

#### Submit a Job
```http
POST /submit
Content-Type: application/json

{
  "code": "<Python script code>",
  "resources": {
    "cpu": <num_cpus>,
    "memory": <memory_mb>,
    "gpu": <num_gpus>
  }
}
```

#### Check Job Status
```http
GET /job/<job_id>/status
```

#### Retrieve Job Result
```http
GET /job/<job_id>/result
```

## Project Structure
- `jobman/agent.py`: Agent service for executing jobs.
- `jobman/jobctl.py`: CLI tool for interacting with the job manager.
- `jobman/scheduler.py`: Scheduler service for managing job submissions and resource allocation.
- `pyproject.toml`: Project configuration file.

## License
This project is licensed under the MIT License. See the LICENSE file for details.

## Contributing
Contributions are welcome! Please open an issue or submit a pull request on GitHub.
