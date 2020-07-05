.. _how-to:setup_computer:

***********************
How to setup a computer
***********************

A |Computer| in AiiDA denotes a computational resource on which you will run your calculations.
It can either be

 1. the machine where AiiDA is installed or
 2. any machine that is accessible via `SSH <https://en.wikipedia.org/wiki/Secure_Shell>`_ from the machine where AiiDA is installed.

The second option allows managing multiple remote compute resources (including HPC clusters and cloud services) from the same AiiDA installation and moving computational jobs between them.

.. tip::

    The second option requires access through a SSH keypair.
    If your compute resource demands two-factor authentication, you may need to install AiiDA directly on the compute resource instead.

Computer requirements
=====================

Requirements for configuring a compute resource in AiiDA are:

* It runs a Unix-like operating system (Linux distros and MacOS will work fine)
* It has ``bash`` installed
* (option 2.) It is accessible via SSH from the machine that runs AiiDA (possibly :ref:`via a proxy server<how-to:ssh:proxy>`)
* (optional) It has batch scheduler installed (see the :ref:`list of supported schedulers <topics:schedulers>`)

If you are configuring a remote computer, start by :ref:`configuring passwordless SSH access <how-to:ssh>` to it.

.. note::

    AiiDA will use ``bash`` on the remote computer, regardless of the default shell.
    Please ensure that your remote ``bash`` configuration does not load a different shell.

Computer setup and configuration
================================

The configuration of computers happens in two steps: first, setting up the public metadata asociated with the |Computer| in AiiDA provenance graphs, and second, configuring private connection details.

Throughout the process you will be prompted for information on the computer and on how to access it.

.. tip::

   Type ``?`` followed by ``<enter>`` to get help on what is being asked at any prompt.

.. tip::

   Press ``<CTRL>+C`` at any moment to abort the setup process.
   Your AiiDA database will remain unmodified.

.. note::

  The ``verdi computer`` command uses ``readline`` extensions to provide default answers, that require an advanced terminal.
  Use a standard terminal -- terminals embedded in some text editors (such as ``emacs``) have been known to cause problems.

.. _how-to:setup_computer:setup:

Setup of the computer
---------------------

Start by creating a new computer instance in the database:

.. code-block:: console

   $ verdi computer setup

At the end, the command will open your default editor on a file containing a summary of the configuration up to this point.
You can add ``bash`` commands that will be executed either *before* the actual execution of the job (under 'Pre-execution script') or *after* the script submission (under 'Post execution script').
Use these additional lines to perform any further set up of the environment on the computer, for example loading modules or exporting environment variables:

.. code-block:: bash

   export NEWVAR=1
   source some/file

.. note::

   Don't specify settings here that are specific to a code, calculation or scheduler: you can set further pre-execution commands at the ``Code`` and even ``CalcJob`` level.

When you are done editing, save and quit (e.g. ``<ESC>:wq<ENTER>`` in ``vim``).
The computer has now been created in the database but you still need to *configure* access to it using your credentials.

.. tip::
    In order to avoid having to retype the setup information the next time round, you can provide some (or all) of the information via a configuration file:

    .. code-block:: console

       $ verdi computer setup --config computer.yml

    where ``computer.yml`` is a configuration file in the `YAML format <https://en.wikipedia.org/wiki/YAML#Syntax>`__.
    This file contains the information in a series of key:value pairs:

    .. code-block:: yaml

       ---
       label: "localhost"
       hostname: "localhost"
       transport: local
       scheduler: "direct"
       work_dir: "/home/max/.aiida_run"
       mpirun_command: "mpirun -np {tot_num_mpiprocs}"
       mpiprocs_per_machine: "2"
       prepend_text: |
          module load mymodule
          export NEWVAR=1

   The list of the keys for the ``yaml`` file is given by the options of the ``computer setup`` command:

   .. code-block:: console

      $ verdi computer setup --help

   Note: Remove the ``--`` prefix and replace ``-`` within the keys by the underscore ``_``.

.. _how-to:setup_computer:configuration:

Configuration of the computer
------------------------------

The second step configures private connection details using:

.. code-block:: console

   $ verdi computer configure TRANSPORTTYPE COMPUTERNAME

with the appropriate transport type (``local`` for option 1., ``ssh`` for option 2.) and computer label.

After setup and configuration have been completed, let AiiDA check if everything is working properly:

.. code-block:: console

   $ verdi computer test COMPUTERNAME

This will test logging in, copying files, and checking the jobs in the scheduler queue.


Inspecting your computers
=========================

If you are unsure whether your computer is already set up, list configured computers with:

.. code-block:: console

   $ verdi computer list

To get detailed information on the specific computer named ``COMPUTERNAME``:

.. code-block:: console

   $ verdi computer show COMPUTERNAME

To rename a computer or remove it from the database:

.. code-block:: console

   $ verdi computer rename OLDCOMPUTERNAME NEWCOMPUTERNAME
   $ verdi computer delete COMPUTERNAME

.. note::

   Before deleting a |Computer|, you will need to delete *all* nodes linked to it (e.g. any ``CalcJob`` and ``RemoteData`` nodes).
   Otherwise, AiiDA will prevent you from doing so in order to preserve provenance.

If a remote machine is under maintenance (or no longer operational), you may want to **disable** the corresponding |Computer|.
Doing so will prevent AiiDA from connecting to the given computer to check the state of calculations or to submit new calculations.

.. code-block:: console

   $ verdi computer disable COMPUTERNAME
   $ verdi computer enable COMPUTERNAME

.. important::

   The above commands will disable the computer for **all** AiiDA users on your profile.

.. _how-to:setup_computer:overloads:

Avoiding overloads
==================

Some compute resources, particularly large supercomputing centres, may not tolerate submitting too many jobs at once, executing scheduler commands too frequently or opening too many SSH connections.

  * Limit the number of jobs in the queue.

    Set yourself a limit for the maximum number of workflows to submit, and submit new ones only once previous workflows start to complete (in the future `this might be dealt with by AiiDA automatically <https://github.com/aiidateam/aiida-core/issues/88>`_).
    The supported number of jobs depends on your supercomputer - discuss this with your supercomputer administrators (`this page <https://github.com/aiidateam/aiida-core/wiki/Optimising-the-SLURM-scheduler-configuration-(for-cluster-administrators)>`_ may contain useful information for them).

  * Increase the time interval between polling the job queue.

    The time interval (in seconds) can be set through the python API by loading the corresponding |Computer| node, e.g. in the ``verdi shell``:

    .. code-block:: python

        load_computer('fidis').set_minimum_job_poll_interval(30.0)


  * Increase the connection cooldown time.

    This is the minimum time (in seconds) to wait between opening a new connection.
    Modify it for an existing computer using:

    .. code-block:: bash

      verdi computer configure ssh --non-interactive --safe-interval <SECONDS> <COMPUTER_NAME>


.. important::

    The two intervals apply *per daemon worker*, i.e. doubling the number of workers may end up putting twice the load on the remote computer.


.. |Code| replace:: :py:class:`~aiida.orm.nodes.data.Code`
.. |Computer| replace:: :py:class:`~aiida.orm.Computer`
