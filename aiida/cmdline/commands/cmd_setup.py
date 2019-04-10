# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""The `verdi setup` and `verdi quicksetup` commands."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import click

from aiida.cmdline.commands.cmd_verdi import verdi
from aiida.cmdline.params.options.commands import setup as options
from aiida.cmdline.utils import echo
from aiida.manage.configuration import load_profile
from aiida.manage.manager import get_manager


@verdi.command('setup')
@options.SETUP_PROFILE()
@options.SETUP_USER_EMAIL()
@options.SETUP_USER_FIRST_NAME()
@options.SETUP_USER_LAST_NAME()
@options.SETUP_USER_INSTITUTION()
@options.SETUP_USER_PASSWORD()
@options.SETUP_DATABASE_ENGINE()
@options.SETUP_DATABASE_BACKEND()
@options.SETUP_DATABASE_HOSTNAME()
@options.SETUP_DATABASE_PORT()
@options.SETUP_DATABASE_NAME()
@options.SETUP_DATABASE_USERNAME()
@options.SETUP_DATABASE_PASSWORD()
@options.SETUP_REPOSITORY_URI()
@click.pass_context
def setup(ctx, profile, email, first_name, last_name, institution, password, db_engine, db_backend, db_host, db_port,
          db_name, db_username, db_password, repository):
    """Setup a new profile."""
    # pylint: disable=too-many-arguments
    from aiida import orm

    profile.database_engine = db_engine
    profile.database_backend = db_backend
    profile.database_name = db_name
    profile.database_port = db_port
    profile.database_hostname = db_host
    profile.database_username = db_username
    profile.database_password = db_password
    profile.repository_uri = 'file://' + repository

    # Creating the profile
    ctx.obj.config.add_profile(profile)
    ctx.obj.config.set_default_profile(profile.name)

    # Load the profile
    load_profile(profile.name)
    echo.echo_success('created new profile `{}`.'.format(profile.name))

    # Migrate the database
    echo.echo_info('migrating the database.')
    backend = get_manager()._load_backend(schema_check=False)  # pylint: disable=protected-access
    backend.migrate()
    echo.echo_success('database migration completed.')

    # Create the user if it does not yet exist
    created, user = orm.User.objects.get_or_create(
        email=email, first_name=first_name, last_name=last_name, institution=institution, password=password)
    if created:
        user.store()
    profile.default_user = user.email
    ctx.obj.config.update_profile(profile)
    ctx.obj.config.store()


@verdi.command('quicksetup')
@options.SETUP_PROFILE(default='quicksetup')
@options.SETUP_USER_EMAIL()
@options.SETUP_USER_FIRST_NAME()
@options.SETUP_USER_LAST_NAME()
@options.SETUP_USER_INSTITUTION()
@options.SETUP_USER_PASSWORD()
@click.pass_context
def quicksetup(ctx, profile, email, first_name, last_name, institution, password):
    """Setup a new profile where the database is automatically created and configured."""
    # pylint: disable=too-many-arguments,too-many-locals,too-many-statements,too-many-branches,unused-argument,protected-access
    import os
    import getpass
    import hashlib
    from aiida.common.hashing import get_random_string
    from aiida.manage.configuration import get_config
    from aiida.manage.external.postgres import Postgres, manual_setup_instructions, prompt_db_info

    def _check_db_name(dbname, postgres):
        """Looks up if a database with the name exists, prompts for using or creating a differently named one."""
        create = True
        while create and postgres.db_exists(dbname):
            echo.echo_info('database {} already exists!'.format(dbname))
            if not click.confirm('Use it (make sure it is not used by another profile)?'):
                dbname = click.prompt('new name', type=str, default=dbname)
            else:
                create = False
        return dbname, create

    config = get_config(create=True)

    # create a profile, by default 'quicksetup' and prompt the user if already exists
    profile_name = profile.name or 'quicksetup'
    write_profile = False
    while not write_profile:
        if profile_name in config.profile_names:
            echo.echo_warning("Profile '{}' already exists.".format(profile_name))
            if click.confirm("Overwrite existing profile '{}'?".format(profile_name)):
                write_profile = True
            else:
                profile_name = click.prompt('New profile name', type=str)
        else:
            write_profile = True

    # access postgres
    postgres = Postgres(interactive=False, quiet=False)
    postgres.set_setup_fail_callback(prompt_db_info)
    success = postgres.determine_setup()
    if not success:
        echo.echo_critical('failed to determine the PostgreSQL setup')

    osuser = getpass.getuser()
    config_dir_hash = hashlib.md5(config.dirpath.encode('utf-8')).hexdigest()

    # default database user name is aiida_qs_<login-name>
    # default password is random
    # default database name is <profile_name>_<login-name>
    # this ensures that for profiles named test_... the database will also be named test_...
    dbuser = 'aiida_qs_' + osuser + '_' + config_dir_hash
    dbpass = get_random_string(length=50)

    # check if there is a profile that contains the db user already
    # and if yes, take the db user password from there
    # This is ok because a user can only see his own config files
    dbname = profile_name + '_' + osuser + '_' + config_dir_hash
    for available_profile in config.profiles:
        if available_profile.database_username == dbuser:
            dbpass = available_profile.database_password
            echo.echo('using found password for {}'.format(dbuser))
            break
    try:
        create = True
        if not postgres.dbuser_exists(dbuser):
            postgres.create_dbuser(dbuser, dbpass)
        else:
            dbname, create = _check_db_name(dbname, postgres)
        if create:
            postgres.create_db(dbuser, dbname)
    except Exception as exception:
        echo.echo_error('\n'.join([
            'Oops! Something went wrong while creating the database for you.',
            'You may continue with the quicksetup, however:',
            'For aiida to work correctly you will have to do that yourself as follows.',
            manual_setup_instructions(dbuser=dbuser, dbname=dbname), '',
            'Or setup your (OS-level) user to have permissions to create databases and rerun quicksetup.', ''
        ]))
        raise exception

    dbhost = postgres.get_dbinfo().get('host', 'localhost')
    dbport = postgres.get_dbinfo().get('port', '5432')
    backend = 'django'

    repo = 'repository/{}/'.format(profile_name)
    if not os.path.isabs(repo):
        repo = os.path.join(config.dirpath, repo)

    setup_parameters = {
        'profile': profile_name,
        'email': 'test',
        'first_name': 'test',
        'last_name': 'test',
        'institution': 'test',
        'password': 'test',
        'db_engine': 'postgresql_psycopg2',
        'db_backend': backend,
        'db_name': dbname,
        'db_host': dbhost,
        'db_port': dbport,
        'db_username': dbuser,
        'db_password': dbpass,
        'repository': repo,
    }
    ctx.invoke(setup, **setup_parameters)
