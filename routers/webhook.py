from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
import hmac
import hashlib
import subprocess
import os
import shutil
from decouple import config
from loguru import logger

router = APIRouter()

# Initialize the SECRET_KEY from environment or config file
SECRET_KEY = config('SECRET_KEY')

# Set up loguru to log into a file
LOG_FILE = "fast_api_app.log"
logger.add(LOG_FILE, rotation="500 MB")


# Verifies the webhook signature
async def verify_signature(request: Request, secret_key: str):
    signature_header = request.headers.get('X-Hub-Signature-256')
    if not signature_header:
        raise HTTPException(status_code=400, detail="Missing X-Hub-Signature-256 header")

    try:
        algorithm, received_signature = signature_header.split('=')
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid X-Hub-Signature-256 header format")

    if algorithm != 'sha256':
        raise HTTPException(status_code=400, detail="Unsupported signature algorithm")

    try:
        payload = await request.body()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read request body: {str(e)}")

    mac = hmac.new(secret_key.encode(), msg=payload, digestmod=hashlib.sha256)
    expected_signature = mac.hexdigest()

    if not hmac.compare_digest(expected_signature, received_signature):
        raise HTTPException(status_code=400, detail="Invalid signature")


# Git clone function
def git_clone(repo_url: str, folder_name: str):
    clone_path = f"/var/www/{folder_name}"  # Adjust this path as needed

    # Remove existing directory if it exists
    if os.path.exists(clone_path):
        shutil.rmtree(clone_path)
        logger.info(f"Removed existing directory: {clone_path}")

    try:
        result = subprocess.run(['git', 'clone', repo_url, folder_name], cwd="/var/www", capture_output=True, text=True, check=True)
        logger.info(f"Git clone output: {result.stdout}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Git clone failed: {e.stderr}")
        raise RuntimeError(f"Failed to clone repository: {e.stderr}")


# Docker compose function with logging of stdout/stderr
def docker_compose(folder_name: str):
    try:
        # Run docker compose build
        build_result = subprocess.run(['docker', 'compose', 'build', '--no-cache'], cwd=f"/var/www/{folder_name}", capture_output=True, text=True, check=True)
        logger.info(f"Docker Compose build output: {build_result.stdout}")
        if build_result.stderr:
            logger.warning(f"Docker Compose build error: {build_result.stderr}")
        
        # Run docker compose up
        up_result = subprocess.run(['docker', 'compose', 'up', '-d'], cwd=f"/var/www/{folder_name}", capture_output=True, text=True, check=True)
        logger.info(f"Docker Compose up output: {up_result.stdout}")
        if up_result.stderr:
            logger.warning(f"Docker Compose up error: {up_result.stderr}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to docker compose: {e.stderr}")
        raise RuntimeError(f"Failed to docker compose: {e.stderr}")


# Docker prune to clean up unused resources
def docker_prune():
    try:
        prune_result = subprocess.run(['docker', 'system', 'prune', '--volumes', '-f'], capture_output=True, text=True, check=True)
        logger.info(f"Docker prune output: {prune_result.stdout}")
        if prune_result.stderr:
            logger.warning(f"Docker prune error: {prune_result.stderr}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to prune Docker resources: {e.stderr}")
        raise RuntimeError(f"Failed to prune Docker resources: {e.stderr}")



@router.post("/webhook_farhyn", tags=["farhyn_webhook"])
async def farhyn_webhook(request: Request, background_tasks: BackgroundTasks):
    try:
         # Clear the log file (delete it if it exists)
        if os.path.exists(LOG_FILE):
            os.remove(LOG_FILE)
            logger.info(f"Cleared log file: {LOG_FILE}")
        await verify_signature(request, SECRET_KEY)

        # Parse the payload to get repository URL and folder name
        payload = await request.json()
        repo_url = payload.get('repository_url')  # You should replace 'repository_url' with the actual key used in the webhook payload
        folder_name = payload.get('folder_name')  # Ensure the folder_name is passed in the payload

        if not repo_url or not folder_name:
            raise HTTPException(status_code=400, detail="Missing repository URL or folder name in payload")

        # Add tasks to background tasks
        background_tasks.add_task(git_clone, repo_url, folder_name)
        background_tasks.add_task(docker_compose, folder_name)
        background_tasks.add_task(docker_prune)  # Clean up Docker resources after the tasks

        logger.info(f"Webhook payload processed for repo: {repo_url}, folder: {folder_name}")
        return {"message": "Signature verified successfully and tasks scheduled", "data": payload}

    except HTTPException as e:
        logger.error(f"HTTP Exception occurred: {str(e.detail)}")
        return {"error": str(e.detail)}

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
