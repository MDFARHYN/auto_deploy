from fastapi import APIRouter, Request, HTTPException
import hmac
import hashlib
import json
import logging
import subprocess  # For executing shell commands
import os, sys
import shutil
from decouple import config
router = APIRouter()


SECRET_KEY = config('SECRET_KEY')

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





#get clone function
def git_clone(repo_url,folder_name):
    clone_path = f"/var/www/{folder_name}"  # Adjust this path as needed

    # Remove existing directory if it exists
    if os.path.exists(clone_path):
        shutil.rmtree(clone_path)

    try:
        subprocess.run(['git', 'clone', repo_url], cwd="/var/www", check=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to clone repository: {e}")



@router.post("/webhook_farhyn", tags=["farhyn_webhook"])
async def farhyn_webhook(request: Request):
    try:
        await verify_signature(request, SECRET_KEY)
        git_clone("git@github.com:MDFARHYN/farhyn2024_portfolio.git","farhyn2024_portfolio")
        payload = await request.json()


        return {"message": "Signature verified successfully.Docker Compose redeployment successful", "data": payload}
    except HTTPException as e:
        return {"error": str(e.detail)}

