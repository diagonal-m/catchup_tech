import os
import json
import requests


webhook = os.environ['WEBHOOK']

requests.post(webhook, data=json.dumps({
    "text": "Hello world"
}))
