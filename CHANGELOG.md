Changes
=======

<!--
    You should *NOT* be adding new change log entries to this file, this
    file is managed by towncrier. You *may* edit previous change logs to
    fix problems like typo corrections or such.

    To add a new change log entry, please refer
    https://pip.pypa.io/en/latest/development/contributing/#news-entries

    We named the news folder "changes".

    WARNING: Don't drop the last line!
-->

.. towncrier release notes start

19.09.10 (2020-06-16)
---------------------

### Features
* Add `-b`, `--base-dir` option to the `vfolder upload` command ([#106](https://github.com/lablup/backend.ai-client-py/issues/106))
* Add support for announcements, including automatic display of the message when executing a CLI command if available and a new commandset "announcement" to manage the announcement message for superadmins and to dismiss the last shown message for normal users ([#107](https://github.com/lablup/backend.ai-client-py/issues/107))


19.09.9 (2020-05-15)
--------------------

### Fixes
* Fix GQL handling for non-existent running sessions in `backend.ai admin session <sessionAlias>` command ([#104](https://github.com/lablup/backend.ai-client-py/issues/104))


19.09.8 (2020-04-23)
--------------------

* NEW(backported): Add `backend.ai vfolder rename-file` command (#99)

19.09.7 (2020-03-31)
--------------------

* FIX: Not-implemented-error in `backend.ai app` command on Windows, due
  to manually set event loop UNIX signal handlers. (#93)
* FIX: Now *all* CLI commands set exit codes correctly for interrupts
  (Ctrl+C on Windows or SIGINT on POSIX systems) so that batch/shell
  scripts that use `backend.ai` commands get interrupted properly.
  (#93)

19.09.6 (2020-03-16)
--------------------

* NEW: Add `-f` / `--forced` option to `backend.ai terminate` command
  and add an optional `forced` keyword-argument to SDK API (`Kernel.destroy()`). (#89)
* IMPROVE: Prettify the console output for admin CLI commands. (#91)

19.09.5 (2020-03-08)
--------------------

* NEW: Add `backend.ai restart` command and improve error handling in
  the `backend.ai terminate` command.

19.09.4 (2020-02-10)
--------------------

* NEW: SDK API (`EtcdConfig`) and CLI command (`backend.ai admin etcd`)
  to allow querying and updating etcd configurations by admins.

19.09.3 (2019-12-03)
--------------------

* NEW: SDK API (`Auth.update_password()`) and CLI command (`backend.ai update-password`)
  to allow changing the password by the users themselves.
* NEW: SDK API (`VFolder.delete_by_id()`) so that superadmins can delete
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
* FIX: Remove a wrong default for the `--list-all` option of the `backend.ai vfolder list` command.
* DOCS: Add manuals for SSH/SFTP usage.

19.09.0 (2019-10-07)
--------------------

* NEW: Add read-timeout configuration (`BACKEND_READ_TIMEOUT`) to limit the time taken for waiting
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
* NEW: Support for job queueing options such as parameters to `backend.ai run` and `backend.ai
  start` commands to set scheduling waiting time (#70).
* NEW: `backend.ai events` command to monitor session lifecycle events.
* CHANGE: Now Python 3.6 or higher is required.
* Updated documentation and made it easier to read in order.
  Furhter docs update will follow in the next few releases.

19.09.0b9 (2019-09-17)
----------------------

* NEW: Add admin commands to list all vfolder hosts, docker registries, and scaling groups.
* IMPROVE: In the session mode, show the username in `backend.ai config` command. (#68)
* IMPROVE: `backend.ai admin users update` command now has `-d` / `--domain-name` option to
  change a user's domain.
* FIX: CLI's optional argument names use dashes consistently.  Some recently added commands had
  underscore argument names by mistake.

19.09.0b8 (2019-09-09)
----------------------

* NEW: Add `--resource-opts shmem=BINARY_SIZE` to specify shared memory size when launching kernels.
  You can use humanized sizes such as "1g" or "128m". (#67)
* NEW: Add `backend.ai admin resource usage-*` commands to query usage data related for billing.
* NEW: Add `backend.ai admin vfolders list-mounts` command.
* IMPROVE: Show user's full name in `backend.ai admin user` and `backend.ai admin users` commands.
* IMPROVE: Group vfolder can now be created with group name as well as UUID.
* IMPROVE: Allow admins to set options when mounting vfolder hosts.

19.09.0b7 (2019-08-30)
----------------------

* NEW: Add vfolder host/mount admin commands under `backend.ai admin vfolders`
* FIX: Clean up output of `backend.ai ls`

19.09.0b6 (2019-08-27)
----------------------

* NEW: Add `--allowed-docker-registries` option to `backend.ai admin domain add` command

19.09.0b5 (2019-08-21)
----------------------

* FIX: Regression of `backend.ai admin session` command

19.09.0b4 (2019-08-21)
----------------------

* NEW: Support for console server proxies with username/password-based session logins. (#63)
  Set `BACKEND_ENDPOINT_TYPE=session` to enable this mode.
  (`backend.ai login` \& `backend.ai logout` commands are now available for this)
* NEW: Commands for agent watcher controls (#62)
* FIX: Regression of the range expression support in `backend.ai run` command
* Now user-specific state (e.g., cookies for session-based login) and cache (e.g., output logs for
  paralell execution when using range expressions) are stored platform-specific directories,
  such as `~/.cache/backend.ai` (Linux), `~/Application Support/backend.ai` (MacOS), or
  `%HOME%\AppData\Local\Lablup\backend.ai` (Windows). (#65)


19.09.0b3 (2019-08-05)
----------------------

* Add support for scaling groups to both the API functions and the CLI.
