# Migration to enable pgvector extension
# This migration MUST run before 0001_initial to ensure the vector extension is available

from django.db import migrations
from pgvector.django import VectorExtension


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        VectorExtension(),
    ]