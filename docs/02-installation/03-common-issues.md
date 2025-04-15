---
id: issues
title: Issues
sidebar_position: 3
---

# Common Installation Issues

### Database connection errors

- Ensure PostgreSQL container is running
- Check database credentials in .env file
- Verify port 5432 is not in use

### Docker issues

- Run `docker compose down -v` to clean up
- Run the `./logs` script inside the docker folder to tail the logs with timestamps
- Ensure ports 8000, 5432, and 6379 are available

### Python environment issues

- Verify Python version: `python --version`
- Ensure pip is updated: `pip install --upgrade pip`
- Check virtual environment activation