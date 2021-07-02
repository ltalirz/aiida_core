"""
Parsers provided by aiida_diff.

Register parsers via the "aiida.parsers" entry point in the setup.json file.
"""
from aiida.engine import ExitCode
from aiida.parsers.parser import Parser
from aiida.plugins import CalculationFactory
from aiida.orm import SinglefileData

DiffCalculation = CalculationFactory('diff')


class DiffParser(Parser):
    """
    Parser class for parsing output of calculation.
    """

    def parse(self, **kwargs):
        """
        Parse outputs, store results in database.

        :returns: non-zero exit code, if parsing fails
        """

        output_filename = self.node.get_option('output_filename')

        # Check that folder content is as expected
        files_retrieved = self.retrieved.list_object_names()
        files_expected = [output_filename]
        # Note: set(A) <= set(B) checks whether A is a subset of B
        if not set(files_expected) <= set(files_retrieved):
            self.logger.error("Found files '{}', expected to find '{}'".format(
                files_retrieved, files_expected))
            return self.exit_codes.ERROR_MISSING_OUTPUT_FILES

        # add output file
        self.logger.info("Parsing '{}'".format(output_filename))
        with self.retrieved.open(output_filename, 'rb') as handle:
            output_node = SinglefileData(file=handle)
        self.out('diff', output_node)

        return ExitCode(0)

class DiffParserSimple(Parser):
    """
    Parser class for parsing output of calculation.
    """

    def parse(self, **kwargs):
        """
        Parse outputs, store results in database.
        
        This function is used just as a code snippet for the plugin tutorial.
        """

        output_filename = self.node.get_option('output_filename')

        # add output file
        self.logger.info("Parsing '{}'".format(output_filename))
        with self.retrieved.open(output_filename, 'rb') as handle:
            output_node = SinglefileData(file=handle)
        self.out('diff', output_node)

        return ExitCode(0)