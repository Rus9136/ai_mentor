#!/bin/bash
# Cron job for automatic partition creation
# Runs on the 1st of each month at 00:05
# Crontab entry: 5 0 1 * * /home/rus/projects/ai_mentor/scripts/cron_create_partitions.sh >> /var/log/ai_mentor_partitions.log 2>&1

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "========================================"
echo "Partition Creation Job - $(date)"
echo "========================================"

# Check if backend container is running
if ! docker ps --format '{{.Names}}' | grep -q "ai_mentor_backend_prod"; then
    echo "ERROR: Backend container is not running!"
    exit 1
fi

# Create partitions for next 3 months
docker exec ai_mentor_backend_prod python /app/scripts/create_monthly_partitions.py --months 3

echo ""
echo "Job completed at $(date)"
echo "========================================"
