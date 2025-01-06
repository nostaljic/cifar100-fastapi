#!/bin/bash
docker-compose up -d
python3.11 -m venv kpepai
source kpepai/bin/activate
pip install -r requirements-noversion.txt
python setup_bucket.py
uvicorn app.main:app --host 0.0.0.0 --port 8000 #& echo $! > uvicorn.pid