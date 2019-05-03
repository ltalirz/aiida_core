# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""The main `verdi` click group."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import click

from aiida.cmdline.params import options
from aiida.common.extendeddicts import AttributeDict
from aiida.common import exceptions


@click.group(context_settings={'help_option_names': ['-h', '--help']})
@options.PROFILE()
@click.option('--version', is_flag=True, is_eager=True, help='Print the version of AiiDA that is currently installed.')
@click.pass_context
def verdi(ctx, profile, version):
    """The command line interface of AiiDA."""
    import sys
    from aiida import get_version
    from aiida.cmdline.utils import echo
    from aiida.manage.configuration import get_config, load_profile

    if version:
        echo.echo('AiiDA version {}'.format(get_version()))
        sys.exit(0)

    if ctx.obj is None:
        ctx.obj = AttributeDict()

    config = get_config(create=True)

    if not profile:
        try:
            profile = config.get_profile()
        except exceptions.ProfileConfigurationError:
            profile = None

    if profile:
        load_profile(profile.name)

    ctx.obj.config = config
    ctx.obj.profile = profile
