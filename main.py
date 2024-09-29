from fastapi import FastAPI, Request, HTTPException
import hmac
import hashlib
import json
import logging
from routers import webhook

app = FastAPI()

app.include_router(webhook.router)


@app.get("/")
async def root():
    return {"message": "Hello Bigger Applications!"}
