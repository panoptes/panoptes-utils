import typer

import tests

app = typer.Typer()
app.add_typer(tests.app, name='tests')

if __name__ == "__main__":
    app()
