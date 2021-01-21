Configuration
=============

.. note::

   Please consult the detailed usage in the help of each command
   (use ``-h`` or ``--help`` argument to display the manual).

Check out :doc:`the client configuration </gsg/config>` for configurations via environment variables.

API Mode : Useage
---------------------
You should set the access key and secret key as environment variables to use the API. Grab your keypair from cloud.backend.ai or your cluster admin.

On Linux/macOS, create a shell script as 'my-backend-ai.sh' and run it before using the backend.ai command:

.. code-block:: console

   export BACKEND_ACCESS_KEY=...
   export BACKEND_SECRET_KEY=...
   export BACKEND_ENDPOINT=https://my-precious-cluster
   export BACKEND_ENDPOINT_TYPE=api

Session Mode : Useage
---------------------
Change BACKEND_ENDPOINT_TYPE to "session" and set the endpoint to the URL of your console server.

On Linux/macOS, create a shell script as 'my-backend-ai-session.sh' and run it before using the backend.ai command:

.. code-block:: console

   export BACKEND_ENDPOINT=https://my-precious-cluster
   export BACKEND_ENDPOINT_TYPE=session

When the endpoint type is ``"session"``, you must explicitly login and logout
into/from the console server.

.. code-block:: console

   $ backend.ai login
   Username: myaccount@example.com
   Password:
   ✔ Login succeeded.

   $ backend.ai ...  # any commands

   $ backend.ai logout
   ✔ Logout done.

The session expiration timeout is set by the console server.

After setting up the environment variables, just run any command:

.. code-block:: console

   $ backend.ai ...

Checking out the current configuration
--------------------------------------

Run the following command to list your current active configurations.

.. code-block:: console

   $ backend.ai config

Command Reference
-----------------------------------
+-----------+----------------------------------------------------------------------+
| Command   | Description                                                          |
+===========+======================================================================+
| login     | Log-in to the console API proxy.                                     |
+-----------+----------------------------------------------------------------------+ 
| logout    | Log-out from the console API proxy and clears the local cookie data. |
+-----------+----------------------------------------------------------------------+
| config    | Shows the current configuration.                                     |
+-----------+----------------------------------------------------------------------+

