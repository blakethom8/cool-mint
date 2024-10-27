# Alembic
Alembic is a lightweight database migration tool for Python, designed to work with SQLAlchemy, the popular SQL toolkit
and Object-Relational Mapping (ORM) library.
- Version Control Database Schemas: Alembic keeps track of different versions of your database schema, enabling you to upgrade or downgrade to any version as needed.
- Generate Migration Scripts: It can automatically generate migration scripts by comparing your current database schema with your SQLAlchemy models. These scripts describe the changes to be applied, such as adding a new table or modifying a column.
- Apply Migrations Consistently: Using Alembic ensures that all developers on a project apply database changes in the same order and manner, reducing discrepancies between development environments.
- Integrate with CI/CD Pipelines: Alembic can be incorporated into continuous integration and deployment workflows to automate database migrations during deployment.

## Key Components:

- Migration Scripts: Python files that detail specific changes to the database schema.
- Command-Line Interface: Tools to create new migrations, apply existing ones, and manage the migration history.
- Configuration File: Defines connection strings and Alembic settings, typically named alembic.ini.

## GenAI Launchpad
In this project template we've created two custom scripts inside the `app/` folder. 
- makemigrations.sh
- migrate.sh

These scripts are used to run the alembic commands from within the docker container.

### makemigrations.sh
Run this command if you've made any changes to existing database models. It will autogenerate a migration based on the changes.

### migrate.sh
Run this command if want to apply the latest migrations.