import click
from flask.cli import FlaskGroup


def create_app():
    from app import create_app as c
    return c()


@click.group(cls=FlaskGroup, create_app=create_app)
def cli():
    """Management script for the application."""


@click.command('init-data')
def init_data_command():
    """Seed the database with initial data."""
    from app import create_app
    from app.business import init_data
    from app.models import db

    app = create_app()
    with app.app_context():
        db.create_all()
        init_data()
        click.echo('Initial data seeded successfully.')


cli.add_command(init_data_command)


if __name__ == '__main__':
    cli()
