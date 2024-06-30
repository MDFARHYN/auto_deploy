# 🚀 Auto Deploy

Auto Deploy is a tool that automatically deploys changes from your local PC to a web server whenever changes are made in your Git repository. 🌐

## 📚 Overview

Auto Deploy simplifies your deployment process by automating the following steps:
1. **Webhook Setup**: Create a Git webhook API.
2. **Notification**: When changes occur in the Git repository, the server is notified.
3. **Clone & Build**: The server clones the Git repository and builds the Docker images.
4. **Deployment**: Docker Compose is used to bring up the updated services.
     ![image](https://github.com/MDFARHYN/auto_deploy/assets/84085024/2dfc7844-b7fc-43a3-b2cd-ce658ea6a460)


## ⚙️ How It Works

1.  **generate Secret**:
    ```python
      import secrets
      secret_key = secrets.token_hex(32)  # Generate a 256-bit (32-byte) hex key
      print(secret_key )
     ```

2. **Setup Webhook**: 
   - Create a webhook in your Git repository settings to notify the server of changes.
   - click on settings of your git repo
       ![image](https://github.com/MDFARHYN/auto_deploy/assets/84085024/607c83cd-1438-4cf7-a05c-ea7aec5aa52a)
   - click on Webhook
       ![image](https://github.com/MDFARHYN/auto_deploy/assets/84085024/33811ea8-0fd4-43df-aab5-cbb93f101ce5)
   - click on add Webhook
      ![image](https://github.com/MDFARHYN/auto_deploy/assets/84085024/19c3da49-bdd4-4e3a-b7c0-c51769f82a9a)
   - give your api url, choose content type application/json, give the secret
       ![image](https://github.com/MDFARHYN/auto_deploy/assets/84085024/fc4a1f00-20b9-4186-a927-603e22f737fb)


2. **Required Files**:
   - Ensure `docker-compose.yml` and `Dockerfile` are present in the root of your project.

3. **Notification**:
   - When a change is detected, the webhook notifies the server.

4. **Cloning and Building**:
   - The server clones the updated Git repository.
   - Docker images are built using the provided Docker files.

## 🛠️ Installation

1. **Install FastAPI**:
   - On your server, set up a virtual environment and install requirements.txt:
   ```bash
     pip install -r requirements.txt
     ```
2. **give the folder path**:

      ```
         background_tasks.add_task(git_clone, "git repo url", "/var/www/git_repo_name") 
      ```
      
      ```
         background_tasks.add_task(docker_compose, "/var/www/root_folder_name") #root folder name where docker file is located
      ```

## 📋 Code Explanation

Here's a snippet of the main code to help you understand how it works:

```python

SECRET_KEY = config('SECRET_KEY') # your secret key 

@log_function
def git_clone(repo_url, folder_name):
    clone_path = f"/var/www/{folder_name}" 
    if os.path.exists(clone_path):
        shutil.rmtree(clone_path)

    try:
        subprocess.run(['git', 'clone', repo_url], cwd="/var/www", check=True) #clone the repo to /var/www/
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to clone repository: {e}")

@log_function
def docker_compose(folder_name):
    try:
        subprocess.run(['docker', 'compose', "build", "--no-cache"], cwd=folder_name, check=True)
        subprocess.run(['docker', 'compose', "up", "-d"], cwd=folder_name, check=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to docker compose: {e}")

@router.post("/webhook_farhyn", tags=["farhyn_webhook"])
async def farhyn_webhook(request: Request, background_tasks: BackgroundTasks):
    try:
        logging.info("Received webhook request")
        await verify_signature(request, SECRET_KEY)
        background_tasks.add_task(git_clone, "git repo url", "/var/www/git_repo_name")  
        background_tasks.add_task(docker_compose, "/var/www/root_folder_name") #root folder name where docker file is located  
        payload = await request.json()
        logging.info(f"Webhook processed successfully, payload: {payload}")

        return {"message": "Signature verified successfully", "data": payload}
    except HTTPException as e:
        logging.error(f"Exception occurred for /webhook_farhyn api: {str(ex)}")
        return {"error": str(e.detail)}
