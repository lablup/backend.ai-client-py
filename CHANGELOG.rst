Changes
=======

19.09.6 (2020-03-xx)
--------------------

* NEW: Add ``-f`` / ``--forced`` option to ``backend.ai terminate`` command
  and add an optional ``forced`` keyword-argument to SDK API (``Kernel.destroy()``). (#89)

* IMPROVE: Prettify the console output for admin CLI commands. (#91)

19.09.5 (2020-03-08)
--------------------

* NEW: Add ``backend.ai restart`` command and improve error handling in
  the ``backend.ai terminate`` command.

19.09.4 (2020-02-10)
--------------------

* NEW: SDK API (``EtcdConfig``) and CLI command (``backend.ai admin etcd``)
  to allow querying and updating etcd configurations by admins.

19.09.3 (2019-12-03)
--------------------

* NEW: SDK API (``Auth.update_password()``) and CLI command (``backend.ai update-password``)
  to allow changing the password by the users themselves.

* NEW: SDK API (``VFolder.delete_by_id()``) so that superadmins can delete
  a vfolder owned by arbitrary user/group.

19.09.2 (2019-11-04)
--------------------

* NEW: API for disassociating scaling groups from a user group

* FIX: Regression in "admin keypairs" command due to code/server changes

19.09.1 (2019-10-15)
--------------------

* OPTIMIZE: vfolder downloads and application proxies are faster to transfer large files due to increased
  network buffer sizes.

* FIX: The kernel/vfolder download APIs now uses the default event loop executor for file write
  operations which reduces latency jitters in user async applications that embeds this SDK.

* FIX: Remove a wrong default for the ``--list-all`` option of the ``backend.ai vfolder list`` command.

* DOCS: Add manuals for SSH/SFTP usage.

19.09.0 (2019-10-07)
--------------------

* NEW: Add read-timeout configuration (``BACKEND_READ_TIMEOUT``) to limit the time taken for waiting
  server responses.  Its default is set to infinity for now because currently some core APIs require
  indefinite waiting to get responses.

19.09.0rc3 (2019-10-04)
-----------------------

* NEW: Batch tasks options at "backend.ai start" command, includingthe type and startup command
  arguments.

* NEW: Download and print batch task logs via "backend.ai task-logs" command

* IMPROVE: New "--show-tid" option in "backend.ai ps" command

* NEW: Add support for native TCP service ports by refactoring "backend.ai app" command arguments.

* IMPROVE: Support owner-access-key parameter to launch sessions on behalf of other users

* NEW: API wrapper for image import function (#74)

* FIX: underscore/camel-case inconsistency in image-related admin commands and function interfaces

* IMPROVE: Move the composition of vfolder invitation command messages to the client from the server.

* Other fixes and improvements.

19.09.0rc2 (2019-09-24)
-----------------------

* IMPROVE: Refine the result and options of "backend.ai ps" command, so that it shows PENDING,
  PREPARING, PULLING, TERMINATING, CANCELLED sessions appropriately.

19.09.0rc1 (2019-09-23)
-----------------------

* NEW: Support for high availability setup of managers (#70) via client-side
  load balancing and automatic fail-over against multiple endpoints.

* NEW: Support for job queueing options such as parameters to ``backend.ai run`` and ``backend.ai
  start`` commands to set scheduling waiting time (#70).

* NEW: ``backend.ai events`` command to monitor session lifecycle events.

* CHANGE: Now Python 3.6 or higher is required.

* Updated documentation and made it easier to read in order.
  Furhter docs update will follow in the next few releases.

19.09.0b9 (2019-09-17)
----------------------

* NEW: Add admin commands to list all vfolder hosts, docker registries, and scaling groups.

* IMPROVE: In the session mode, show the username in ``backend.ai config`` command. (#68)

* IMPROVE: ``backend.ai admin users update`` command now has ``-d`` / ``--domain-name`` option to
  change a user's domain.

* FIX: CLI's optional argument names use dashes consistently.  Some recently added commands had
  underscore argument names by mistake.

19.09.0b8 (2019-09-09)
----------------------

* NEW: Add ``--resource-opts shmem=BINARY_SIZE`` to specify shared memory size when launching kernels.
  You can use humanized sizes such as "1g" or "128m". (#67)

* NEW: Add ``backend.ai admin resource usage-*`` commands to query usage data related for billing.

* NEW: Add ``backend.ai admin vfolders list-mounts`` command.

* IMPROVE: Show user's full name in ``backend.ai admin user`` and ``backend.ai admin users`` commands.

* IMPROVE: Group vfolder can now be created with group name as well as UUID.

* IMPROVE: Allow admins to set options when mounting vfolder hosts.

19.09.0b7 (2019-08-30)
----------------------

* NEW: Add vfolder host/mount admin commands under ``backend.ai admin vfolders``

* FIX: Clean up output of ``backend.ai ls``

19.09.0b6 (2019-08-27)
----------------------

* NEW: Add ``--allowed-docker-registries`` option to ``backend.ai admin domain add`` command

19.09.0b5 (2019-08-21)
----------------------

* FIX: Regression of ``backend.ai admin session`` command

19.09.0b4 (2019-08-21)
----------------------

* NEW: Support for console server proxies with username/password-based session logins. (#63)
  Set ``BACKEND_ENDPOINT_TYPE=session`` to enable this mode.
  (``backend.ai login`` \& ``backend.ai logout`` commands are now available for this)

* NEW: Commands for agent watcher controls (#62)

* FIX: Regression of the range expression support in ``backend.ai run`` command

* Now user-specific state (e.g., cookies for session-based login) and cache (e.g., output logs for
  paralell execution when using range expressions) are stored platform-specific directories,
  such as ``~/.cache/backend.ai`` (Linux), ``~/Application Support/backend.ai`` (MacOS), or
  ``%HOME%\AppData\Local\Lablup\backend.ai`` (Windows). (#65)


19.09.0b3 (2019-08-05)
----------------------

* Add support for scaling groups to both the API functions and the CLI.


19.06.0b2 (2019-07-24)
----------------------

* Fix handling the content-type HTTP header when proxying.
  This allows sending multipart form uploads (e.g., vfolder uploads) via the proxy.

* Remove client-side vfolder naming checks.

19.06.0b1 (2019-07-14)
----------------------

* Add support for per-group vfolders and usage statistics.

* Update support for domain and groups.

19.06.0a1 (2019-06-03)
----------------------

* Add support for specifying domain and groups. (lablup/backend.ai-manager#148)

* Add support for the new "/auth/authorize" API.

* Include Python 3.7 as an officially supported Python version.

19.03.1 (2019-05-10)
--------------------

* Fix support for Python 3.5 due to f-string literals in the vfolder module.

* Fix the broken unit test suite for both Python 3.5 and 3.6.

* Update the docs and examples.

19.03.0 (2019-04-10)
--------------------

* Include "concurrency_used" when fetching keypairs in "admin keypair" commands.

* Add support for the vfolder host listing API.

* Improve test cases and coverage.

19.03.0rc2 (2019-03-26)
-----------------------

* NEW: Add SDK/CLI support for resource policy management.

* NEW: Add SDK/CLI support for vfolder renaming.

* NEW: Add SDK/CLI support for owner_access_key in the kernel APIs and "-o" /
  "--owner-access-key" argument to the kernel-releated CLI commands.

19.03.0rc1 (2019-02-25)
-----------------------

* Support pagination of "admin sessions" and "admin agents" commands.

* Send websocket pings to keep connections and sessions alive while app services
  are being used.

19.03.0b4 (2019-02-15)
----------------------

* Fix an error when pretty-printing agent exceptions.

19.03.0b3 (2019-02-08)
----------------------

* NEW: ``--skip-sslcert-validation`` CLI option.

* Minor CLI updates: Add ``cpu_using`` field to "admin agents" statistics
  and ``size_bytes`` field to the "admin image" result.

19.03.0b2 (2019-01-30)
----------------------

* Minor fix for the CLI to show extra error details only when they are present.

19.03.0b1 (2019-01-30)
----------------------

* Support API v4.20190315 and change GraphQL fields for various admin commands
  to match with the v19.03 series server.

  This renders the client after this version won't be compatible with old servers.

* Fix various bugs.

18.12.3 (2019-02-10)
--------------------

* Add "--skip-sslcert-validation" option and environment variable equivalent.
  (backported from master)

* Fix pretty-printing of server errors with no/null title field in the details.
  (backported from master)

18.12.2 (2019-01-30)
--------------------

* Minor fix for the CLI to show extra error details only when they are present.
  (backported from master)

18.12.1 (2019-01-21)
--------------------

* Automatically detect the legacy mode (API version &lt;= v4.20181215).
  Removed "--legacy" option for the "run" command.

18.12.0 (2019-01-06)
--------------------

* Fix various bugs.

18.12.0a2 (2018-12-21)
----------------------

* NEW: "admin images" command to show the kernel images registered to the server.

* Improve error displays.

* Explicitly set connection timeout only for potentially long-running requests such
  as file uploads/downloads and kernel creation.


18.12.0a1 (2018-12-14)
----------------------

* NEW: "app" command for app service ports! You can now connect to Jupyter Notebook
  and other services running in the compute sessions directly!

* NEW: "start" command which starts a compute sessino but does not anything.

* Adopt Click (CLI toolkit) for better Windows support and future shell
  autocompletion support.

* "ps" and "admin sessions" commands show more detailed resource statistics,
  includign real-time memory usage.

* Revamp the SDK documentation: https://docs.client-py.backend.ai

1.5.1 (2018-12-03)
------------------

* Display CLI errors with more details, including server-generated extra messages
  and fully formatted exception arguments line-by-line.

* Fix a regression bug in the kernel file download API.

1.5.0 (2018-11-26)
------------------

* Support API v4's authentication mechanism which skips the request body when
  calculating auth signatures.  (This will be the preferred way in favor of
  streaming-based APIs.)

* Rewrite the low-level request APIs and API function implementations.
  Now all APIs are written in async codes first and then wrapped as synchronous APIs
  if non-async Session is used.

* Due to a large amount of internal changes, we bump the version to v1.5.0
  before going to v18.12.0 series.

1.4.2 (2018-11-06)
------------------

* Improve handling of unspecified resource shares.

* Internal updates for test cases and test dependencies.

1.4.1 (2018-10-30)
------------------

* Hotfix for regression in ``Kernel.stream_pty()`` method.

1.4.0 (2018-09-23)
------------------

* Support download and deletion of virtual folder files.
  Check ``backend.ai vfolder --help`` for new commands!

* Allow customization of keypairs when creating new one via extra arguments.
  See ``backend.ai admin keypairs add --help`` for available options.

* Accept both integer and string values in ``-u`` / ``--user`` arguments for
  Backend.AI v1.4+ forward compatibility.

1.3.7 (2018-06-19)
------------------

* Fix use of synchronous APIs inside asyncio-based applications using a separate
  worker thread that needs to be shut down manually.
  (e.g., our Jupyter notebook kernel plugin)

* Synchronous API users now MUST call "ai.backend.client.request.shutdown()"
  function when their application exits.

* Update dependencies (aiohttp and aioresponses)

1.3.6 (2018-06-02)
------------------

* Fix installation warnings about aiohttp/async_timeout/attrs version mismatch
  with the new pip 10 series.

  NOTE: A workaround is to add ``--upgrade-strategy=eager`` option to ``pip install``
  command.

1.3.4 (2018-04-08)
------------------

* Add progress bars when uploading files to kernel/vfolder in CLI. (#23)

* Drop dependency to requests and use aiohttp all the time, in favor of
  better streaming request/response handling for large files.
  Synchronous APIs will implicitly spawn event loops if not already there,
  via ``asyncio.get_event_loop()``.  You may also pass a loop object explicitly.

* Remove default timeout (10 secs) in asynchronous requests, to allow
  large file uploads that takes longer than that.

1.3.3 (2018-04-05)
------------------

* Hotfix for passing environment variables when creating new kernels.

1.3.2 (2018-03-28)
------------------

* Fix missing date object/header when making websocket requests.

* run command: Show the name and URL of files generated by the kernel.

* Upgrade aiohttp to v3.1 series, which introduces bugfixes and improvements in
  websocket handling.

1.3.0 (2018-03-20)
------------------

* Add support for BACKEND_VFOLDER_MOUNTS environment variable. (#21)
  This allows use of auto-mounted vfolders when using 3rd-party integrations such as
  Jupyter notebook.  The format is a list of comma-separated strings for the vfolder
  names.

* Individual API Function objects such as Kernel can now have individual
  APIConfig objects via optional "config" parameters to static/class methods
  and the per-instance config attribute. (#20)

* Improve vfolder CLI command outputs.

* Improve scripting support: all CLI commands that fail now return exit code 1
  explicitly.

1.2.1 (2018-03-08)
------------------

* BackendError is now normal Exception, not BaseException.
  This was a mistake in the early stage of development.

1.2.0 (2018-03-08)
------------------

* Fixed vfolder upload API to work with aiohttp v3.

* "vfolder upload" command can now upload multiple files.

1.1.11 (2018-03-07)
-------------------

* Change StreamPty methods to become coroutines to match with aiohttp v3
  API changes.

1.1.10 (2018-03-04)
-------------------

* Fix file upload handling in the asyncio version.

* Stringifying exception classes now use the output of "repr()".

1.1.9 (2018-03-02)
------------------

* Improve asyncio exception handling.
  Now it does NOT silently swallow CancelledError/TimeoutError and other
  non-aiohttp errors!

1.1.8 (2018-03-01)
------------------

* Upgrade to use aiohttp v3 series.

* Improve handling of base directories outside the current working directory
  when uploading files for the batch mode execution.

* Display exit code if available in the batch mode execution.

1.1.7 (2018-01-09)
------------------

* Hotfix: Add missing "ai.backend.client.cli.admin" module in the package.

1.1.6 (2018-01-06)
------------------

* Apply authentication to websocket requests as well.

* Fix the client-side validation of client token length.

1.1.5 (2018-01-05)
------------------

* Relicensed to MIT License to motivate integration with commercial/proprietary
  software products.

* Lots of CLI improvements!

  - Add "terminate" command.

  - Add more "run" command options.  Now it does NOT terminate the session after
    execution by default, and you can force it using "--rm" option.

  - Add "admin keypairs" command and its subcommands for managing keypairs.

  - Add "admin agents" command to list agent instances.

  - "ps" and "admin session" commands now correctly show the client-given session ID
    token instead of the master kernel ID of the session.

  - Add "logs" command.

* Fix a continuation bug of the "run" command when using the batch-mode, which
  has caused a mismatch of run ID management of the agent and the internal task
  queue of the kernel runner, resulting an indefinite hang up with two legitimate
  subsequent requesting of batch-mode executions.

  As being a reference implementation of the execution loop, all API users are
  advised to review and fix their client-side codes.

* Now the client sets a custom User-Agent header value as follows:
  "Backend.AI Client for Python X.X.X" where X.X.X is the version.

1.1.1 (2017-12-04)
------------------

* Add mount ("-m"), environment variable ("-e") arguments to CLI "run" command
  which can be specified multiple times.
  This deprecates "-b" and "-e" abbreviations for "--build" and "--exec".

* Fix garbled tabular outputs of CLI commands in Python versions less than 3.6
  due to non-preserved dictionary ordering.

1.1.0 (2017-11-17)
------------------

**NEW**

* Now the CLI supports "vfolder" subcommands.

1.0.6 (2017-11-16)
------------------

**CHANGES**

* Now it uses "api.backend.ai" as the default endpoint.

* It also searches ``BACKEND_``-prefixed environment variables first and then
  falls back to ``SORNA_``-prefixed environment variables as legacy.

1.0.5 (2017-11-02)
------------------

**CHANGE**

* Remove ``simplejson`` from our dependencies.

1.0.4 (2017-10-31)
------------------

**NEW**

* Add "-s" / "--stats" option to the CLI "run" command.
  When specified, the CLI shows resource usage statistics after session termination.

1.0.3 (2017-10-18)
------------------

**NEW**

* Now you can run the CLI commands using "backend.ai"
  instead of "python -m ai.backend.client.cli"

* Add a few new CLI commands: config, help, ps

* Running "backend.ai" without any args shows the help message
  instead of an error.

**FIX**

* Fix colored terminal output in *NIX (#12)

1.0.2 (2017-10-07)
------------------

**FIX**

* Make the colored terminal output working on Windows (#12)

1.0.1 (2017-10-06)
------------------

**FIXES**

* Include missing dependencies: multidict

* Improve Windows platform supports (#12)

**CHANGES**

* Install asyncio-based dependencies by default (aiohttp and async_timeout)

1.0.0 (2017-09-20)
------------------

**CHANGES**

* Rename the product name "Sorna" to "Backend.AI".
  - Package import path: "sorna" → "ai.backend.client"
  - Class names: "SornaError" / "SornaAPIError" → "BackendError" / "BackendAPIError"
  - Any mention of "Sorna" in the API headers → "BackendAI".
    e.g., "X-Sorna-Version" API request header → "X-BackendAI-Version"

* Refactor the internal structure for sync/async API functions.

* Add support for the Admin API based on GraphQL both in the CLI and the functions.
  Now you can list up details of your compute sessions with ease.

0.9.7 (2017-08-25)
------------------

**FIX**

* Missing sorna.cli module in distribution.


0.9.6 (2017-08-25)
------------------

**NEW**

* Add console scripts "lcc" and "lpython" which are aliases
  of "python -m sorna.cli run c" and "python -m sorna.cli run python".

* Add explicit "--build" and "--exec" option for batch-mode
  customization.

0.9.5 (2017-06-30)
------------------

**FIX**

* Fix support for interactive inputs in the batch mode.

0.9.4 (2017-06-29)
------------------

**CHANGES**

* The ``run`` command now prints the build status in the batch mode.

0.9.3 (2017-06-29)
------------------

**NEW**

* The command-line interface.  Try ``python -m sorna.cli run`` command.

* It supports the batch-mode API with source file uploads.

* The client now now runs on Python 3.5 as well as Python 3.6.
  (Debian 9 / Ubuntu 16.04 users can install the client without
  searching for Google!)

0.9.2 (2017-04-20)
------------------

**NEW**

* It supports the draft auto-completion API.

**FIX**

* Now compatible with aiohttp 2.0+

0.9.1 (2017-03-14)
------------------

**FIX**

* Fix a bogus error when given empty codes for continuation.

0.9.0 (2017-03-14)
------------------

**NEW**

* New object-style API: Kernel objects.
  You can still use the legacy (but deprecated) function API.

* Add support for APIv2.20170315
  (vfolder API is coming soon!)

**CHANGES**

* Now requires Python 3.6 or higher.

* Improved exception handling.

  Now it uses a common base exception called "SornaError"
  and reports client-side errors as "SornaClientError"
  while server-side errors as "SornaAPIError".

0.8.3 (2017-01-13)
------------------

**FIX**

* Web terminal now works via SSL-enabled API servers.

0.8.2 (2017-01-11)
------------------

**FIXES**

* Add missing proxy method for exception() to StreamPty.

* Fix broken async_timeout checks due to pre-mature optimization,
  by reverting the optimization (thread-local HTTP sessions).

0.8.0 (2017-01-10)
------------------

**NEW**

* Add support for (now implemented) HTTP-based web terminal API.

0.7.0 (2016-12-14)
------------------

**NEW**

* First "usable" release.

0.1.1 (2016-11-23)
------------------

**FIXES**

* Add a missing package dependency (requests).

0.1.0 (2016-11-23)
------------------

**NEW**

* First public release.
