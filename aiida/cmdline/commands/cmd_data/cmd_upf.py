# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""`verdi data upf` command."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import io
import click

from aiida.cmdline.commands.cmd_data import verdi_data
from aiida.cmdline.params import arguments, options
from aiida.cmdline.utils import decorators, echo


@verdi_data.group('upf')
def upf():
    """Manipulation of the upf families."""
    pass


@upf.command('uploadfamily')
@click.argument('folder', type=click.Path(exists=True, file_okay=False, resolve_path=True))
@click.argument('group_name', type=click.STRING)
@click.argument('group_description', type=click.STRING)
@click.option(
    '--stop-if-existing',
    is_flag=True,
    default=False,
    help='Interrupt pseudos import if a pseudo was already present in the AiiDA database')
@decorators.with_dbenv()
def upf_uploadfamily(folder, group_name, group_description, stop_if_existing):
    """
    Upload a new pseudopotential family.

    Returns the numbers of files found and the number of nodes uploaded.

    Call without parameters to get some help.
    """
    import aiida.orm.data.upf as upf_
    files_found, files_uploaded = upf_.upload_upf_family(folder, group_name, group_description, stop_if_existing)
    echo.echo_success("UPF files found: {}. New files uploaded: {}".format(files_found, files_uploaded))


@upf.command('listfamilies')
@click.option(
    '-d',
    '--with-description',
    'with_description',
    is_flag=True,
    default=False,
    help="Show also the description for the UPF family")
@options.WITH_ELEMENTS()
@decorators.with_dbenv()
def upf_listfamilies(elements, with_description):
    """
    Print on screen the list of upf families installed
    """
    from aiida import orm
    from aiida.orm.data.upf import UPFGROUP_TYPE

    UpfData = orm.DataFactory('upf')  # pylint: disable=invalid-name
    query = orm.QueryBuilder()
    query.append(UpfData, tag='upfdata')
    if elements is not None:
        query.add_filter(UpfData, {'attributes.element': {'in': elements}})
    query.append(
        orm.Group,
        group_of='upfdata',
        tag='group',
        project=["name", "description"],
        filters={"type": {
            '==': UPFGROUP_TYPE
        }})

    query.distinct()
    if query.count() > 0:
        for res in query.dict():
            group_name = res.get("group").get("name")
            group_desc = res.get("group").get("description")
            query = orm.QueryBuilder()
            query.append(orm.Group, tag='thisgroup', filters={"name": {'like': group_name}})
            query.append(UpfData, project=["id"], member_of='thisgroup')

            if with_description:
                description_string = ": {}".format(group_desc)
            else:
                description_string = ""

            echo.echo_success("* {} [{} pseudos]{}".format(group_name, query.count(), description_string))

    else:
        echo.echo_warning("No valid UPF pseudopotential family found.")


@upf.command('exportfamily')
@click.argument('folder', type=click.Path(exists=True, file_okay=False, resolve_path=True))
@arguments.GROUP()
@decorators.with_dbenv()
def upf_exportfamily(folder, group):
    """
    Export a pseudopotential family into a folder.
    Call without parameters to get some help.
    """
    import os

    # pylint: disable=protected-access
    for node in group.nodes:
        dest_path = os.path.join(folder, node.filename)
        if not os.path.isfile(dest_path):
            with io.open(dest_path, 'w', encoding='utf8') as dest:
                with node._get_folder_pathsubfolder.open(node.filename) as source:
                    dest.write(source.read())
        else:
            echo.echo_warning("File {} is already present in the destination folder".format(node.filename))


@upf.command('import')
@click.argument('filename', type=click.Path(exists=True, dir_okay=False, resolve_path=True))
@decorators.with_dbenv()
def upf_import(filename):
    """
    Import upf data object
    """
    from aiida.orm.data.upf import UpfData

    node, _ = UpfData.get_or_create(filename)
    echo.echo_success('Imported: {}'.format(node))
