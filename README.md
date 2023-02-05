# home-owner-insurance

## Dependencies

- Python 3.10
- Docker
- PostgreSQL

## Environment Setup

1. Install Docker Desktop and other related tools
   - https://docs.docker.com/desktop/
2. Setup Python
   - https://www.python.org/downloads/release/python-3109/
3. Setup virtual environment
   - https://github.com/pyenv/pyenv
   - https://docs.python.org/3.10/library/venv.html
4. Install libraries from requirements.txt & requirements-dev.txt
   - `pip install -r requirements.txt requirements-dev.txt`

## Docker/Docker Compose

- Upon updating the Dockerfile, be sure to build the Docker container
```
docker-compose build
```
- Run app through Docker
```
docker-compose up
```
- Tear down any artifacts from Docker
```
docker-compose down
```

## Django Admin Commands

### Create new project
```
django-admin startproject <project_name> .
```

### Run Tests
```
docker-compose run --rm app sh -c "python manage.py test"
```
