# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Create, configure, manage users"""


def get_or_new_user(**kwargs):
    """find an existing user or instantiate a new one (unstored)"""
    from aiida.orm import User
    candidates = User.search_for_users(**kwargs)
    if candidates:
        user = candidates[0]
        created = False
    else:
        user = User(**kwargs)
        created = True
    return user, created


def get_user_of_default_profile(config=None):
    """ Returns AiiDA user associated with default profile.

    :param config: AiiDA configuration file

    :return duser: Default user or None
    :rtype duser: aiida.orm.user.User
    """

    if config is None:
        from aiida.common.setup import get_or_create_config
        config = get_or_create_config()

    from aiida.common.exceptions import NotExistent
    try:
        profiles = config['profiles']
        default_conf_name = config['default_profiles']['verdi']
        default_conf = profiles[default_conf_name]
        default_email = default_conf['default_user_email']

        from aiida import load_dbenv, is_dbenv_loaded
        if not is_dbenv_loaded():
            load_dbenv()

        from aiida.orm.user import User as AiiDAUser
        users = AiiDAUser.search_for_users(email=default_email)
        duser = users[0]
        return duser

    except (KeyError, NotExistent):
        return None
