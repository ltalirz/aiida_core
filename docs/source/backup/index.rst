.. _backup:

AiiDA stores information in

 * the ``.aiida`` folder, typically located at ``~/.aiida`` (see also :ref:`configure_aiida`).
   This contains the configuration of the profiles as well as their associated file repositories.
 * the PostgreSQL database (one database per profile).

Both are required for the operation of AiiDA and below we explain how to back up and restore both of them.

.. _repository_backup:

Repository backup (``.aiida`` folder)
++++++++++++++++++++++++++++++++++++++

For small repositories you can simply back up the ``.aiida``, either by making a full copy or using tools for incremental backups like ``rsync``.

For large repositories with 100k nodes or more, incremental backups can take a significant amount of time, and AiiDA provides a helper script that takes advantage of the AiiDA database in order to figure out which files have been added since your last backup. The instructions below explain how to use it.


 1. Configure your backup:
	verdi -p PROFILENAME run MY_AIIDA_FOLDER/aiida/manage/backup/backup_setup.py

    | where PROFILENAME is the name of the profile that should be backed up.
    | This will ask for information on:

      * The "backup folder", where the backup *configuration file* will be placed.
        This defaults to a folder named ``backup_PROFILENAME`` in your ``.aiida`` directory.

      * The "destination folder", where the files of the backup will be stored.
        This defaults to the same folder as above but we **strongly suggest to back up to a different drive** (see note below).

    A template backup configuration file (``backup_info.json.tmpl``) will be created in the backup folder.
    You can set the backup variables by yourself after renaming the template file to ``backup_info.json``, or you can answer the questions asked by the script, and then ``backup_info.json`` will be created based on your answers.

.. note::

  Using the same disk for your backup forgoes protection against the most common cause of data loss: disk failure.
  One simple option is to use a destination folder mounted over ssh.

  On Ubuntu, install ``sshfs`` using ``sudo apt-get install sshfs``.

  Imagine you run your calculations on `server_1` and would like to back up regularly to `server_2`.
  Mount a `server_2` directory on `server_1` using the following command on `server_1`:

  .. code-block:: shell

    sshfs -o idmap=user -o rw backup_user@server_2:/home/backup_user/backup_destination_dir/ /home/aiida_user/remote_backup_dir/

  Use ``gnome-session-properties`` in the terminal to add this line to the actions performed at start-up.
  Do **not** add it to your shell's startup file (e.g. ``.bashrc``) or your computer will complain that the mount point is not empty whenever you open a new terminal...

The main script will backup the AiiDA repository that is referenced by the current AiiDA database.
The script will start from the ``oldest_object_backedup`` date, or the date of the oldest Node object found, and it will periodically backup (in periods of ``periodicity`` days) until the end date of the backup specified by ``end_date_of_backup`` or ``days_to_backup``.

The backup parameters to be set in the ``backup_info.json`` are:

* | ``periodicity`` (in `days`):
  | The backup runs periodically for a number of days defined in the periodicity variable.
    The purpose of this variable is to limit the backup to run only on a few number of days and therefore to limit the number of files that are backed up at every round.
  | E.g. ``"periodicity": 2``.
  | Example:
  | If you have files in the AiiDA repositories created in the past 30 days, and periodicity is 15, the first run will backup the files of the first 15 days; a second run of the script will backup the next 15 days, completing the backup (if it is run within the same day).
    Further runs will only backup newer files, if they are created.

* | ``oldest_object_backedup`` (`timestamp` or ``null``):
  | This is the timestamp of the oldest object that was backed up.
    If you are not aware of this value or if it is the first time you start a backup for this repository, then set this value to ``null``.
    Then the script will search the creation date of the oldest Node object in the database and start the backup from that date.
  | E.g. ``"oldest_object_backedup": "2015-07-20 11:13:08.145804+02:00"``

* | ``end_date_of_backup`` (`timestamp` or ``null``):
  | If set, the backup script will backup files that have a modification date up until the value specified by this variable.
    If not set, the ending of the backup will be set by the ``days_to_backup`` variable, which specifies how many days to backup from the start of the backup.
    If none of these variables are set (``end_date_of_backup`` and ``days_to_backup``), then the end date of backup is set to the current date.
  | E.g. ``"end_date_of_backup": null`` or ``"end_date_of_backup": "2015-07-20 11:13:08.145804+02:00"``.

* | ``days_to_backup`` (in `days` or ``null``):
  | If set, you specify how many days you will backup from the starting date of your backup.
    If it is set to ``null`` and also ``end_date_of_backup`` is set to ``null``, then the end date of the backup is set to the current date.
    You can not set ``days_to_backup`` & ``end_date_of_backup`` at the same time (it will lead to an error).
  | E.g. ``"days_to_backup": null`` or ``"days_to_backup": 5``.

* | ``backup_length_threshold`` (in `hours`):
  | The backup script runs in rounds and on every round it will backup a number of days that are controlled primarily by ``periodicity`` and also by ``end_date_of_backup`` / ``days_to_backup``, for the last backup round.
    The ``backup_length_threshold`` specifies the *lowest acceptable* round length.
    This is important for the end of the backup.
  | E.g. ``backup_length_threshold: 1``

* | ``backup_dir`` (absolute path):
  | The destination directory of the backup.
  | E.g. ``"backup_dir": "/home/USERNAME/.aiida/backup/backup_dest"``.

To start the backup, run the ``start_backup.py`` script.
Run as often as needed to complete a full backup, and then run it periodically (e.g. calling it from a cron script, for instance every day) to backup new changes.

.. note::

  You can set up a cron job using the following command::

    sudo crontab -u USERNAME -e

  It will open an editor, where you can add a line of the form::

    00 03 * * * /home/USERNAME/.aiida/backup/start_backup.py 2>&1 | mail -s "Incremental backup of the repository" USER_EMAIL@domain.net

  or (if you need to backup a different profile than the default one)::

    00 03 * * * verdi -p PROFILENAME run /home/USERNAME/.aiida/backup/start_backup.py 2>&1 | mail -s "Incremental backup of the repository" USER_EMAIL@domain.net

  This will launch the backup of the database every day at 3 AM (03:00), and send the output (or any error message) to the email address specified at the end (provided the ``mail`` command -- from ``mailutils`` -- is configured appropriately).

Finally, do not forget to exclude the repository folder from the normal backup of your home directory!

.. _backup_postgresql:

Create database backup
++++++++++++++++++++++

| The instructions below have been tested under Ubuntu 12.04 and 18.04.
| In the following, we assume your database is called ``aiidadb``, and the database user and owner is ``aiida``.

The database information is typically stored in system directories and spread over multiple files that, if backed up as they are at any given time, cannot be used to restore the database.
It is therefore strongly recommended to periodically (typically once a day) dump the database contents to a file that will be backed up,
using a bash script similar to :download:`backup_postgresql.sh <backup_postgresql.sh>`:

.. _backup_script:

.. literalinclude:: backup_postgresql.sh
   :language: shell

In order to avoid having to enter your database password each time you use the script, create a file :download:`.pgpass <pgpass>` in your home directory:

.. literalinclude:: pgpass

where ``YOUR_DATABASE_PASSWORD`` is the password you set up for the database.

.. note::

  This file needs read and write permissions: ``chmod u=rw .pgpass``.

In order to automatically dump the database to a file ``i~/.aiida/${AIIDADB}-backup.psql.gz`` once per day,
add the following script :download:`backup-aiidadb-USERNAME <backup-aiidadb-USERNAME>` to the folder ``/etc/cron.daily/``:

.. literalinclude:: backup-aiidadb-USERNAME
   :language: shell

where all instances of ``USERNAME`` must replaced by your actual user name.
The ``su USERNAME`` makes you the owner of the file rather than ``root``.
Remember to give the script execute permissions::

  sudo chmod +x /etc/cron.daily/backup-aiidadb-USERNAME

Finally make sure your database folder (``/home/USERNAME/.aiida/``) containing this dump file and the ``repository`` directory, is properly backed up by your backup software (under Ubuntu, 12.04: Backup -> check the "Folders" tab, 18.04: Backups -> check the "Folder to save" tab).

.. note::

  If your database is very large (more than a few hundreds of thousands of nodes), a standard backup of your repository folder will be very slow (up to days), thus slowing down your computer dramatically.
  To fix this problem you can set up an incremental backup of your repository by following the instructions :ref:`here <repository_backup>`.

.. _restore_postgresql:

Restore database backup
+++++++++++++++++++++++

| In order to retrieve the database from a backup, you have to first extract the gzipped file created by the :ref:`backup script <backup_script>` (should be created in ``~/.aiida/``).
| Then you must create an empty database following the instructions described in :ref:`database` skipping the ``verdi setup`` phase.
  The database should have the same name as the backed up one, and also the same database username, i.e. you may have to either rename or delete your existing database.

``cd`` to the folder of the extracted backup file (``aiidadb-backup.psql``) and, while still acting as the postgres user, type the following command::

  psql -h localhost -U aiida -d aiidadb -f aiidadb-backup.psql

After supplying your database password, this will apply all commands from your backup file to the database ``aiidadb``.

.. note::

  To act as the postgres user, type in ``su - postgres`` or ``sudo su - postgres`` (depending on your distribution).

  Another way of doing this without having to become the postgres user (on Ubuntu 18.04) is::

    sudo -u postgres -- psql -h localhost -U aiida -d aiidadb -f aiidadb-backup.psql


.. _move_postgresql:

Move database
+++++++++++++

It might happen that you need to move the physical location of the database files on your hard-drive (for instance, due to the lack of space in the partition where it is located).

First, make sure you have a backup of the full database (see instructions :ref:`here <backup_postgresql>`), and that the AiiDA daemon is not running.
Then, become the UNIX ``postgres`` user, typing as root::

  su - postgres

(or, equivalently, type ``sudo su - postgres``, depending on your distribution).

Then enter the postgres shell::

  psql

and look for the current location of the data directory::

  SHOW data_directory;

Typically, you should get something like ``/var/lib/postgresql/9.1/main`` or ``/scratch/postgres/9.6/main``.

.. note:: In the above, ``9.1`` or ``9.6`` is replaced by the actual version number of your postgres distribution (the same applies to the remainder of the section).

.. note:: If you are experiencing memory problems and cannot enter the postgres shell, you can look directly into the file ``/etc/postgresql/9.6/main/postgresql.conf`` and check out the line defining the variable ``data_directory``.

Then exit the shell with ``\q`` and stop the postgres database daemon::

  service postgresql stop

Copy all the files and folders from the postgres data directory into the new directory::

  cp -a SOURCE_DIRECTORY DESTINATION_DIRECTORY

where ``SOURCE_DIRECTORY`` is the directory you got from the ``SHOW data_directory;`` command, and ``DESTINATION_DIRECTORY`` is the new directory for the database files.

.. note:: The behaviour of the ``cp -a`` command is to create a directory within ``DESTINATION_DIRECTORY``, e.g.::

    cp -a OLD_DIR/main/ NEW_DIR/

  will create the directory ``main`` under ``NEW_DIR``.

Make sure the permissions for owner and group are the same in the old and new directory (including all levels below the ``DESTINATION_DIRECTORY``).
The owner and group should be both ``postgres``, at the notable exception of some symbolic links in ``server.crt`` and ``server.key`` (these files might be absent, depending on your postgresql version number).

.. note::

  If the permissions of these links need to be changed, use the ``-h`` option of ``chown`` to avoid changing the permissions of the destination of the links.
  In case you have changed the permission of the links destination by mistake, they should typically be (beware that this might depend on your actual distribution!)::

    -rw-r--r-- 1 root root 989 Mar  1  2012 /etc/ssl/certs/ssl-cert-snakeoil.pem
    -rw-r----- 1 root ssl-cert 1704 Mar  1  2012 /etc/ssl/private/ssl-cert-snakeoil.key

Then you can change the postgres configuration file, which should typically be located at ``/etc/postgresql/9.6/main/postgresql.conf``.

Make a backup version of this file, then look for the line defining ``data_directory`` and replace it with the new data directory path::

   data_directory = 'NEW_DATA_DIRECTORY'

Now restart the database daemon::

  service postgresql start

Finally, you can check that the data directory has indeed changed::

  psql
  SHOW data_directory;
  \q

Before definitively removing the previous location of the database files, first rename it and test AiiDA with the new database location (e.g. do simple queries like ``verdi code list`` or create a node and store it).
If everything went fine, you can delete the old database location.
