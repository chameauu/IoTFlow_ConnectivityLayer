# Poetry Usage Guide

This project uses Poetry for dependency management and virtual environment handling.

## Poetry Commands

### Environment Management

```bash
# Show virtual environment info
poetry env info

# List available environments
poetry env list

# Activate the virtual environment in a new shell
poetry shell

# Run commands in the virtual environment
poetry run python <script>
```

### Dependency Management

```bash
# Install all dependencies
poetry install

# Add a new dependency
poetry add <package-name>

# Add a development dependency
poetry add --group dev <package-name>

# Update dependencies
poetry update

# Show installed packages
poetry show

# Show dependency tree
poetry show --tree
```

### Running the Application

```bash
# Start the development server
poetry run python app.py

# Or use Flask CLI
poetry run flask run

# Initialize database
poetry run python manage.py init-db

# Create a new device
poetry run python manage.py create-device "Device Name"

# Run tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=src
```

### Code Quality Tools

```bash
# Format code with Black
poetry run black .

# Check code style with Flake8
poetry run flake8 src/ tests/

# Sort imports with isort
poetry run isort .

# Run all code quality checks
poetry run black . && poetry run isort . && poetry run flake8 src/ tests/
```

### Database Operations

```bash
# Flask-Migrate commands through Poetry
poetry run flask db init       # Initialize migrations
poetry run flask db migrate    # Create migration
poetry run flask db upgrade    # Apply migrations
poetry run flask db downgrade  # Rollback migrations
```

### Building and Publishing

```bash
# Build the package
poetry build

# Publish to PyPI (if configured)
poetry publish

# Export requirements.txt (if needed for Docker)
poetry export -f requirements.txt --output requirements.txt
```

## VS Code Integration

The project includes VS Code settings that automatically:

- Use the Poetry virtual environment
- Enable code formatting with Black
- Enable import sorting with isort
- Enable linting with Flake8
- Format code on save

## Environment Variables

Create a `.env` file from `.env.example`:

```bash
cp .env.example .env
```

Then edit the `.env` file with your specific configuration.

## Development Workflow

1. **Start development**: `poetry shell` or use `poetry run` prefix
2. **Make changes**: Edit code, Poetry handles the environment
3. **Test changes**: `poetry run pytest`
4. **Format code**: `poetry run black . && poetry run isort .`
5. **Check style**: `poetry run flake8 src/ tests/`
6. **Commit**: Standard git workflow

## Production Deployment

For production, you can:

1. **Export requirements.txt**: `poetry export -f requirements.txt --output requirements.txt`
2. **Use Poetry directly**: Install Poetry on production and use `poetry install --only=main`
3. **Build wheel**: `poetry build` and install the wheel file

## Troubleshooting

### Environment Issues

```bash
# Remove and recreate environment
poetry env remove python
poetry install

# Clear Poetry cache
poetry cache clear pypi --all
```

### Dependency Conflicts

```bash
# Update lock file
poetry lock --no-update

# Force update all dependencies
poetry update
```
