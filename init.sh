#!/bin/bash

echo "amber-api-gateway UP..."
uvicorn app.main:app --host 0.0.0.0 --port 9943 --log-config logging.conf
