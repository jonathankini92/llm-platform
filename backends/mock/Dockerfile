# =============================================================================
# Dockerfile for the Mock Backend
# =============================================================================
# A Dockerfile describes how to build a Docker image.
# An image = a snapshot of a system with our application installed.

# -----------------------------------------------------------------------------
# 1. BASE IMAGE
# -----------------------------------------------------------------------------
# We start from an official Python image, slim version (lightweight).
# "slim" = without compilation tools, smaller (~150MB vs ~1GB)
FROM python:3.11-slim

# -----------------------------------------------------------------------------
# 2. WORKING DIRECTORY
# -----------------------------------------------------------------------------
# Creates the /app folder in the container and positions itself there.
# All subsequent commands will run from /app.
WORKDIR /app

# -----------------------------------------------------------------------------
# 3. DEPENDENCY INSTALLATION
# -----------------------------------------------------------------------------
# We first copy requirements.txt ALONE, then install.
# Why? Docker caches each step.
# If the code changes but not requirements.txt, Docker reuses the cache
# for dependencies → faster build.

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --no-cache-dir: don't save pip cache (lighter image)

# -----------------------------------------------------------------------------
# 4. CODE COPY
# -----------------------------------------------------------------------------
# Copy all contents of the current directory to /app
COPY . .

# -----------------------------------------------------------------------------
# 5. EXPOSED PORT
# -----------------------------------------------------------------------------
# Documents that the container listens on port 8000.
# This is informational - you still need to map the port at launch.
EXPOSE 8000

# -----------------------------------------------------------------------------
# 6. STARTUP COMMAND
# -----------------------------------------------------------------------------
# The command executed when the container starts.
# Launches uvicorn (ASGI server) with our FastAPI application.
#
# --host 0.0.0.0: listen on all interfaces (required in Docker)
# --port 8000   : listening port
# main:app      : main.py file, app variable (our FastAPI())
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
