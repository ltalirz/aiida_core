.. _how-to:setup_code:

*******************
How to setup a code
*******************

Once you have at least one computer configured (see :ref:`how-to:setup_computer`), you can configure codes on it.

AiiDA stores a set of metadata for each code, which is attached automatically to each calculation using it.
Besides being important for reproducibility, this also makes it easy to query for all calculations that were run with a given code (for instance, if a specific version was discovered to contain a bug).

AiiDA distinguishes two types of codes: **remote** codes and **local** codes, where the distinction between the two is described here below.


Setting up a code
-----------------

The ``verdi code`` CLI is the access point for managing codes in AiiDA.
To setup a new code, execute:

.. code-block:: console

   $ verdi code setup

and you will be guided through a process to setup your code.

.. admonition:: Getting help
    :class: tip title-icon-lightbulb

    At every prompt, you can type the ``?`` character and press ``<enter>`` to get a more detailed explanation of what is being asked.


.. admonition:: On remote and local codes
    :class: tip title-icon-lightbulb

    In most cases, it is advisable to install the executables to be used by AiiDA on the target machine *before* submitting calculations using them in order to take advantage of the compilers and libraries present on the target machine.
    This setup is referred to as *remote* codes (``Installed on target computer?: True``).

    Occasionally, you may need to run small, reasonably machine-independent scripts (e.g. Python or bash), and copying them manually to a number of different target computers can be tedious.
    For this use case, AiiDA provides *local* codes (``Installed on target computer?: False``).
    Local codes are stored in the AiiDA file repository and copied to the target computer for every execution.

    Do *not* use local codes as a way of encapsulating the environment of complex executables.
    Containers are a much better solution to this problem, and we are working on adding native support for containers in AiiDA.


At the end of these steps, you will be prompted to edit a script, where you can include ``bash`` commands that will be executed

 * *before* running the submission script (after the 'Pre execution script' lines), and
 * *after* running the submission script (after the 'Post execution script' separator).

Use this for instance to load modules or set variables that are needed by the code, e.g.:

.. code-block:: bash

    module load intelmpi

At the end, you receive a confirmation, with the *PK* and the *UUID* of your new code.
You are ready to launch your calculations!

.. admonition:: Where Next?
    :class: seealso title-icon-read-more

    Try running a basic Calcjob in the :ref:`introductory tutorial <tutorial:basic:calcjob>`, or find more information about running external codes in :ref:`this howto <how-to:codes>`.

.. admonition:: Using configuration files
    :class: tip title-icon-lightbulb

  Analogous to a :ref:`computer setup <how-to:setup_computer>`, some (or all) the information described above can be provided via a configuration file:

  .. code-block:: console

     $ verdi code setup --config code.yml

  where ``code.yml`` is a configuration file in the `YAML format <https://en.wikipedia.org/wiki/YAML#Syntax>`_.

  This file contains the information in a series of key:value pairs:

  .. code-block:: yaml

      ---
      label: "qe-6.3-pw"
      description: "quantum_espresso v6.3"
      input_plugin: "quantumespresso.pw"
      on_computer: true
      remote_abs_path: "/path/to/code/pw.x"
      computer: "localhost"
      prepend_text: |
        module load module1
        module load module2
      append_text: " "

  The list of the keys for the ``yaml`` file is given by the available options of the ``code setup`` command:

  .. code-block:: console

    $ verdi code setup --help

  Note: Remove the ``--`` prefix and replace ``-`` within the keys by the underscore ``_``.



Managing codes
--------------

You can change the label of a code by using the following command:

.. code-block:: console

  $ verdi code relabel <IDENTIFIER> "new-label"

where <IDENTIFIER> can be the numeric *PK*, the *UUID* or the label of the code (either ``label`` or ``label@computername``) if the label is unique.

You can also list all available codes and their identifiers with:

.. code-block:: console

  $ verdi code list

which also accepts flags to filter only codes on a given computer, or only codes using a specific plugin, etc. (use the ``-h`` option).

You can get the information of a specific code with:

.. code-block:: console

  $ verdi code show <IDENTIFIER>

Finally, to delete a code use:

.. code-block:: console

  $ verdi code delete <IDENTIFIER>

(only if it wasn't used by any calculation, otherwise an exception is raised).

.. note::

  Codes are a subclass of :py:class:`Node <aiida.orm.nodes.Node>` and, as such, you can attach ``extras`` to a code, for example:

  .. code-block:: python

      load_code('<IDENTIFIER>').set_extra('version', '6.1')
      load_code('<IDENTIFIER>').set_extra('family', 'cp2k')

  These can be useful for querying, for instance in order to find all runs done with the CP2K code of version 6.1 or later.
