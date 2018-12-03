# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the process_function decorator."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import io

from aiida.backends.testbase import AiidaTestCase
from aiida.orm.data.bool import get_true_node
from aiida.orm.data.int import Int
from aiida.orm.data.str import Str
from aiida.orm.mixins import FunctionCalculationMixin
from aiida.orm.node.process import ProcessNode
from aiida.work import run, run_get_node, submit, process_function, Process, ExitCode

DEFAULT_INT = 256
DEFAULT_LABEL = 'Default label'
DEFAULT_DESCRIPTION = 'Default description'
CUSTOM_LABEL = 'Custom label'
CUSTOM_DESCRIPTION = 'Custom description'


class ProcessFunctionNode(FunctionCalculationMixin, ProcessNode):
    """A dummy ORM node class to test base process functions."""
    pass


class TestProcessFunction(AiidaTestCase):
    """
    Note that the @process_function decorator should never be used in production, which is why it does not have a node
    class by default and we create a dummy class in this file especially for testing purposes. We just use it here to
    test the generic interface functionality, that is shared between the concrete @calcfunction and @workfunction
    variants. For that reason we also do not test the outputs here, because they will not be generated for the base
    ProcessNode class and are specific to the @calculation and @workfunction, and will therefore be tested for them
    separately.
    """

    def setUp(self):
        super(TestProcessFunction, self).setUp()
        self.assertIsNone(Process.current())

        @process_function(node_class=ProcessFunctionNode)
        def function_return_input(data):
            return data

        @process_function(node_class=ProcessFunctionNode)
        def function_return_true():
            return get_true_node()

        @process_function(node_class=ProcessFunctionNode)
        def function_args(data_a):
            return data_a

        @process_function(node_class=ProcessFunctionNode)
        def function_args_with_default(data_a=Int(DEFAULT_INT)):
            return data_a

        @process_function(node_class=ProcessFunctionNode)
        def function_kwargs(**kwargs):
            return kwargs

        @process_function(node_class=ProcessFunctionNode)
        def function_args_and_kwargs(data_a, **kwargs):
            result = {'data_a': data_a}
            result.update(kwargs)
            return result

        @process_function(node_class=ProcessFunctionNode)
        def function_args_and_default(data_a, data_b=Int(DEFAULT_INT)):
            return {'data_a': data_a, 'data_b': data_b}

        @process_function(node_class=ProcessFunctionNode)
        def function_defaults(data_a=Int(DEFAULT_INT), label=DEFAULT_LABEL, description=DEFAULT_DESCRIPTION):  # pylint: disable=unused-argument
            return data_a

        @process_function(node_class=ProcessFunctionNode)
        def function_exit_code(exit_status, exit_message):
            return ExitCode(exit_status.value, exit_message.value)

        @process_function(node_class=ProcessFunctionNode)
        def function_excepts(exception):
            raise RuntimeError(exception.value)

        self.function_return_input = function_return_input
        self.function_return_true = function_return_true
        self.function_args = function_args
        self.function_args_with_default = function_args_with_default
        self.function_kwargs = function_kwargs
        self.function_args_and_kwargs = function_args_and_kwargs
        self.function_args_and_default = function_args_and_default
        self.function_defaults = function_defaults
        self.function_exit_code = function_exit_code
        self.function_excepts = function_excepts

    def tearDown(self):
        super(TestProcessFunction, self).tearDown()
        self.assertIsNone(Process.current())

    def test_process_state(self):
        """Test the process state for a process function."""
        _, node = self.function_args_with_default.run_get_node()

        self.assertEqual(node.is_terminated, True)
        self.assertEqual(node.is_excepted, False)
        self.assertEqual(node.is_killed, False)
        self.assertEqual(node.is_finished, True)
        self.assertEqual(node.is_finished_ok, True)
        self.assertEqual(node.is_failed, False)

    def test_exit_status(self):
        """A FINISHED process function has to have an exit status of 0"""
        _, node = self.function_args_with_default.run_get_node()
        self.assertEqual(node.exit_status, 0)
        self.assertEqual(node.is_finished_ok, True)
        self.assertEqual(node.is_failed, False)

    def test_source_code_attributes(self):
        """Verify function properties are properly introspected and stored in the nodes attributes and repository."""
        function_name = 'test_process_function'

        @process_function(node_class=ProcessFunctionNode)
        def test_process_function(data):
            return {'result': Int(data.value + 1)}

        _, node = test_process_function.run_get_node(data=Int(5))

        # Read the source file of the calculation function that should be stored in the repository
        # into memory, which should be exactly this test file
        function_source_file = node.function_source_file

        with io.open(function_source_file, encoding='utf8') as handle:
            function_source_code = handle.readlines()

        # Get the attributes that should be stored in the node
        function_name = node.function_name
        function_starting_line_number = node.function_starting_line_number

        # Verify that the function name is correct and the first source code linenumber is stored
        self.assertEqual(function_name, function_name)
        self.assertIsInstance(function_starting_line_number, int)

        # Check that first line number is correct. Note that the first line should correspond
        # to the `@process_function` directive, but since the list is zero-indexed we actually get the
        # following line, which should correspond to the function name i.e. `def test_process_function(data)`
        function_name_from_source = function_source_code[function_starting_line_number]
        self.assertTrue(function_name in function_name_from_source)

    def test_function_varargs(self):
        """Variadic arguments are not supported and should raise."""
        with self.assertRaises(ValueError):

            @process_function(node_class=ProcessFunctionNode)
            def function_varargs(*args):  # pylint: disable=unused-variable
                return args

    def test_function_args(self):
        """Simple process function that defines a single positional argument."""
        arg = 1

        with self.assertRaises(ValueError):
            result = self.function_args()  # pylint: disable=no-value-for-parameter

        result = self.function_args(data_a=Int(arg))
        self.assertTrue(isinstance(result, Int))
        self.assertEqual(result, arg)

    def test_function_args_with_default(self):
        """Simple process function that defines a single argument with a default."""
        arg = 1

        result = self.function_args_with_default()
        self.assertTrue(isinstance(result, Int))
        self.assertEqual(result, Int(DEFAULT_INT))

        result = self.function_args_with_default(data_a=Int(arg))
        self.assertTrue(isinstance(result, Int))
        self.assertEqual(result, arg)

    def test_function_kwargs(self):
        """Simple process function that defines keyword arguments."""
        kwargs = {'data_a': Int(DEFAULT_INT)}

        result = self.function_kwargs()
        self.assertTrue(isinstance(result, dict))
        self.assertEqual(result, {})

        result = self.function_kwargs(**kwargs)
        self.assertTrue(isinstance(result, dict))
        self.assertEqual(result, kwargs)

    def test_function_args_and_kwargs(self):
        """Simple process function that defines a positional argument and keyword arguments."""
        arg = 1
        args = (Int(DEFAULT_INT),)
        kwargs = {'data_b': Int(arg)}

        result = self.function_args_and_kwargs(*args)
        self.assertTrue(isinstance(result, dict))
        self.assertEqual(result, {'data_a': args[0]})

        result = self.function_args_and_kwargs(*args, **kwargs)
        self.assertTrue(isinstance(result, dict))
        self.assertEqual(result, {'data_a': args[0], 'data_b': kwargs['data_b']})

    def test_function_args_and_kwargs_default(self):
        """Simple process function that defines a positional argument and an argument with a default."""
        arg = 1
        args_input_default = (Int(DEFAULT_INT),)
        args_input_explicit = (Int(DEFAULT_INT), Int(arg))

        result = self.function_args_and_default(*args_input_default)
        self.assertTrue(isinstance(result, dict))
        self.assertEqual(result, {'data_a': args_input_default[0], 'data_b': Int(DEFAULT_INT)})

        result = self.function_args_and_default(*args_input_explicit)
        self.assertTrue(isinstance(result, dict))
        self.assertEqual(result, {'data_a': args_input_explicit[0], 'data_b': args_input_explicit[1]})

    def test_function_args_passing_kwargs(self):
        """Cannot pass kwargs if the function does not explicitly define it accepts kwargs."""
        arg = 1

        with self.assertRaises(ValueError):
            self.function_args(data_a=Int(arg), data_b=Int(arg))  # pylint: disable=unexpected-keyword-arg

    def test_function_set_label_description(self):
        """Verify that the label and description can be set for all process function variants."""
        _, node = self.function_args.run_get_node(
            data_a=Int(DEFAULT_INT), label=CUSTOM_LABEL, description=CUSTOM_DESCRIPTION)
        self.assertEqual(node.label, CUSTOM_LABEL)
        self.assertEqual(node.description, CUSTOM_DESCRIPTION)

        _, node = self.function_args_with_default.run_get_node(label=CUSTOM_LABEL, description=CUSTOM_DESCRIPTION)
        self.assertEqual(node.label, CUSTOM_LABEL)
        self.assertEqual(node.description, CUSTOM_DESCRIPTION)

        _, node = self.function_kwargs.run_get_node(label=CUSTOM_LABEL, description=CUSTOM_DESCRIPTION)
        self.assertEqual(node.label, CUSTOM_LABEL)
        self.assertEqual(node.description, CUSTOM_DESCRIPTION)

        _, node = self.function_args_and_kwargs.run_get_node(
            data_a=Int(DEFAULT_INT), label=CUSTOM_LABEL, description=CUSTOM_DESCRIPTION)
        self.assertEqual(node.label, CUSTOM_LABEL)
        self.assertEqual(node.description, CUSTOM_DESCRIPTION)

        _, node = self.function_args_and_default.run_get_node(
            data_a=Int(DEFAULT_INT), label=CUSTOM_LABEL, description=CUSTOM_DESCRIPTION)
        self.assertEqual(node.label, CUSTOM_LABEL)
        self.assertEqual(node.description, CUSTOM_DESCRIPTION)

    def test_function_defaults(self):
        """Verify that a process function can define a default label and description but can be overriden."""
        _, node = self.function_defaults.run_get_node(data_a=Int(DEFAULT_INT))
        self.assertEqual(node.label, DEFAULT_LABEL)
        self.assertEqual(node.description, DEFAULT_DESCRIPTION)

        _, node = self.function_defaults.run_get_node(label=CUSTOM_LABEL, description=CUSTOM_DESCRIPTION)
        self.assertEqual(node.label, CUSTOM_LABEL)
        self.assertEqual(node.description, CUSTOM_DESCRIPTION)

    def test_launchers(self):
        """Verify that the various launchers are working."""
        result = run(self.function_return_true)
        self.assertTrue(result)

        result, node = run_get_node(self.function_return_true)
        self.assertTrue(result)
        self.assertEqual(result, get_true_node())
        self.assertTrue(isinstance(node, ProcessFunctionNode))

        with self.assertRaises(AssertionError):
            submit(self.function_return_true)

    def test_return_exit_code(self):
        """
        A process function that returns an ExitCode namedtuple should have its exit status and message set FINISHED
        """
        exit_status = 418
        exit_message = 'I am a teapot'

        _, node = self.function_exit_code.run_get_node(exit_status=Int(exit_status), exit_message=Str(exit_message))

        self.assertTrue(node.is_finished)
        self.assertFalse(node.is_finished_ok)
        self.assertEqual(node.exit_status, exit_status)
        self.assertEqual(node.exit_message, exit_message)

    def test_normal_exception(self):
        """If a process, for example a FunctionProcess, excepts, the exception should be stored in the node."""
        exception = 'This process function excepted'

        with self.assertRaises(RuntimeError):
            _, node = self.function_excepts.run_get_node(exception=Str(exception))
            self.assertTrue(node.is_excepted)
            self.assertEqual(node.exception, exception)

    def test_simple_workflow(self):
        """Test construction of simple workflow by chaining process functions."""

        @process_function(node_class=ProcessFunctionNode)
        def add(data_a, data_b):
            return data_a + data_b

        @process_function(node_class=ProcessFunctionNode)
        def mul(data_a, data_b):
            return data_a * data_b

        @process_function(node_class=ProcessFunctionNode)
        def add_mul_wf(data_a, data_b, data_c):
            return mul(add(data_a, data_b), data_c)

        result, node = add_mul_wf.run_get_node(Int(3), Int(4), Int(5))

        self.assertEqual(result, (3 + 4) * 5)
        self.assertIsInstance(node, ProcessFunctionNode)

    def test_hashes(self):
        """Test that the hashes generated for identical process functions with identical inputs are the same."""
        _, node1 = self.function_return_input.run_get_node(data=Int(2))
        _, node2 = self.function_return_input.run_get_node(data=Int(2))
        self.assertEqual(node1.get_hash(), node1.get_extra('_aiida_hash'))
        self.assertEqual(node2.get_hash(), node2.get_extra('_aiida_hash'))
        self.assertEqual(node1.get_hash(), node2.get_hash())

    def test_hashes_different(self):
        """Test that the hashes generated for identical process functions with different inputs are the different."""
        _, node1 = self.function_return_input.run_get_node(data=Int(2))
        _, node2 = self.function_return_input.run_get_node(data=Int(3))
        self.assertEqual(node1.get_hash(), node1.get_extra('_aiida_hash'))
        self.assertEqual(node2.get_hash(), node2.get_extra('_aiida_hash'))
        self.assertNotEqual(node1.get_hash(), node2.get_hash())
