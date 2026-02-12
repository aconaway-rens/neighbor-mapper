#!/bin/bash

# Script to update the running Docker container with new code changes
# This updates the visualization features without rebuilding the entire container

echo "🔄 Updating Neighbor Mapper container with visualization features..."

# Check if container is running
if ! docker ps | grep -q neighbor-mapper; then
    echo "❌ Error: neighbor-mapper container is not running"
    echo "Please start it first with: docker-compose up -d"
    exit 1
fi

# Copy updated files to container
echo "📦 Copying updated files to container..."

docker cp app/visualizer.py neighbor-mapper:/app/app/visualizer.py
docker cp app/app.py neighbor-mapper:/app/app/app.py
docker cp templates/index.html neighbor-mapper:/app/templates/index.html

# Restart the Flask app inside the container
echo "🔄 Restarting Flask application..."
docker exec neighbor-mapper pkill -f "python app.py" || true
sleep 2

echo "✅ Update complete!"
echo ""
echo "The visualization feature is now active."
echo "Visit http://localhost:8000 and run a discovery to see it!"
echo ""
echo "After discovery completes, you'll see a purple button:"
echo "🌐 View Interactive Network Diagram"
