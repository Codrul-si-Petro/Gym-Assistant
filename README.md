# Gym Assistant

Gym assistant SaaS intended for gym goers to log their workouts and get feedback through charts and interactive views ( *well at least not yet but sometime!* )

## Contributor set up

You will need the following tools depending on which part of the application you touch:
- [Python](https://www.python.org/downloads/) -- check pyproject.toml to see which version is in use
- [uv](https://docs.astral.sh/uv/) -- ultra fast Python package manager
- pre-commit install -- pre-commit hook to have tests check your code in each commit (less annoying when it fails locally than when it fails in the pull request, trust me)

## To set up your Python environment:

- uv sync  -- syncs your project based on the uv.lock file
- source .venv/bin/activate -- standard .venv activation for your Python virtual environment ( what uv did earlier )

We have two sets of environment variables for now, one which sits in .env.dev and one in .env.prod.
To easily access them based on our needs, there is the load sh script in the utils/ directory.

You can set up this command in your .zshrc/.bashrc or PowerShell dotfile ( though you will have to figure that out yourself ) like below:
```

## Environment Configuration

Load environment variables using the `load django [dev/prod]` command:

```bash
# Development
source utils/load django dev

**Tip:** Add this to your `~/.zshrc` for a shortcut:
```bash
load() {
  source ~/<pathtothelocalrepo>/Gym-Assistant/utils/load "$@"
}
```

Then just use:
```bash
load django dev
```

### Environment Files
You have to ask for them, sorry

## Running the Django server

```bash
load django dev
python manage.py runserver
```


## Database Migrations ( only used for Auth tables which are managed by Django )

```bash
python manage.py makemigrations
python manage.py migrate
```
```bash
# from project root
cd db/
alembic revision --autogenerate -m "your message here"
alembic upgrade head
```

## dbt

```bash
# from project root
cd infra/dbt/transformation
dbt build -s tag:seeds && dbt build -s tag:models
```

## API Documentation

Once the server is running, visit:
- Swagger UI: http://localhost:8000/swagger/

## Services used

The app is hosted on [Render](https://render.com) for free (and most likely it will stay like that)

A cron job on [cron-job.org](https://cron-job.org) pings the server every 14 minutes to keep it alive. (because Render sleeps inactive services using its' free tier)


# Links to service specific documentation:

- [DRF API](https://www.youtube.com/watch?v=dQw4w9WgXcQ)
- [Alembic](db/README.md)
- [dbt](db/transformation/README.md)


# This documentation is a work in progress. If you encounter any issues or there are things that would be nice to be added here, please let the repo owners know.
