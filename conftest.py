# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Configuration file for pytest tests."""

import pytest  # pylint: disable=unused-import

pytest_plugins = ['aiida.manage.tests.pytest_fixtures']  # pylint: disable=invalid-name


@pytest.fixture(scope='session', autouse=True)
def default_user(self):
    """ Add default user if required.

    Note: AiiDA databases set up by the TestManager already contain a default user.
    However, AiiDA test_profile databases *after* running tests can lack the default user.
    """
    from aiida.manage.configuration import get_config
    from aiida import orm
    from aiida.common import exceptions
    self.user_email = get_config().current_profile.default_user

    try:
        self.user = orm.User.objects.get(email=self.user_email)
    except exceptions.NotExistent:
        self.user = orm.User(email=self.user_email).store()
