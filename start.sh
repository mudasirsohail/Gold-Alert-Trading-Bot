#!/bin/bash

echo "🚀 Starting Gold Alert Bot..."

# Start Flask keepalive server in background
python -u keepalive.py &
echo "✅ Keepalive server started on port 7860"

# Start main alert script with unbuffered output
echo "✅ Starting Gold Alert script..."
python -u gold_alert.py
