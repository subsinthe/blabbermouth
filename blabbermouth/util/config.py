import os

import jinja2
import yaml


def load_config(config_directory, env_file, config_env_overrides=None):
    if config_env_overrides is None:
        config_env_overrides = {}

    with open(os.path.join(config_directory, env_file)) as env_fd:
        config_env = yaml.load(env_fd)

    for key, value in config_env_overrides.items():
        config_env[key] = value

    jinja_env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(config_directory),
        trim_blocks=True,
        lstrip_blocks=True,
    )

    sources = (
        entry
        for entry in os.listdir(config_directory)
        if entry != env_file
        and os.path.isfile(os.path.join(config_directory, entry))
    )

    result = config_env.copy()

    for source in sources:
        template = jinja_env.get_template(source)
        yaml_config = template.render(config_env)
        result[source.split(".")[0]] = yaml.load(yaml_config)

    return result
