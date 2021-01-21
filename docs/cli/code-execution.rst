Code Execution
==============

Compute sessions
----------------

.. note::

   Please consult the detailed usage in the help of each command.
   (use ``-h`` or ``--help`` argument to display the manual)

----------------
Listing sessions
----------------

List the session owned by you with various status filters.
The most recently status-changed sessions are listed first.
To prevent overloading the server, the result is limited to the first 10
sessions and it provides a separate ``--all`` option to paginate further
sessions.

.. code-block:: shell

  backend.ai ps

The ``ps`` command is an alias of the following ``admin sessions`` command.
If you have the administrator privilege, you can list sessions owned by
other users by adding ``--access-key`` option here.

.. code-block:: shell

  backend.ai admin sessions

Both commands offer options to set the status filter as follows.
For other options, please consult the output of ``--help``.

.. list-table::
   :widths: 15 85
   :header-rows: 1

   * - Option
     - Included Session Status

   * - (no option)
     - ``PENDING``, ``PREPARING``, ``RUNNING``, ``RESTARTING``,
       ``TERMINATING``, ``RESIZING``, ``SUSPENDED``, and ``ERROR``.

   * - ``--running``
     - ``PREPARING``, ``PULLING``, and ``RUNNING``.

   * - ``--dead``
     - ``CANCELLED`` and ``TERMINATED``.

Both commands offer options to specify which fields of sessions should be printed as follows.

.. list-table::
   :widths: 20 80
   :header-rows: 1

   * - Option
     - Included Session Fields

   * - (no option)
     - ``Session ID``, ``Owner``, ``Image``, ``Type``,

       ``Status``, ``Status Info``, ``Last updated``, and ``Result``.

   * - ``--name-only``
     - ``Display session names only``.

   * - ``--detail``
     - ``Session ID``, ``Owner``, ``Image``, ``Type``,

       ``Status``, ``Status Info``, ``Last updated``, ``Result``,

       ``Tag``, ``Created At``, ``Occupied Resource``, ``Used Memory (MiB)``,

       ``Max Used Memory (MiB)``, and ``CPU Using (%)``.

   * - ``-f``, ``--format``
     - Specified fields by user.
  
   * - ``--plain``
     - Display the session list without decorative line drawings and the header

.. note::
    Fields for ``-f/--format`` option can be displayed by specifying comma-separated parameters.

    Available parameters for this option are: ``id``, ``status``, ``status_info``, ``created_at``, ``last_updated``, ``result``, ``image``, ``type``, ``task_id``, ``tag``, ``occupied_slots``, ``used_memory``, ``max_used_memory``, ``cpu_using``.

    For example:

    .. code-block:: shell

        backend.ai admin session --format id,status,cpu_using

.. _simple-execution:

-----------------------
Running simple sessions
-----------------------

The following command spawns a Python session and executes
the code passed as ``-c`` argument immediately.
``--rm`` option states that the client automatically terminates
the session after execution finishes.

.. code-block:: shell

  backend.ai run --rm -c 'print("hello world")' python:3.6-ubuntu18.04

.. note::

   By default, you need to specify language with full version tag like
   ``python:3.6-ubuntu18.04``. Depending on the Backend.AI admin's language
   alias settings, this can be shortened just as ``python``. If you want
   to know defined language aliases, contact the admin of Backend.AI server.


The following command spawns a Python session and executes
the code passed as ``./myscript.py`` file, using the shell command
specified in the ``--exec`` option.

.. code-block:: shell

  backend.ai run --rm --exec 'python myscript.py arg1 arg2' \
             python:3.6-ubuntu18.04 ./myscript.py


Please note that your ``run`` command may hang up for a very long time
due to queueing when the cluster resource is not sufficiently available.

To avoid indefinite waiting, you may add ``--enqueue-only`` to return
immediately after posting the session creation request.

.. note::

   When using ``--enqueue-only``, the codes are *NOT* executed and relevant
   options are ignored.
   This makes the ``run`` command to the same of the ``start`` command.

Or, you may use ``--max-wait`` option to limit the maximum waiting time.
If the session starts within the given ``--max-wait`` seconds, it works
normally, but if not, it returns without code execution like when used
``--enqueue-only``.

To watch what is happening behind the scene until the session starts,
try ``backend.ai events <sessionID>`` to receive the lifecycle events
such as its scheduling and preparation steps.

----------------------------------
Running sessions with accelerators
----------------------------------

Use one or more ``-r`` options to specify resource requirements when
using ``backend.ai run`` and ``backend.ai start`` commands.

For instance, the following command spawns a Python TensorFlow session
using a half of virtual GPU device, 4 CPU cores, and 8 GiB of the main
memory to execute ``./mygpucode.py`` file inside it.

.. code-block:: shell

  backend.ai run --rm \
             -r cpu=4 -r mem=8g -r cuda.shares=2 \
             python-tensorflow:1.12-py36 ./mygpucode.py

----------------------------------
Terminating or cancelling sessions
----------------------------------

Without ``--rm`` option, your session remains alive for a configured
amount of idle timeout (default is 30 minutes).
You can see such sessions using the ``backend.ai ps`` command.
Use the following command to manually terminate them via their session
IDs.  You may specifcy multiple session IDs to terminate them at once.

.. code-block:: shell

  backend.ai rm <sessionID> [<sessionID>...]

If you terminate ``PENDING`` sessions which are not scheduled yet,
they are cancelled.

Also there are a lot of sub-commands for ``admin`` command. See the below commands

.. code-block:: shell

  backend.ai admin [command]

.. list-table::
  :widths: 15 85 
  :header-rows: 1

  * - Command
    - Description

  * - ``agent``
    - Show the information about the given agent.

  * - ``agents``
    - List and manage agents
  
  * - ``alias-image``
    - Add an image alias.

  * - ``dealias-image``
    - Remove an image alias.
  
  * - ``domain``
    - Show the information about the given domain.
  
  * - ``domains``
    - List and manage domains.
  
  * - ``etcd``
    - List and manage ETCD configurations
  
  * - ``group``
    - Show the information about the given group.
  
  * - ``groups``
    - List and manage groups
  
  * - ``images``
    - Show the list of registered images in this cluster.

  * - ``keypair``
    - Show the server-side information of the currently configured access key

  * - ``keypair-resource-policies``
    - List and manage keypair resource policies.
  
  * - ``keypair-resource-policy``
    - Show details about a keypair resource policy.
  
  * - ``keypairs``
    - List and manage keypairs.
  
  * - ``list-scaling-groups``
    - 
  
  * - ``rescan-images``
    - Update the kernel image metadata from all configured docker registries.

  * - ``resources``
    - Manage resources.
  
  * - ``scaling-group``
    - Show the information about the given scaling group. (superadmin privilege required)

  * - ``scaling-groups``
    - List and manage scaling groups.
  
  * - ``session``
    - Show detailed information for a running compute session.

  * - ``sessions``
    - List and manage compute sessions.
  
  * - ``show-license``
    - Show the license information (enterprise editions only).

  * - ``storage``
    - Show the information about the given storage volume. (super-admin privilege required)
  
  * - ``storage-list``
    - List storage volumes.
  
  * - ``user``
    - Show the information about the given user by email.

      If email is not give, requester's information will be displayed.
  
  * - ``users``
    - List and manage users.
  
  * - ``vfolders``
    - List and manage virtual folders.
  
  * - ``watcher``
    - Provides agent watcher operations.


Container Applications
----------------------

.. note::

   Please consult the detailed usage in the help of each command
   (use ``-h`` or ``--help`` argument to display the manual).

---------------------------------------------------------
Starting a session and connecting to its Jupyter Notebook
---------------------------------------------------------

The following command first spawns a Python session named "mysession"
without running any code immediately, and then executes a local proxy which
connects to the "jupyter" service running inside the session via the local
TCP port 9900.
The ``start`` command shows application services provided by the created
compute session so that you can choose one in the subsequent ``app``
command.
In the ``start`` command, you can specify detailed resource options using
``-r`` and storage mounts using ``-m`` parameter.

.. code-block:: shell

  backend.ai start -t mysession python
  backend.ai app -b 9900 mysession jupyter

Once executed, the ``app`` command waits for the user to open the displayed
address using appropriate application.
For the jupyter service, use your favorite web browser just like the
way you use Jupyter Notebooks.
To stop the ``app`` command, press ``Ctrl+C`` or send the ``SIGINT`` signal.

-------------------------------------
Accessing sessions via a web terminal
-------------------------------------

All Backend.AI sessions expose an intrinsic application named ``"ttyd"``.
It is an web application that embeds xterm.js-based full-screen terminal
that runs on web browsers.

.. code-block:: shell

   backend.ai start -t mysession ...
   backend.ai app -b 9900 mysession ttyd

Then open ``http://localhost:9900`` to access the shell in a fully
functional web terminal using browsers.
The default shell is ``/bin/bash`` for Ubuntu/CentOS-based images and
``/bin/ash`` for Alpine-based images with a fallback to ``/bin/sh``.

.. note::

   This shell access does *NOT* grant your root access.
   All compute session processes are executed as the user privilege.

Options for ``app`` commands

.. list-table::
  :widths: 15 85 
  :header-rows: 1

  * - Options
    - Description
  
  * - ``-p, --protocol [http|tcp|preopen]``
    - The application-level protocol to use.
  
  * - ``-b, --bind [HOST:]PORT``
    - The IP/host address and the port number to bind this proxy.
  
  * - ``--arg "--option <value>"``
    - Add additional argument when starting service.
  
  * - ``-e, --env "ENVNAME=envvalue"`` 
    - Add additional environment variable when starting service.

--------------------------------------
Accessing sessions via native SSH/SFTP
--------------------------------------

Backend.AI offers direct access to compute sessions (containers) via SSH
and SFTP, by auto-generating host identity and user keypairs for all
sessions.
All Baceknd.AI sessions expose an intrinsic application named ``"sshd"``
like ``"ttyd"``.

To connect your sessions with SSH, first prepare your session and download
an auto-generated SSH keypair named ``id_container``.
Then start the service port proxy ("app" command) to open a local TCP port
that proxies the SSH/SFTP traffic to the compute sessions:

.. code-block:: console

  $ backend.ai start -t mysess ...
  $ backend.ai download mysess id_container
  $ mv id_container ~/.ssh
  $ backend.ai app mysess sshd -b 9922

In another terminal on the same PC, run your ssh client like:

.. code-block:: console

  $ ssh -o StrictHostKeyChecking=no \
  >     -o UserKnownHostsFile=/dev/null \
  >     -i ~/.ssh/id_container \
  >     work@localhost -p 9922
  Warning: Permanently added '[127.0.0.1]:9922' (RSA) to the list of known hosts.
  f310e8dbce83:~$

This SSH port is also compatible with SFTP to browse the container's
filesystem and to upload/download large-sized files.

You could add the following to your ``~/.ssh/config`` to avoid type
extra options every time.

.. code-block:: text

  Host localhost
    User work
    IdentityFile ~/.ssh/id_container
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null

.. code-block:: console

  $ ssh localhost -p 9922

.. warning::

   Since the SSH keypair is auto-generated every time when your launch a
   new compute session, you need to download and keep it separately for
   each session.

To use your own SSH private key across all your sessions without
downloading the auto-generated one every time, create a vfolder named
``.ssh`` and put the ``authorized_keys`` file that includes the public key.
The keypair and ``.ssh`` directory permissions will be automatically
updated by Backend.AI when the session launches.

.. code-block:: console

  $ ssh-keygen -t rsa -b 2048 -f id_container
  $ cat id_container.pub > authorized_keys
  $ backend.ai vfolder create .ssh
  $ backend.ai vfolder upload .ssh authorized_keys

There is only one options for command ``ssh``

.. list-table::
  :widths: 15 85 
  :header-rows: 1

  * - Option
    - Description

  * - ``-p, --port PORT``
    - The port number for localhost

There are many options for command ``start``. See the below table.

.. list-table::
  :widths: 15 85 
  :header-rows: 1

  * - Option
    - Description

  * - ``-t, --name, --client-token name``
    - Specify a human-readable session name. If not set, a random hex string is used.
  
  * - ``-o, --owner, --owner-access-key ACCESS_KEY``
    - Set the owner of the target session explicitly.
  
  * - ``--type SESSTYPE``
    - Either batch or interactive

  * - ``--starts-at STARTS_AT``
    - Let session to be started at a specific or relative time.
  
  * - ``-c, --startup-command COMMAND`` 
    - Set the command to execute for batch-type sessions.

  * - ``--enqueue-only``
    - Enqueue the session and return immediately without waiting for its startup.
  
  * - ``--max-wait SECONDS``
    - The maximum duration to wait until the session starts.

  * - ``--no-reuse``
    - Do not reuse existing sessions but return an error.

  * - ``-e, --env KEY=VAL``
    - Environment variable (may appear multiple times)

  * - ``--bootstrap-script PATH, --tag TEXT``
    - A user-defined script to execute on startup. User-defined tag string to annotate sessions.

  * - ``-v, -m, --volume, --mount NAME[=PATH]``
    - User-owned virtual folder names to mount. 
      
      If path is not provided, virtual folder will be mounted under ``/home/work``. 
      
      All virtual folders can only be mounted under ``/home/work``.

  * - ``--scaling-group, --sgroup TEXT``
    - The scaling group to execute session. If not specified, all available scaling groups are included in the scheduling.

  * - ``-r, --resources KEY=VAL``
    - Set computation resources used by the session (e.g: -r cpu=2 -r mem=256 -r gpu=1).1 slot of cpu/gpu represents 1 core. 
      The unit of mem(ory) is MiB.

  * - ``--cluster-size NUMBER``
    - The size of cluster in number of containers.
  
  * - ``--cluster-mode MODE``
    - The mode of clustering.
  
  * - ``--resource-opts KEY=VAL``
    - Resource options for creating compute session (e.g: shmem=64m)

  * - ``-d, --domain DOMAIN_NAME``
    - Domain name where the session will be spawned. If not specified, config's domain name will be used.

  * - ``-g, --group GROUP_NAME``
    - GROUP name where the session is spawned. User should be a member of the group to execute the code.
  
  * - ``--preopen TEXT``
    - Pre-open service ports

Advanced Code Execution
-----------------------

.. note::

   Please consult the detailed usage in the help of each command
   (use ``-h`` or ``--help`` argument to display the manual).

--------------------------------------
Running concurrent experiment sessions
--------------------------------------

In addition to single-shot code execution as described in
:ref:`simple-execution`, the ``run`` command offers concurrent execution of
multiple sessions with different parameters interpolated in the execution
command specified in ``--exec`` option and environment variables specified
as ``-e`` / ``--env`` options.

To define variables interpolated in the ``--exec`` option, use ``--exec-range``.
To define variables interpolated in the ``--env`` options, use ``--env-range``.

Here is an example with environment variable ranges that expands into 4
concurrent sessions.

.. code-block:: shell

  backend.ai run -c 'import os; print("Hello world, {}".format(os.environ["CASENO"]))' \
      -r cpu=1 -r mem=256m \
      -e 'CASENO=$X' \
      --env-range=X=case:1,2,3,4 \
      lablup/python:3.6-ubuntu18.04

Both range options accept a special form of argument: "range expressions".
The front part of range option value consists of the variable name used for
interpolation and an equivalence sign (``=``).
The rest of range expressions have the following three types:

.. list-table::
   :widths: 24 76
   :header-rows: 1

   * - Expression
     - Interpretation

   * - ``case:CASE1,CASE2,...,CASEN``
     - A list of discrete values. The values may be either string or numbers.

   * - ``linspace:START,STOP,POINTS``
     - An inclusive numerical range with discrete points, in the same way
       of ``numpy.linspace()``.  For example, ``linspace:1,2,3`` generates
       a list of three values: 1, 1.5, and 2.

   * - ``range:START,STOP,STEP``
     - A numerical range with the same semantics of Python's :func:`range`.
       For example, ``range:1,6,2`` generates a list of values:
       1, 3, and 5.

If you specify multiple occurrences of range options in the ``run``
command, the client spawns sessions for *all possible combinations* of all
values specified by each range.

.. note::

  When your resource limit and cluster's resource capacity cannot run all
  spawned sessions at the same time, some of sessions may be queued and the
  command may take a long time to finish.

.. warning::

  Until all cases finish, the client must keep its network connections to
  the server alive because this feature is implemented in the client-side.
  Server-side batch job scheduling is under development!

Session Templates
-----------------

--------------------------------------
Creating and starting session template
--------------------------------------

Users may define commonly used set of session creation parameters as
reusable templates.

A session template includes common session parameters such as resource
slots, vfolder mounts, the kernel iamge to use, and etc.
It also support an extra feature that automatically clones a Git repository
upon startup as a bootstrap command.

The following sample shows how a session template looks like:

.. code-block:: yaml

  ---
  api_version: v1
  kind: taskTemplate
  metadata:
    name: template1234
    tag: example-tag
  spec:
    kernel:
      environ:
        MYCONFIG: XXX
      git:
        branch: '19.09'
        commit: 10daee9e328876d75e6d0fa4998d4456711730db
        repository: https://github.com/lablup/backend.ai-agent
        destinationDir: /home/work/baiagent
      image: python:3.6-ubuntu18.04
    resources:
      cpu: '2'
      mem: 4g
    mounts:
      hostpath-test: /home/work/hostDesktop
      test-vfolder:
    sessionType: interactive

The ``backend.ai sesstpl`` command set provides the basic CRUD operations
of user-specific session templates.

The ``create`` command accepts the YAML content either piped from the
standard input or read from a file using ``-f`` flag:

.. code-block:: console

  $ backend.ai sesstpl create < session-template.yaml
  # -- or --
  $ backend.ai sesstpl create -f session-template.yaml

Once the session template is uploaded, you may use it to start a new
session:

.. code-block:: console

  $ backend.ai start-template <templateId>

with substituting ``<templateId>`` to your template ID.

Other CRUD command examples are as follows:

.. code-block:: console

  $ backend.ai sesstpl update <templateId> < session-template.yaml
  $ backend.ai sesstpl list
  $ backend.ai sesstpl get <templateId>
  $ backend.ai sesstpl delete <templateId>

.. list-table::
  :widths: 15 85 
  :header-rows: 1

  * - Command
    - Description

  * - ``create``
    - Store task template to Backend.AI Manager and return template ID.
  
  * - ``delete``
    - Delete task template from Backend.AI Manager.
  
  * - ``get``
    - Print task template associated with given template ID
  
  * - ``list``
    - List all availabe task templates by user.
  
  * - ``update``
    - Update task template stored in Backend.AI Manager.
-----------------------------
Full syntax for task template
-----------------------------

.. code-block:: text

  ---
  api_version or apiVersion: str, required
  kind: Enum['taskTemplate', 'task_template'], required
  metadata: required
    name: str, required
    tag: str (optional)
  spec:
    type or sessionType: Enum['interactive', 'batch'] (optional), default=interactive
    kernel:
      image: str, required
      environ: map[str, str] (optional)
      run: (optional)
        bootstrap: str (optional)
        stratup or startup_command or startupCommand: str (optional)
      git: (optional)
        repository: str, required
        commit: str (optional)
        branch: str (optional)
        credential: (optional)
          username: str
          password: str
        destination_dir or destinationDir: str (optional)
    mounts: map[str, str] (optional)
    resources: map[str, str] (optional)

Command Reference
-----------------

.. list-table::
   :widths: 15 85 
   :header-rows: 1

   * - Command
     - Description
   
   * - ``admin``
     - Provides the ``admin API access``.

   * - ``announcement``
     - Global announcement related commands.

   * - ``app``
     - Run a local proxy to a service provided by Backend.
       AI compute sessions.
       
       The type of proxy depends on the app definition: plain TCP or HTTP.

       ``SESSID``: The compute session ID.
       
       ``APP``: The name of service provided by the given session.
   * - ``apps``
     - List available additional arguments and environment variables when
       starting service.

       ``SESSID``: The compute session ID.

       ``APP``: The name of service provided by the given session. Repeatable.
       
       If none provided, this will print all available services.

   * - ``dotfile``
     - Provides dotfile operations.

   * - ``download``
     - Download files from a running container.
   
   * - ``events``
     - Monitor the lifecycle events of a compute session.

       ``SESSID``: session ID or its alias given when creating the session.
   
   * - ``info``
     - Show detailed information for a running compute session. This is an alias
       of the "admin session ``<sess_id>``" command.

       ``SESSID``: session ID or its alias given when creating the session.

   * - ``logs``
     - Shows the output logs of a running container.

       ``SESSID``: Session ID or its alias given when creating the session.

   * - ``ls``
     - List files in a path of a running container.

   * - ``manager``
     - Provides manager-related operations.

   * - ``proxy``
     - Run a non-encrypted non-authorized API proxy server. Use this only for
       development and testing!

   * - ``ps``
     - Lists the current running compute sessions for the current keypair. 

       This is an alias of the "admin sessions --status=RUNNING" command.

   * - ``restart``
     - Restart the given session.

   * - ``run``
     - Run the given code snippet or files in a session. 

       Depending on the session ID you give (default is random), it may reuse an existing session or
       create a new one.

       ``IMAGE``: The name (and version/platform tags appended after a colon) of session
       runtime or programming language.')
  
       ``FILES``: The code file(s). Can be added multiple times.   
   
   * - ``scp``
     - Execute the scp command against the target compute session.

       The SRC and DST have the same format with the original scp command,
       either a remote path as "work@localhost:path" or a local path.

       ``SESSION_REF``: The user-provided name or the unique ID of a running compute session. 
       
       ``SRC``: the source path 
       
       ``DST``: the destination path

       All remaining options and arguments not listed here are passed to the ssh
       command as-is.

       Examples:

       Uploading a local directory to the session:
          
       .. code-block:: shell

         backend.ai scp mysess -p 9922 -r tmp/ work@localhost:tmp2/
          
       Downloading a directory from the session:

       .. code-block:: shell

         backend.ai scp mysess -p 9922 -r work@localhost:tmp2/ tmp/
   
   * - ``server-logs``
     - Provides operations related to server logs.

   * - ``session-template (sesstpl)``
     - Provides task template operations

   * - ``ssh``
     - Execute the ssh command against the target compute session

       ``SESSION_REF``: The user-provided name or the unique ID of a running compute session.

       All remaining options and arguments not listed here are passed to the ssh
       command as-is.

   * - ``start``, ``start-template``
     - Prepare and start a single compute session without executing codes. You
       may use the created session to execute codes using the ``"run"`` command or
       connect to an application service provided by the session using the "app"
       command.

       ``IMAGE``: The name (and version/platform tags appended after a colon) of session
       runtime or programming language.
   
   * - ``task-logs``
     - Shows the output logs of a batch task.

   * - ``terminate (kill,rm)``
     - Terminate the given session.

   * - ``update-passwor``
     - Update user's password.
  
   * - ``upload``
     - Upload files to user's home folder.

