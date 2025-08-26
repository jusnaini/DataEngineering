# What is Docker?
Docker is a platform that allows building, running, and managing applications inside **containers**.  
A container is a lightweight, isolated environment that includes everything needed by an application (code, runtime, libraries, and dependencies).  

---

# Why Docker is Useful
- **Consistency**: Solves the “it works on my machine” problem by ensuring containers behave the same everywhere.  
- **Isolation**: Each container runs in its own environment, avoiding dependency conflicts.  
- **Portability**: Containers can run on any system with Docker installed (local, cloud, or server).  
- **Reproducibility**: Environments can be easily shared and reproduced using Dockerfiles and images.  

---

# Installing Docker
Follow the official installation guide based on the operating system:  
👉 [Get Docker](https://docs.docker.com/get-docker/)  

---

# Checking Docker Installation
```bash
# Check Docker version
docker --version

# Run a test container
docker run hello-world
```
---

# A Super Simple Example with Python

Let’s create a basic Docker container with Python.

```bash
# Start a container with Python 3.9 (Docker will download it if not available locally)
docker run -it python:3.9
```
This opens a Python REPL. Try:

```python
import sys
print(sys.version)
```
**Python REPL** stands for **Read–Eval–Print Loop**.

It is the interactive shell that comes with Python.
- Read → takes the command that is typed in 
- Eval → evaluates (executes) the command
- Print → shows the result
- Loop → waits for the next command

Example:

```markdown
$ python
Python 3.9.20 (default, Aug 21 2025, 10:00:00) 
[GCC 11.2.0] on linux
Type "help", "copyright", "credits" or "license" for more information.
>>> 2 + 3
5
>>> print("hello")
hello
>>> import sys; sys.version
'3.9.20 (default, Aug 21 2025, 10:00:00) \n[GCC 11.2.0]'


The >>> is the REPL prompt.
It’s called REPL because the shell continuously reads commands, evaluates them, prints the result, and loops again.
```

So, when running:

```bash
docker run -it python:3.9
```
the container opens directly into the Python REPL (instead of bash).

## Opening a Bash Shell in the Container

Instead of entering Python directly, a bash shell can be opened inside the container:

```bash
docker run -it --entrypoint=bash python:3.9
```
Inside the container:

```bash
pip list
pip install pandas
python -c "import pandas as pd; print(pd.__version__)"
```


**⚠️ Note:**

* Packages installed in a running container will not persist if the container is stopped and restarted.
* This is because Docker containers are ephemeral by default (they don’t save state by default).
* To preserve installed dependencies, a Dockerfile is required.


## Dockerfile Example

Create a file called `Dockerfile`:

```Dockerfile
FROM python:3.9

RUN pip install pandas

# ENTRYPOINT ["bash"]   # could also be used
CMD ["bash"]

```

## Build and Run the Image
```bash
# Build the image in current directory (.) and name it test:pandas
docker build -t test:pandas .

# Run the built image in interactive mode
docker run -it test:pandas
```

Now, inside the container shell:

```bash
python -c "import pandas as pd; print(pd.__version__)"
```

✅ This time `pandas` is always available, because it was baked into the Docker image.


# Summary
1. Install Docker (if not already installed).
2. Verify Docker installation:

    ```bash
    docker --version
    docker run hello-world

    ```
3. Run Python in a container:

    ```bash
    docker run -it python:3.9
    ```
4. Observe that manually installed packages do not persist across runs.

5. Use a `Dockerfile` to create a reproducible environment with dependencies.

6. Build and run the custom image:

    ```bash
    docker build -t test:pandas .
    docker run -it test:pandas
    ```


# Common Use Cases of Docker

- **`Local Experiments and Development`**
  Quickly set up isolated environments for testing new tools, frameworks, or code without polluting the local machine.  

- **`Integration Tests / CI/CD Pipelines`**  
  Containers provide consistent environments for automated testing and continuous integration, ensuring that builds and tests run reliably across different systems.  

- **`Batch Jobs`**  
  Containers are commonly used for running scheduled or one-off jobs (e.g., ETL tasks, data pipelines).  
  - Examples: AWS Batch, Kubernetes Jobs.  
  - (Detailed orchestration is outside the scope of this note.)  

- **`Big Data and Distributed Computing`**  
  Platforms like **Apache Spark** can run inside containers for scalable data processing.  

- **`Serverless and Microservices`**  
  Containers often serve as the underlying technology for serverless platforms and microservice architectures.  
  - Example: AWS Lambda uses container images for custom runtimes.  

---

📌 **Observation**:  
Containers have become a standard unit of deployment in modern software engineering.  
They are used across local development, testing, data engineering, machine learning, and production systems. In short: **containers are everywhere**.  

# Common Docker Commands

### Image Management
```bash
# List all images on the system
docker images

# Pull an image from Docker Hub
docker pull python:3.9

# Remove an image
docker rmi image_name:tag
```

### Container Management
```bash
# Run a container interactively
docker run -it python:3.9

# Run a container with a custom name
docker run -it --name my_python python:3.9

# Start a container in the background (detached mode)
docker run -d nginx

# List running containers
docker ps

# List all containers (including stopped ones)
docker ps -a

# Stop a running container
docker stop <container_id>

# Remove a container
docker rm <container_id>


# List all volumes
docker volume ls

# Inspect a specific volume
docker volume inspect <volume_name>

#Remove a volume
docker volume rm <volume_name>
```

### Container Access
```bash
# Access a running container with bash
docker exec -it <container_id> bash

# Attach to a container's shell
docker attach <container_id>
```
### Building Custom Images
```bash
# Build an image from a Dockerfile
docker build -t my_image:latest .

# Run a container from the custom image
docker run -it my_image:latest
```

### Logs and Monitoring
```bash
# View container logs
docker logs <container_id>

# Follow logs in real-time
docker logs -f <container_id>

# Inspect container details (env vars, mounts, etc.)
docker inspect <container_id>
```

### Cleaning Up
```bash
# Remove all stopped containers
docker container prune

# Remove unused images
docker image prune

# Remove everything unused (containers, networks, images)
docker system prune

```

**📌 Observation:**

The most frequently used workflow is usually:
- `docker pull` (get the image)
- `docker run` (start a container)
- `docker ps` (check running containers)
- `docker exec` (interact inside container)
- `docker build `(custom image from Dockerfile)
- `docker logs` (debugging)
- `docker system prune` (clean up space)