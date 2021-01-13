import os

import click_spinner
import docker
import docker.errors
import typer

app = typer.Typer()


@app.command()
def run(
        directory: str = typer.Argument('/var/panoptes/panoptes-utils/'),
        image_tag: str = typer.Argument('panoptes-utils:testing'),
        log_dir: str = typer.Option('logs',
                                    help='Location to stir log files, relative to project root.')
):
    """Run the test suite."""
    client = docker.from_env()

    typer.secho(f'Log files will be output to {log_dir}')
    os.makedirs(log_dir, exist_ok=True)
    mount_volumes = {
        os.path.realpath(log_dir): {'bind': '/var/panoptes/logs', 'mode': 'rw'},
        os.path.realpath('.'): {'bind': '/var/panoptes/panoptes-utils', 'mode': 'rw'}
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
                                      volumes=mount_volumes,
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
