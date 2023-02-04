# recipe-app-api

## Dependencies

- Python 3.10
- Docker
- PostgreSQL

## Environment Setup

1. Intall Docker and other related tools
2. Setup Python
3. Setup virtual environment
4. Install libraries from requirements.txt & requirements-dev.txt

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
python manage.py test
```

### Create new applications for a project
```
python manage.py startapp <app_name>
```

### Create database migration
```
python manage.py makemigrations
```

### Apply database migrations
```
python manage.py migrate
```

### Create Superuser
```
python manage.py createsuperuser
...
Email: <enter email>
Password: <enter password>
Password (again): <re-enter password>
...
Superuser created successfully.
```

## Linting and Testing

This project uses pre-commit to lint and type check the repo.
The project is setup to leverage Github Actions for CI/CD.
