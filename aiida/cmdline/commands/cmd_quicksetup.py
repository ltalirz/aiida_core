# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=too-many-arguments,too-many-locals,too-many-statements,too-many-branches
"""`verdi quicksetup` command."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import os
import sys
import hashlib

import click

from aiida.cmdline.commands.cmd_verdi import verdi
from aiida.cmdline.params import arguments, options
from aiida.cmdline.utils import echo
from aiida.manage.external.postgres import Postgres, manual_setup_instructions, prompt_db_info
from aiida.manage.configuration.setup import setup_profile


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


@verdi.command('quicksetup')
@arguments.PROFILE_NAME(default='quicksetup')
@options.PROFILE_ONLY_CONFIG()
@options.PROFILE_SET_DEFAULT()
@options.NON_INTERACTIVE()
@options.BACKEND()
@options.DB_HOST()
@options.DB_PORT()
@options.DB_NAME()
@options.DB_USERNAME()
@options.DB_PASSWORD()
@options.REPOSITORY_PATH()
@options.USER_EMAIL()
@options.USER_FIRST_NAME()
@options.USER_LAST_NAME()
@options.USER_INSTITUTION()
def quicksetup(profile_name, only_config, set_default, non_interactive, backend, db_host, db_port, db_name, db_username,
               db_password, repository, email, first_name, last_name, institution):
    """Set up a sane configuration with as little interaction as possible."""
    import getpass
    from aiida.common.hashing import get_random_string
    from aiida.manage.configuration.utils import load_config
    from aiida.manage.configuration.setup import create_instance_directories

    create_instance_directories()
    config = load_config(create=True)

    # create profile, prompt the user if already exists
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
    dbinfo = {'host': db_host, 'port': db_port}
    postgres = Postgres(interactive=bool(not non_interactive), quiet=False, dbinfo=dbinfo)
    postgres.set_setup_fail_callback(prompt_db_info)
    success = postgres.determine_setup()
    if not success:
        sys.exit(1)

    osuser = getpass.getuser()
    config_dir_hash = hashlib.md5(config.dirpath.encode('utf-8')).hexdigest()

    # default database user name is aiida_qs_<login-name>
    # default password is random
    db_user = db_username or 'aiida_qs_' + osuser + '_' + config_dir_hash
    db_password = db_password or get_random_string(length=50)

    # check if there is a profile that contains the db user already
    # if yes, take the db user password from there
    # Note: A user can only see his or her own config files
    for profile in config.profiles:
        if profile.dictionary.get('AIIDADB_USER', '') == db_user and not db_password:
            db_password = profile.dictionary.get('AIIDADB_PASS')
            echo.echo('using found password for {}'.format(db_user))
            break

    # default database name is <profile_name>_<login-name>
    # this ensures that for profiles named test_... the database will also be named test_...
    dbname = db_name or profile_name + '_' + osuser + '_' + config_dir_hash

    try:
        create = True
        if not postgres.dbuser_exists(db_user):
            postgres.create_dbuser(db_user, db_password)
        else:
            dbname, create = _check_db_name(dbname, postgres)
        if create:
            postgres.create_db(db_user, dbname)
    except Exception as exception:
        echo.echo_error('\n'.join([
            'Oops! quicksetup was unable to create the AiiDA database for you.',
            'For AiiDA to work, please either create the database yourself as follows:',
            manual_setup_instructions(dbuser=db_user, dbname=dbname), '',
            'Alternatively, give your (operating system) user permission to create postgresql databases' +
            'and run quicksetup again.', ''
        ]))
        raise exception

    repository = repository or 'repository/{}/'.format(profile_name)
    if not os.path.isabs(repository):
        repository = os.path.join(config.dirpath, repository)

    setup_args = {
        'backend': backend,
        'email': email,
        'db_host': db_host,
        'db_port': db_port,
        'db_name': dbname,
        'db_user': db_user,
        'db_pass': db_password,
        'repo': repository,
        'first_name': first_name,
        'last_name': last_name,
        'institution': institution,
        'force_overwrite': write_profile,
    }

    setup_profile(profile_name, only_config=only_config, set_default=set_default, non_interactive=True, **setup_args)
    echo.echo_success("Set up profile '{}'.".format(profile_name))
