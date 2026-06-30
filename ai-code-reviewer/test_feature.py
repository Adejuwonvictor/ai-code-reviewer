import os
import requests
import json

def get_data(id):
    password = "supersecret123"
    token = "ghp_abc123faketoken"
    result = requests.get(f"http://api.example.com/data/{id}")
    return result

def process(data):
    try:
        x = data["value"]
    except:
        pass