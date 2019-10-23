#!/bin/bash

# Be verbose, and stop with error as soon there's one
set -ev

# Needed on Jenkins
if [ -e ~/.bashrc ] ; then source ~/.bashrc ; fi

CI_DIR="${TRAVIS_BUILD_DIR}/.ci"

case "$TEST_TYPE" in
    docs)
        # Compile the docs (HTML format);
        # -C change to 'docs' directory before doing anything
        # -n to warn about all missing references
        # -W to convert warnings in errors
        SPHINXOPTS="-nW" make -C docs
        ;;
    tests)
        VERDI=`which verdi`

        # The `check-load-time` command will check for indicators that typically slow down the `verdi` command
        coverage run -a $VERDI devel check-load-time

        # Test the loading time of `verdi` to ensure the database environment is not loaded
        set +e
        "${CI_DIR}/test_verdi_load_time.sh"

        # If the load time test failed, only exit if we are on travis
        if [ $? -gt 0 ] && [ -n "${TRAVIS}" ]; then
            exit 2
        fi
        set -e

        # Add the .ci folder to the python path so workchains within it can be found by the daemon
        export PYTHONPATH="${PYTHONPATH}:${CI_DIR}"

        # Clean up coverage file (there shouldn't be any, but just in case)
        coverage erase

        # Run preliminary tests
        coverage run -a "${CI_DIR}/test_test_manager.py"
        coverage run -a "${CI_DIR}/test_plugin_testcase.py"
        # append to coverage file, do not create final report
        pytest --cov=aiida --cov-append --cov-report= "${CI_DIR}/pytest"
        # rerun tests with existing profile
        #TEST_AIIDA_PROFILE=test_${TEST_AIIDA_BACKEND} pytest --cov=aiida --cov-append --cov-report= "${CI_DIR}/pytest"

        # Run verdi devel tests
        coverage run -a $VERDI -p test_${TEST_AIIDA_BACKEND} devel tests -v

        # Run the daemon tests using docker
        # Note: This is not a typo, the profile is called ${TEST_AIIDA_BACKEND}

        # In case of error, I do some debugging, but I make sure I anyway exit with an exit error
        coverage run -a $VERDI -p ${TEST_AIIDA_BACKEND} run "${CI_DIR}/test_daemon.py" || ( if which docker > /dev/null ; then docker ps -a ; docker exec torquesshmachine cat /var/log/syslog ; fi ; exit 1 )

        # Run the sphinxext tests, append to coverage file, do not create final report
        coverage run --append -m pytest aiida/sphinxext/tests

        # Now, we run all the tests and we manually create the final report
        # Note that this is only the partial coverage for this backend
        coverage report
        ;;
    pre-commit)
        pre-commit run --all-files || ( git status --short ; git diff ; exit 1 )
        ;;
    conda)
        # Note: Not added to install in order not to slow down other tests
        source ${CI_DIR}/install_conda.sh

        # Replace dep1 dep2 ... with your dependencies
        conda env create -f environment.yml -n test-environment python=$TRAVIS_PYTHON_VERSION
        source activate test-environment
        verdi --help
        ;;
esac
