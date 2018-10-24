# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Utilities for testing components from the workflow engine"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
import plumpy
from aiida.work.processes import Process


class DummyProcess(Process):
    """A Process that does nothing when it runs."""

    @classmethod
    def define(cls, spec):
        super(DummyProcess, cls).define(spec)
        spec.inputs.dynamic = True
        spec.outputs.dynamic = True

    def _run(self):
        pass


class AddProcess(Process):
    """A simple Process that adds two integers."""

    @classmethod
    def define(cls, spec):
        super(AddProcess, cls).define(spec)
        spec.input('a', required=True)
        spec.input('b', required=True)
        spec.output('result', required=True)

    def _run(self):
        self.out(self.inputs.a + self.inputs.b)


class BadOutput(Process):
    """A Process that emits an output that isn't part of the spec raising an exception."""

    @classmethod
    def define(cls, spec):
        super(BadOutput, cls).define(spec)
        spec.outputs.dynamic = True

    def _run(self):
        self.out("bad_output", 5)


class ExceptionProcess(Process):
    """A Process that raises a RuntimeError when run."""

    def _run(self):  # pylint: disable=no-self-use
        raise RuntimeError('CRASH')


class WaitProcess(Process):
    """A Process that waits until it is asked to continue."""

    def _run(self):
        return plumpy.Wait(self.next_step)

    def next_step(self):
        pass
