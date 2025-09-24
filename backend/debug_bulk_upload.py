#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cv_tailor.settings')
django.setup()

import json
from django.test import Client
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

# Create test user
user = User.objects.create_user(
    email='debug@example.com',
    username='debuguser',
    password='debugpass123'
)

# Get token
token = RefreshToken.for_user(user).access_token

# Create client
client = Client()

# Test data
metadata = {
    'title': 'Debug Upload Project',
    'description': 'Testing bulk upload endpoint',
    'artifact_type': 'project',
    'technologies': ['Python', 'Django'],
    'evidence_links': [
        {
            'url': 'https://github.com/debug/repo',
            'type': 'github',
            'description': 'Source code'
        }
    ]
}

# Test bulk upload
response = client.post(
    '/api/v1/artifacts/upload/',
    {
        'metadata': json.dumps(metadata)
    },
    HTTP_AUTHORIZATION=f'Bearer {token}',
    content_type='multipart/form-data'
)

print(f"Status Code: {response.status_code}")
print(f"Response Content: {response.content.decode()}")

# Clean up
user.delete()