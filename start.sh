#!/bin/bash
# =============================================================
# DENAI Production Startup Script
# Jalankan ini di server production, BUKAN uvicorn langsung.
# Gunicorn mengelola 4 worker process secara otomatis.
# =============================================================

# Jumlah worker: (2 x jumlah CPU) + 1 adalah patokan umum.
# Droplet saat ini: 1 vCPU / 2GB RAM → maksimal 3 workers aman.
# Jika upgrade ke 2 vCPU / 4GB, ubah ke 5. Jika 4 vCPU / 8GB, ubah ke 9.
WORKERS=${WORKERS:-3}
HOST=${HOST:-0.0.0.0}
PORT=${PORT:-8000}

export ENVIRONMENT=production

echo "Starting DENAI API..."
echo "Workers : $WORKERS"
echo "Bind    : $HOST:$PORT"

exec gunicorn backend.main:app \
    --workers $WORKERS \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind "$HOST:$PORT" \
    --timeout 120 \
    --graceful-timeout 30 \
    --keep-alive 5 \
    --access-logfile - \
    --error-logfile -
