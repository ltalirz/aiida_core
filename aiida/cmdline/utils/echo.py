# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
""" Convenience functions for printing output from verdi commands """

from enum import IntEnum
from collections import OrderedDict
import sys

import yaml
import click

from aiida.common import AIIDA_LOGGER

__all__ = (
    'echo', 'echo_info', 'echo_debug', 'echo_success', 'echo_warning', 'echo_error', 'echo_critical', 'echo_highlight',
    'echo_dictionary', 'CMDLINE_LOGGER'
)

CMDLINE_LOGGER = AIIDA_LOGGER.getChild('cmdline')


class ExitCode(IntEnum):
    """Exit codes for the verdi command line."""
    CRITICAL = 1
    DEPRECATED = 80
    UNKNOWN = 99
    SUCCESS = 0


COLORS = {
    'success': 'green',
    'highlight': 'green',
    'info': 'blue',
    'warning': 'bright_yellow',
    'error': 'red',
    'critical': 'red',
    'deprecated': 'red',
}
BOLD = True  # whether colors are used together with 'bold'


# pylint: disable=invalid-name
def echo(message, bold=False, nl=True, err=False):
    """
    Print a normal message through click's echo function to stdout

    :param message: the string representing the message to print
    :param bold: whether to print the message in bold
    :param nl: whether to print a newline at the end of the message
    :param err: whether to print to stderr
    """
    CMDLINE_LOGGER.info(click.style(message, bold=bold), extra=dict(nl=nl, err=err))


def echo_debug(message, bold=False, nl=True, err=False):
    """
    Print a debug message through click's echo function to stdout

    :param message: the string representing the message to print
    :param bold: whether to print the message in bold
    :param nl: whether to print a newline at the end of the message
    :param err: whether to print to stderr
    """
    msg = click.style(message, bold=bold)
    CMDLINE_LOGGER.debug(msg, extra=dict(nl=nl, err=err))


def echo_info(message, bold=False, nl=True, err=False):
    """
    Print an info message through click's echo function to stdout, prefixed with 'Info:'

    :param message: the string representing the message to print
    :param bold: whether to print the message in bold
    :param nl: whether to print a newline at the end of the message
    :param err: whether to print to stderr
    """
    msg = click.style('Info: ', fg=COLORS['info'], bold=True) + click.style(message, bold=bold)
    CMDLINE_LOGGER.info(msg, extra=dict(nl=nl, err=err))


def echo_success(message, bold=False, nl=True, err=False):
    """
    Print a success message through click's echo function to stdout, prefixed with 'Success:'

    :param message: the string representing the message to print
    :param bold: whether to print the message in bold
        include a newline character
    :param nl: whether to print a newline at the end of the message
    :param err: whether to print to stderr
    """
    msg = click.style('Success: ', fg=COLORS['success'], bold=True) + click.style(message, bold=bold)
    CMDLINE_LOGGER.info(msg, extra=dict(nl=nl, err=err))


def echo_warning(message, bold=False, nl=True, err=False):
    """
    Print a warning message through click's echo function to stdout, prefixed with 'Warning:'

    :param message: the string representing the message to print
    :param bold: whether to print the message in bold
    :param nl: whether to print a newline at the end of the message
    :param err: whether to print to stderr
    """
    msg = click.style('Warning: ', fg=COLORS['warning'], bold=True) + click.style(message, bold=bold)
    CMDLINE_LOGGER.warning(msg, extra=dict(nl=nl, err=err))


def echo_error(message, bold=False, nl=True, err=True):
    """
    Print an error message through click's echo function to stdout, prefixed with 'Error:'

    :param message: the string representing the message to print
    :param bold: whether to print the message in bold
    :param nl: whether to print a newline at the end of the message
    :param err: whether to print to stderr
    """
    msg = click.style('Error: ', fg=COLORS['error'], bold=True) + click.style(message, bold=bold)
    CMDLINE_LOGGER.error(msg, extra=dict(nl=nl, err=err))


def echo_critical(message, bold=False, nl=True, err=True):
    """
    Print an error message through click's echo function to stdout, prefixed with 'Critical:'
    and then calls sys.exit with the given exit_status.

    This should be used to print messages for errors that cannot be recovered
    from and so the script should be directly terminated with a non-zero exit
    status to indicate that the command failed

    :param message: the string representing the message to print
    :param bold: whether to print the message in bold
    :param nl: whether to print a newline at the end of the message
    :param err: whether to print to stderr
    """
    msg = click.style('Critical: ', fg=COLORS['critical'], bold=True) + click.style(message, bold=bold)
    CMDLINE_LOGGER.critical(msg, extra=dict(nl=nl, err=err))
    sys.exit(ExitCode.CRITICAL)


def echo_highlight(message, nl=True, bold=True, color='highlight'):
    """
    Print a highlighted message to stdout

    :param message: the string representing the message to print
    :param bold: whether to print the message in bold
    :param nl: whether to print a newline at the end of the message
    :param color: a color from COLORS
    """
    msg = click.style(message, bold=bold, fg=COLORS[color])
    CMDLINE_LOGGER.info(msg, extra=dict(nl=nl))


# pylint: disable=redefined-builtin
def echo_deprecated(message, bold=False, nl=True, err=True, exit=False):
    """
    Print an error message through click's echo function to stdout, prefixed with 'Deprecated:'
    and then calls sys.exit with the given exit_status.

    This should be used to indicate deprecated commands.

    :param message: the string representing the message to print
    :param bold: whether to print the message in bold
    :param nl: whether to print a newline at the end of the message
    :param err: whether to print to stderr
    :param exit: whether to exit after printing the message
    """
    msg = click.style('Deprecated: ', fg=COLORS['deprecated'], bold=True) + click.style(message, bold=bold)
    CMDLINE_LOGGER.info(msg, extra=dict(nl=nl, err=err))

    if exit:
        sys.exit(ExitCode.DEPRECATED)


def echo_formatted_list(collection, attributes, sort=None, highlight=None, hide=None):
    """Print a collection of entries as a formatted list, one entry per line.

    :param collection: a list of objects
    :param attributes: a list of attributes to print for each entry in the collection
    :param sort: optional lambda to sort the collection
    :param highlight: optional lambda to highlight an entry in the collection if it returns True
    :param hide: optional lambda to skip an entry if it returns True
    """
    if sort:
        entries = sorted(collection, key=sort)
    else:
        entries = collection

    template = f"{{symbol}}{' {}' * len(attributes)}"

    for entry in entries:
        if hide and hide(entry):
            continue

        values = [getattr(entry, attribute) for attribute in attributes]
        if highlight and highlight(entry):
            CMDLINE_LOGGER.info(click.style(template.format(symbol='*', *values), fg=COLORS['highlight']))
        else:
            CMDLINE_LOGGER.info(click.style(template.format(symbol=' ', *values)))


def _format_dictionary_json_date(dictionary):
    """Return a dictionary formatted as a string using the json format and converting dates to strings."""
    from aiida.common import json

    def default_jsondump(data):
        """Function needed to decode datetimes, that would otherwise not be JSON-decodable."""
        import datetime
        from aiida.common import timezone

        if isinstance(data, datetime.datetime):
            return timezone.localtime(data).strftime('%Y-%m-%dT%H:%M:%S.%f%z')

        raise TypeError(f'{repr(data)} is not JSON serializable')

    return json.dumps(dictionary, indent=4, sort_keys=True, default=default_jsondump)


VALID_DICT_FORMATS_MAPPING = OrderedDict((('json+date', _format_dictionary_json_date), ('yaml', yaml.dump),
                                          ('yaml_expanded', lambda d: yaml.dump(d, default_flow_style=False))))


def echo_dictionary(dictionary, fmt='json+date'):
    """
    Print the given dictionary to stdout in the given format

    :param dictionary: the dictionary
    :param fmt: the format to use for printing
    """
    try:
        format_function = VALID_DICT_FORMATS_MAPPING[fmt]
    except KeyError:
        formats = ', '.join(VALID_DICT_FORMATS_MAPPING.keys())
        raise ValueError(f'Unrecognised printing format. Valid formats are: {formats}')

    echo(format_function(dictionary))


def is_stdout_redirected():
    """Determines if the standard output is redirected.

    For cases where the standard output is redirected and you want to
    inform the user without messing up the output. Example::

        echo.echo_info("Found {} results".format(qb.count()), err=echo.is_stdout_redirected)
        echo.echo(tabulate.tabulate(qb.all()))
    """
    # pylint: disable=no-member
    return not sys.stdout.isatty()
