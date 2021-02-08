# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the `run` functions."""
from pympler import muppy

from aiida.backends.testbase import AiidaTestCase
from aiida.engine import run, run_get_node
from aiida.engine.processes import Process
from aiida.orm import Int, Str, ProcessNode

from tests.utils.processes import DummyProcess


class TestRun(AiidaTestCase):
    """Tests for the `run` functions."""

    @staticmethod
    def test_run():
        """Test the `run` function."""
        inputs = {'a': Int(2), 'b': Str('test')}
        run(DummyProcess, **inputs)

        # check that no references to processes are left in memory
        all_objects = muppy.get_objects()  # note: this also calls gc.collect()
        processes = [o for o in all_objects if hasattr(o, '__class__') and isinstance(o, Process)]
        assert not processes

    def test_run_get_node(self):
        """Test the `run_get_node` function."""
        inputs = {'a': Int(2), 'b': Str('test')}
        result, node = run_get_node(DummyProcess, **inputs)  # pylint: disable=unused-variable
        self.assertIsInstance(node, ProcessNode)
