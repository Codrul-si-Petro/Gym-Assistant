# Gym Assistant

Gym workout tracking assistant with Django REST API and dbt for data transformations.

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) 
- PostgreSQL

Install uv:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Setup

# Create venv and install dependencies
uv sync

# Activate virtual environment
source .venv/bin/activate

# Install pre-commit hooks
pre-commit install
```

## Environment Configuration

Load environment variables using the `load` command:

```bash
# Development
source utils/load django dev

**Tip:** Add this to your `~/.zshrc` for a shortcut:
```bash
load() {
  source ~/personal/Gym-Assistant/utils/load "$@"
}
```

Then just use:
```bash
load django dev
```

### Environment Files

## Running the Server

```bash
load django dev
python manage.py runserver
```

## Code Quality

### Linting (Ruff)

```bash
# Check for issues
ruff check .

# Auto-fix issues
ruff check . --fix

# Format code
ruff format .
```

### Type Checking (mypy)

```bash
mypy .
```

### Pre-commit Hooks

Pre-commit runs ruff and mypy automatically before each commit:

```bash
# Install hooks (one-time)
pre-commit install

# Run manually on all files
pre-commit run --all-files
```

## Database Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

## dbt (Data Transformations)

```bash
cd infra/dbt/transformation
dbt run
dbt test
```

## API Documentation

Once the server is running, visit:
- Swagger UI: http://localhost:8000/swagger/
- ReDoc: http://localhost:8000/redoc/
