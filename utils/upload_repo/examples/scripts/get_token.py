#!/usr/bin/env python3
import requests
import json

response = requests.post(
    'http://136.119.36.216:7272/v3/users/login',
    headers={'Content-Type': 'application/x-www-form-urlencoded'},
    data={'username': 'e.a.gurin@gmail.com', 'password': 'Qazxsw12_'}
)

if response.status_code == 200:
    token = response.json()['results']['access_token']['token']
    with open('/tmp/r2r_token.txt', 'w') as f:
        f.write(token)
    print(f"Token saved. Length: {len(token)}")
else:
    print(f"Error: {response.status_code}")
    print(response.text)
