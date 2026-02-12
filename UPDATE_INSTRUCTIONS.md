# How to Update Your Container with Visualization Features

The visualization button won't appear until you rebuild the Docker container with the updated code.

## Quick Update (Recommended)

```bash
# 1. Stop and remove the old container
docker-compose down

# 2. Rebuild the image with the new code
docker-compose build --no-cache

# 3. Start the container
docker-compose up -d

# 4. View logs to confirm it's running
docker-compose logs -f
```

## Verify It's Working

1. Go to http://localhost:8000
2. Run a discovery with demo device (e.g., IP: `192.168.1.1`)
3. After discovery completes, scroll down past the summary
4. You should see a purple button: **🌐 View Interactive Network Diagram**

## Alternative: Manual File Update (If rebuild fails)

If you can't rebuild for some reason, you can manually copy files:

```bash
# Make the update script executable
chmod +x update_container.sh

# Run the update script
./update_container.sh
```

## Troubleshooting

**Button still not showing?**
- Check that `visualization` variable is being passed to template
- Look at Flask logs: `docker-compose logs -f`
- Make sure `/tmp` directory in container is writable

**Container won't start?**
- Check logs: `docker-compose logs`
- Ensure ports 8000 and 8001 are not in use
- Try: `docker-compose down -v` then rebuild

## What Changed?

These files were updated to add visualization:
- `app/visualizer.py` - New visualization module
- `app/app.py` - Generates visualization after discovery
- `templates/index.html` - Adds the visualization button
