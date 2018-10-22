#!/usr/bin/env python
# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
import click
import os
import sys
import toml
import json

THIS_DIR = os.path.split(os.path.realpath(__file__))[0]
ROOT_DIR = os.path.join(THIS_DIR, os.pardir)

FILENAME_TOML = 'pyproject.toml'
PATH_TOML = os.path.join(ROOT_DIR, FILENAME_TOML)

FILENAME_REQUIREMENTS = 'setup.json'
PATH_REQUIREMENTS = os.path.join(ROOT_DIR, FILENAME_REQUIREMENTS)

FILENAME_ENVIRONMENT = 'environment.yml'
PATH_ENVIRONMENT = os.path.join(ROOT_DIR, FILENAME_ENVIRONMENT)

dir_path = os.path.dirname(os.path.realpath(__file__))


@click.group()
def cli():
    pass

@click.command('version')
def validate_pyproject():
    """
    Ensure that the version of reentry in setup.json and pyproject.toml are identical
    """

    reentry_requirement = None
    with open(PATH_REQUIREMENTS, 'r') as info:
        setup_json = json.load(info)

    for requirement in setup_json['install_requires']:
        if 'reentry' in requirement:
            reentry_requirement = requirement
            break

    if reentry_requirement is None:
        click.echo('Could not find the reentry requirement in {}'.format(FILENAME_REQUIREMENTS), err=True)
        sys.exit(1)

    try:
        with open(PATH_TOML, 'r') as handle:
            toml_string = handle.read()
    except IOError as exception:
        click.echo('Could not read the required file: {}'.format(PATH_TOML), err=True)
        sys.exit(1)

    try:
        parsed_toml = toml.loads(toml_string)
    except Exception as exception:
        click.echo('Could not parse {}: {}'.format(PATH_TOML, exception), err=True)
        sys.exit(1)

    try:
        pyproject_toml_requires = parsed_toml['build-system']['requires']
    except KeyError as exception:
        click.echo('Could not retrieve the build-system requires list from {}'.format(PATH_TOML), err=True)
        sys.exit(1)

    if reentry_requirement not in pyproject_toml_requires:
        click.echo('Reentry requirement from {} {} is not mirrored in {}'.format(
            FILENAME_REQUIREMENTS, reentry_requirement, PATH_TOML), err=True)
        sys.exit(1)


@click.command('conda')
def update_environment_yml():
    """
    Updates environment.yml file for conda.
    """
    import yaml

    with open(PATH_REQUIREMENTS, 'r') as info:
        setup_json = json.load(info)

    install_requires = setup_json['install_requires']

    # fix incompatibilities between conda and pypi
    replacements = {
        'psycopg2-binary' : 'psycopg2',
        'validate-email' : 'validate_email',
    }
    sep = '%'  # use something forbidden in conda package names
    pkg_string = sep.join(install_requires)
    for (pypi_pkg_name, conda_pkg_name) in iter(replacements.items()):
        pkg_string = pkg_string.replace(pypi_pkg_name, conda_pkg_name)
    install_requires = pkg_string.split(sep)

    environment = dict(
        name = 'aiida',
        channels = ['defaults', 'conda-forge', 'etetoolkit'],
        dependencies = install_requires,
    )

    with open(PATH_ENVIRONMENT, 'w') as env_file:
        env_file.write('# Usage: conda env create -f environment.yml\n')
        yaml.dump(environment, env_file, explicit_start=True, 
                  default_flow_style=False)

cli.add_command(validate_pyproject)
cli.add_command(update_environment_yml)

if __name__ == '__main__':
    cli()  # pylint: disable=no-value-for-parameter
