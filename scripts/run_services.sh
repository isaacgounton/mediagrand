#!/bin/bash

# Handle SIGTERM for graceful shutdown
cleanup() {
    echo "Received SIGTERM, shutting down..."
    kill ${pids[@]}
    wait
    exit 0
}

trap cleanup SIGTERM

# Bootstrap API key management system on first run
echo "🚀 Bootstrapping API key management system..."
python3 utils/bootstrap_admin.py
echo "✅ Bootstrap completed"

# Array to store background process PIDs
declare -a pids

# Start RQ workers with correct settings
for i in $(seq 1 ${RQ_WORKERS:-2}); do
    python3 utils/start_worker.py & # Use custom worker script to avoid CLI conflicts
    pids+=($!)
done

# Start Gunicorn
gunicorn --bind 0.0.0.0:8080 \
    --workers ${GUNICORN_WORKERS:-2} \
    --timeout ${GUNICORN_TIMEOUT:-300} \
    --worker-class sync \
    --keep-alive 80 \
    --preload \
    app:app &
pids+=($!)

# Wait for all processes
wait