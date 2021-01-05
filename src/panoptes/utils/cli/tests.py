import click_spinner
import docker
import docker.errors
import typer
from dotenv import dotenv_values

app = typer.Typer()


@app.command()
def run(
        directory: str = typer.Argument('/var/panoptes/panoptes-utils/'),
        image_tag: str = typer.Argument('panoptes-utils:testing'),
        env_path: str = typer.Argument('/var/panoptes/panoptes-utils/tests/env'),
        log_dir: str = typer.Option(None)
):
    """Run the test suite."""
    client = docker.from_env()

    env_vars = dotenv_values(dotenv_path=env_path)
    if log_dir is not None:
        typer.echo(f'Using {log_dir} for logs')
        env_vars['PANLOG'] = log_dir
    else:
        log_dir = env_vars['PANLOG']

    typer.secho(f'Log files will be output to {log_dir}')
    mount_volumes = {
        log_dir: {'bind': '/var/panoptes/logs', 'mode': 'rw'}
    }

    try:
        client.images.get(image_tag)
    except docker.errors.ImageNotFound:
        typer.secho('Building test image (may take a few minutes)', fg=typer.colors.RED)
        with click_spinner.spinner():
            build_test_image(directory, image_tag, docker_client=client)

    typer.echo(f'Starting testing on docker containers from {directory} with {image_tag}')
    container = client.containers.run(image_tag,
                                      name='panoptes-utils-testing',
                                      detach=True,
                                      auto_remove=True,
                                      environment=env_vars,
                                      volumes=mount_volumes
                                      )

    for line in container.logs(stream=True, follow=True):
        typer.secho(line.decode(), nl=False)


def build_test_image(context_dir, image_tag, dockerfile=None, docker_client=None):
    """Builds the docker image used for testing."""
    docker_client = docker_client or docker.from_env()
    dockerfile = dockerfile or f'{context_dir}/tests/Dockerfile'

    test_image, build_logs = docker_client.images.build(
        path=context_dir,
        tag=image_tag,
        dockerfile=dockerfile
    )

    return test_image
