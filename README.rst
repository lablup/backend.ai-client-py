Backend.AI Client
=================

.. image:: https://badge.fury.io/py/backend.ai-client.svg
   :target: https://badge.fury.io/py/backend.ai-client
   :alt: PyPI version

.. image:: https://img.shields.io/pypi/pyversions/backend.ai-client.svg
   :target: https://pypi.org/project/backend.ai-client/
   :alt: Python Versions

.. image:: https://travis-ci.org/lablup/backend.ai-client-py.svg?branch=master
   :target: https://travis-ci.org/lablup/backend.ai-client-py
   :alt: Build Status (Linux)

.. image:: https://ci.appveyor.com/api/projects/status/5h6r1cmbx2965yn1/branch/master?svg=true
   :target: https://ci.appveyor.com/project/lablup/backend.ai-client-py/branch/master
   :alt: Build Status (Windows)

.. image:: https://codecov.io/gh/lablup/backend.ai-client-py/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/lablup/backend.ai-client-py
   :alt: Code Coverage

The official API client library for `Backend.AI <https://backend.ai>`_

Usage
-----

You should set the access key and secret key as environment variables to use the API.
Grab your keypair from `cloud.backend.ai <https://cloud.backend.ai>`_ or your cluster
admin.

.. code-block:: sh

   export BACKEND_ACCESS_KEY=...
   export BACKEND_SECRET_KEY=...

   # optional (for local clusters)
   export BACKEND_ENDPOINT="https://my-precious-cluster/"


Command-line Interface
----------------------

``backend.ai`` command is the entry point of all sub commands.
(Alternatively you can use a verbosely long version: ``python -m
ai.backend.client.cli``)

Highlight: ``run`` command
~~~~~~~~~~~~~~~~~~~~~~~~~~

To run the code specified in the command line directly,
use ``-c`` option to pass the code string (like a shell).

.. code-block:: console

   $ backend.ai run python -c "print('hello world')"
   ∙ Client session token: d3694dda6e5a9f1e5c718e07bba291a9
   ✔ Kernel (ID: zuF1OzMIhFknyjUl7Apbvg) is ready.
   hello world

You can even run a C code on-the-fly. (Note that we put a dollar sign before
the single-quoted code argument so that the shell to interpret ``'\n'`` as
actual newlines.)

.. code-block:: console

   $ backend.ai run c -c $'#include <stdio.h>\nint main() {printf("hello world\\n");}'
   ∙ Client session token: abc06ee5e03fce60c51148c6d2dd6126
   ✔ Kernel (ID: d1YXvee-uAJTx4AKYyeksA) is ready.
   hello world

For larger programs, you may upload multiple files and then build & execute
them.  The below is a simple example to run `a sample C program
<https://gist.github.com/achimnol/df464c6a3fe05b21e9b06d5b80e986c5>`_.

.. code-block:: console

   $ git clone https://gist.github.com/achimnol/df464c6a3fe05b21e9b06d5b80e986c5 c-example
   Cloning into 'c-example'...
   Unpacking objects: 100% (5/5), done.
   $ cd c-example
   $ backend.ai run c main.c mylib.c mylib.h
   ∙ Client session token: 1c352a572bc751a81d1f812186093c47
   ✔ Kernel (ID: kJ6CgWR7Tz3_v2WsDHOwLQ) is ready.
   ✔ Uploading done.
   ✔ Build finished.
   myvalue is 42
   your name? LABLUP
   hello, LABLUP!

Please refer the ``--help`` manual provided by the ``run`` command.

You may use a shortcut command ``lcc`` and ``lpython`` instead of typing the full
Python module path like:

.. code-block:: console

   $ lcc main.c mylib.c mylib.h
   
Since the client version 1.1.5, the sessions are no longer automatically cleaned up.
To do that, add ``--rm`` option to the ``run`` command, like Docker CLI.

Highlight: ``ps`` and ``terminate`` command
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can see the list of currently running sessions using your API keypair.

.. code-block:: console

   $ backend.ai ps
   Session ID                        Lang/runtime    Created At                        Termianted At    Status      Memory Slot    CPU Slot    GPU Slot
   --------------------------------  --------------  --------------------------------  ---------------  --------  -------------  ----------  ----------
   5baafb2136029228ca9d873e1f2b4f6a  python:latest   2018-01-09T04:32:21.962223+00:00                   RUNNING            1024           1           0

If you set ``-t`` option in the ``run`` command, it will be used as the session ID—you may use it to assign a human-readable, easy-to-type alias for your sessions.
These session IDs can be reused after the current session using the same ID terminates.

To terminate a session,

.. code-block:: console

   $ backend.ai terminate 5baafb2136029228ca9d873e1f2b4f6a
   ✔ Done.

Highlight: ``proxy`` command
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To use API development tools such as GraphiQL for the admin API, run an insecure
local API proxy.  This will attach all the necessary authorization headers to your
vanilla HTTP API requests.

.. code-block:: console

   $ backend.ai proxy
   ∙ Starting an insecure API proxy at http://localhost:8084

More commands?
~~~~~~~~~~~~~~

Please run ``backend.ai --help`` to see more commands.


Synchronous API (v1.2+)
-----------------------

.. code-block:: python

   from ai.backend.client import Session

   with Session() as session:
       kern = session.Kernel.get_or_create('lua5', client_token='mysession')
       code = 'print("hello world")'
       mode = 'query'
       run_id = None
       while True:
           result = kern.execute(run_id, code, mode=mode)
           run_id = result['runId']  # keeps track of this particular run loop
           for rec in result.get('console', []):
               if rec[0] == 'stdout':
                   print(rec[1], end='', file=stdout)
               elif rec[0] == 'stderr':
                   print(rec[1], end='', file=stderr)
               else:
                   handle_media(rec)
           if result['status'] == 'finished':
               break
           elif result['status'] == 'waiting-input':
               mode = 'input'
               if result['options'].get('is_password', False):
                   code = getpass.getpass()
               else:
                   code = input()
           else:
               mode = 'continued'
               code = ''
       kern.destroy()

You need to take care of ``client_token`` because it determines whether to
reuse kernel sessions or not.
Backend.AI cloud has a timeout so that it terminates long-idle kernel sessions,
but within the timeout, any kernel creation requests with the same ``client_token``
let Backend.AI cloud to reuse the kernel.

Asynchronous API (v18.12+)
--------------------------

.. code-block:: python

   import asyncio
   import json
   import aiohttp
   from ai.backend.client import AsyncSession

   async def main():
       async with AsyncSession() as session:
           kern = await session.Kernel.get_or_create('lua5', client_token='mysession')
           code = 'print("hello world")'
           mode = 'query'
           stream = await kern.stream_execute(code, mode=mode)
           # no need for explicit run_id since WebSocket connection represents it!
           async for result in stream:
               if result.type != aiohttp.WSMsgType.TEXT:
                   continue
               result = json.loads(result.data)
               for rec in result.get('console', []):
                   if rec[0] == 'stdout':
                       print(rec[1], end='', file=stdout)
                   elif rec[0] == 'stderr':
                       print(rec[1], end='', file=stderr)
                   else:
                       handle_media(rec)
               if result['status'] == 'finished':
                   break
               elif result['status'] == 'waiting-input':
                   mode = 'input'
                   if result['options'].get('is_password', False):
                       code = getpass.getpass()
                   else:
                       code = input()
                   await stream.send_text(code)
               else:
                   mode = 'continued'
                   code = ''
           await kern.destroy()

   loop = asyncio.get_event_loop()
   try:
       loop.run_until_complete(main())
   finally:
       loop.close()

The async version has all sync-version interfaces as coroutines but comes with additional
features such as ``stream_execute()`` which streams the execution results via websockets and
``stream_pty()`` for interactive terminal streaming.


Troubleshooting (FAQ)
---------------------

* There are error reports related to ``simplejson`` with Anaconda on Windows.
  This package no longer depends on simplejson since v1.0.5, so you may uninstall it
  safely since Python 3.5+ offers almost identical ``json`` module in the standard
  library.

  If you really need to keep the ``simplejson`` package, uninstall the existing
  simplejson package manually and try reinstallation of it by downloading `a
  pre-built binary wheel from here
  <https://www.lfd.uci.edu/%7Egohlke/pythonlibs/#simplejson>`_.
