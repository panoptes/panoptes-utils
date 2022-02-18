import typer

from panoptes.utils.cli import image

app = typer.Typer()
state = {'verbose': False}

app.add_typer(image.app, name="image", help='Process an image.')

if __name__ == "__main__":
    app()
