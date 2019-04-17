# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
Integration tests for setup, quicksetup, and delete

These can not be added to test_profile.py in the locally run test suite as long as that does
not use a separate (temporary) configuration directory:
 * it might overwrite user profiles
 * it might leave behind partial profiles
 * it does not clean up the file system behind itself

Possible ways of solving this problem:

 * migrate all tests to the fixtures in aiida.utils.fixtures, which already provide this functionality
 * implement the functionality in the Aiidatestcase
 * implement the functionality specifically for the verdi profile tests (using setUp and tearDown methods)

It has not been done yet due to time constraints.
"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import unittest
import os

from click.testing import CliRunner

from aiida.backends.tests.utils.configuration import create_mock_profile, with_temporary_config_instance
from aiida.cmdline.commands.cmd_setup import quicksetup


class ProfileManageTestCase(unittest.TestCase):
    """Tests that manipulate profiles and their databases.

     Testing:
      * `verdi quicksetup`
      * `verdi profile delete`

      """

    @classmethod
    def setUpClass(cls):
        """Set up database, profile and file repository."""
        from aiida.manage.fixtures import _GLOBAL_FIXTURE_MANAGER

        cls.backend = os.environ.get('TEST_AIIDA_BACKEND', 'django')

        cls.fixture_manager = _GLOBAL_FIXTURE_MANAGER
        if cls.fixture_manager.has_profile_open():
            raise ValueError("Fixture mananger already has an open profile. This is unexpected.")

        cls.fixture_manager.backend = cls.backend
        cls.fixture_manager.create_profile()

    @classmethod
    def tearDownClass(cls):
        cls.fixture_manager.destroy_all()

    def setUp(self):
        self.runner = CliRunner()

    def tearDown(self):
        self.fixture_manager.reset_db()

    @with_temporary_config_instance
    def test_quicksetup(self):
        """Test `verdi quicksetup` non-interactively."""
        from aiida.manage import configuration
        configuration.BACKEND_UUID = None
        result = self.runner.invoke(quicksetup, [
            '--profile=giuseppe-{}'.format(self.backend),
            '--db-backend={}'.format(self.backend),
            '--email=giuseppe.verdi@ope.ra',
            '--first-name=Giuseppe',
            '--last-name=Verdi',
            '--institution=Scala',
            '--db-port={}'.format(self.fixture_manager.db_port),
            '--non-interactive',
        ])
        self.assertFalse(result.exception, msg=get_debug_msg(result))

    @with_temporary_config_instance
    def test_postgres_failure(self):
        """Test `verdi quicksetup` non-interactively with incorrect database connection parameters."""
        result = self.runner.invoke(quicksetup, [
            '--profile=giuseppe2-{}'.format(self.backend), '--db-backend={}'.format(
                self.backend), '--email=giuseppe2.verdi@ope.ra', '--first-name=Giuseppe', '--last-name=Verdi',
            '--institution=Scala', '--db-port=1111', '--non-interactive'
        ])
        self.assertTrue(result.exception, msg=get_debug_msg(result))

    @with_temporary_config_instance
    def test_delete(self):
        """Test for verdi profile delete command."""
        from aiida.cmdline.commands.cmd_profile import profile_delete, profile_list
        from aiida.manage.configuration import get_config

        # Create mock profiles
        mock_profiles = ['mock_profile1', 'mock_profile2', 'mock_profile3', 'mock_profile4']
        config = get_config()
        for profile_name in mock_profiles:
            config.add_profile(create_mock_profile(profile_name))
        config.set_default_profile(mock_profiles[0], overwrite=True).store()

        # Delete single profile
        result = self.runner.invoke(profile_delete, ['--force', mock_profiles[1]])
        self.assertIsNone(result.exception, result.output)

        result = self.runner.invoke(profile_list)
        self.assertIsNone(result.exception, result.output)

        self.assertNotIn(mock_profiles[1], result.output)
        self.assertIsNone(result.exception, result.output)

        # Delete multiple profiles
        result = self.runner.invoke(profile_delete, ['--force', mock_profiles[2], mock_profiles[3]])
        self.assertIsNone(result.exception, result.output)

        result = self.runner.invoke(profile_list)
        self.assertIsNone(result.exception, result.output)
        self.assertNotIn(mock_profiles[2], result.output)
        self.assertNotIn(mock_profiles[3], result.output)
        self.assertIsNone(result.exception, result.output)


def get_debug_msg(result):
    msg = '{}\n---\nOutput:\n{}'
    return msg.format(result.exception, result.output)


if __name__ == '__main__':
    unittest.main()
