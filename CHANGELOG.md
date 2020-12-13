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

20.09.0b1 (2020-12-02)
----------------------


### Features
* Add more detail fields (`live_stat` and `allowed_docker_registries`) to admin session/domain query CLI commands ([#147](https://github.com/lablup/backend.ai-client-py/issues/147))


20.09.0a3 (2020-11-16)
----------------------

### Fixes
* Write upstream websocket errors more reliably to the client (browser) in the downstream ([#144](https://github.com/lablup/backend.ai-client-py/issues/144))
* Fix an inadvertent internal cancellation error when a client closes an app-proxy connection in the `app` command ([#146](https://github.com/lablup/backend.ai-client-py/issues/146))


20.09.0a2 (2020-10-30)
----------------------

### Features
* Add `backend.ai ssh` and `backend.ai scp` command which provides transparent wrappers of `ssh` and `scp` against the given compute session ([#138](https://github.com/lablup/backend.ai-client-py/issues/138))

### Fixes
* Improve error message output when the server responds with invalid API parameter errors, when it only sends generic text-only error messages. ([#136](https://github.com/lablup/backend.ai-client-py/issues/136))
* Fix naming and defaults of new vfolder creation parameters `cloneable` and `quota` (added in APIv6) for both the functional SDK and the CLI arguments ([#137](https://github.com/lablup/backend.ai-client-py/issues/137))
* Fix a wrong argument name in `vfolder update-options` cli command ([#139](https://github.com/lablup/backend.ai-client-py/issues/139))
* Fix regression of the `admin vfolders` command since introduction of paginated GraphQL queries ([#140](https://github.com/lablup/backend.ai-client-py/issues/140))
* Update aiohttp to 3.7.2 to fix [an upstream issue](https://github.com/aio-libs/aiohttp/issues/5149) related to fallback of `sendfile()` with uvloop ([#143](https://github.com/lablup/backend.ai-client-py/issues/143))

### Miscellaneous
* Update dependencies (including aiohttp 3.7.1) and CI workflows to use `towncrier.check` instead of the psf-chronogrphaer app ([#142](https://github.com/lablup/backend.ai-client-py/issues/142))


20.09.0a1 (2020-10-06)
----------------------

### Breaking Changes
* Low-level API: Removed no longer needed `session` argument when instantiating `client.request.Request` ([#128](https://github.com/lablup/backend.ai-client-py/issues/128))

### Features
* Add purge command for users, groups, and domains. ([#117](https://github.com/lablup/backend.ai-client-py/issues/117))
* Add support for storage proxy ([#118](https://github.com/lablup/backend.ai-client-py/issues/118))
  - The vfolder upload and download functions/commands now uses the storage proxy designated by the gateway APIs with the issued JWT token to transfer actual payloads.
  - The vfolder upload function uses `aiotusclient` for large-sized, resumable uploads.
* Display users' full name when querying keypair(s). ([#122](https://github.com/lablup/backend.ai-client-py/issues/122))
* Support for APIv6 clustering ([#125](https://github.com/lablup/backend.ai-client-py/issues/125))
  - Add `--cluster-size` and `--cluster-mode` CLI arguments and function API arguments when creating new sessions, which are added in APIv6
  - Include the session ID by default in `backend.ai ps` and `backend.ai admin session` commands
* Add new functional APIs and commands corresponding to the new vfolder clone and update-options APIs ([#127](https://github.com/lablup/backend.ai-client-py/issues/127), [#133](https://github.com/lablup/backend.ai-client-py/issues/133))
* Add quota as an option for vfolder creation. ([#130](https://github.com/lablup/backend.ai-client-py/issues/130))
* Add support for adding/updating/deleting/listing domain dotfiles and group dotfiles ([#132](https://github.com/lablup/backend.ai-client-py/issues/132))

### Fixes
* Extends the keypair's `paginated_list` query to accept `user_id` parameter. ([#119](https://github.com/lablup/backend.ai-client-py/issues/119))
* Fix various API v4/v5 compatibility issues when using CLI commands and make output of "admin session" more readable ([#121](https://github.com/lablup/backend.ai-client-py/issues/121))
* Use session IDs when invoking stream APIs to prevent conflicts in partial matches of prefix-overlapping session names ([#126](https://github.com/lablup/backend.ai-client-py/issues/126))
* Fix tus upload and download test functions ([#131](https://github.com/lablup/backend.ai-client-py/issues/131))
* Include more details in the `vfolder list` command, including the hosting volume name and the creation date ([#135](https://github.com/lablup/backend.ai-client-py/issues/135))

### Miscellaneous
* Improve CI execution performance by migrating to GitHub Actions ([#134](https://github.com/lablup/backend.ai-client-py/issues/134))


20.03.0 (2020-07-28)
--------------------

### Breaking Changes
* Replace `--is-active` (`is_active`) option to `--status` (`status`) to allow using an enumeration of multiple user statuses in the CLI and the functional API. ([#111](https://github.com/lablup/backend.ai-client-py/issues/111))

### Features
* Add support for user-defined bootstrap script when running/starting new sessions via CLI ([#114](https://github.com/lablup/backend.ai-client-py/issues/114))
* Add `admin show-license` command for the enterprise edition users ([#115](https://github.com/lablup/backend.ai-client-py/issues/115))

### Fixes
* Change the GraphQL argument type of `user_id` from String to ID in the user detail query and explicitly allow passing UUID objects ([#113](https://github.com/lablup/backend.ai-client-py/issues/113))
* Show the unique session ID (generated by the server) correctly after creating new compute sessions ([#116](https://github.com/lablup/backend.ai-client-py/issues/116))


20.03.0b2 (2020-07-02)
----------------------

### Features
* Add `-b`, `--base-dir` option to the `vfolder upload` command and allow use of colon as mount path-mapping separator like docker CLI ([#106](https://github.com/lablup/backend.ai-client-py/issues/106))
* Add support for announcements, including automatic display of the message when executing a CLI command if available and a new commandset "announcement" to manage the announcement message for superadmins and to dismiss the last shown message for normal users ([#107](https://github.com/lablup/backend.ai-client-py/issues/107))
* Add starts_at option for creating session. ([#109](https://github.com/lablup/backend.ai-client-py/issues/109))
* Add the functional SDK and CLI support for the scheduler operation APIs, which allows extra operations such as excluding/including agents from/in scheduling ([#110](https://github.com/lablup/backend.ai-client-py/issues/110))

### Fixes
* Fix missing handling of `BackendClientError` when fetching announcements during opening sessions ([#108](https://github.com/lablup/backend.ai-client-py/issues/108))


20.03.0b1 (2020-05-12)
----------------------

### Breaking Changes
* The phase 1 for API v5 schema updates ([#97](https://github.com/lablup/backend.ai-client-py/issues/97))
  - Drop support for Python 3.6
  - Apply kernel/session naming changes
* The phase 2 for API v5 schema updates ([#103](https://github.com/lablup/backend.ai-client-py/issues/103))
  - `Agent.list_with_limit()` is replaced with `Agent.paginated_list()`.
  - Legacy `<ObjectType>.list()` methods are now returns only up to 100 entries.
    Users must use `<ObjectType>.paginated_list()` for fetching all items with pagination.

### Features
* Add usage_mode and permission option in creating vfolder ([#96](https://github.com/lablup/backend.ai-client-py/issues/96))
* The phase 1 for API v5 schema updates ([#97](https://github.com/lablup/backend.ai-client-py/issues/97))
  - `admin rescan-images` now have a working progress bar!
* File rename command for a file/directory inside a virtual folder. ([#99](https://github.com/lablup/backend.ai-client-py/issues/99))
* Improve console-server support with proxy-mode API sessions ([#100](https://github.com/lablup/backend.ai-client-py/issues/100))
* Add `backend.ai server-logs` command-set to list server-stored error logs ([#101](https://github.com/lablup/backend.ai-client-py/issues/101))
* Improve and refactor pagination to avoid excessive server queries and apply to more CLI commands ([#102](https://github.com/lablup/backend.ai-client-py/issues/102))
* The phase 2 for API v5 schema updates ([#103](https://github.com/lablup/backend.ai-client-py/issues/103))
  - Session queries now work with the API v5 GraphQL schema and recognizes multi-container sessions
  - Improve pagination for `admin agents`, `admin sessions`, `admin users`, and `admin keypairs` commands
  - Add support for async generator API function methods, wrapped as synchronouse plain generators in synchronouse API sessions
  - Add new filtering options to `admin agents` (scaling groups) and `admin users` (user groups)

### Fixes
* Remove a bogus "bad file descriptor" error when commands exiting via exceptions ([#103](https://github.com/lablup/backend.ai-client-py/issues/103))

### Miscellaneous
* The phase 1 for API v5 schema updates ([#97](https://github.com/lablup/backend.ai-client-py/issues/97))
  - API function classes are now type-checked and interoperable with Python IDEs such as PyCharm, since references to the current active session is rewritten to use `contextvars`.


20.03.0a1 (2020-04-07)
----------------------

### Breaking Changes
* Breaking Changes without explicit PR/issue numbers
  Now the client SDK runs on Python 3.6, 3.7, and 3.8 and dropped support for Python 3.5.
* All functional API classes are moved into the `ai.backend.client.func` sub-package.
  [(#82)](https://github.com/lablup/backend.ai-client-py/issues/82)
  - `Kernel` is changed to `Session`.
  - The session ID field name in the response of `Session` objects
    is now `session_id` instead of `kernel_id`.
  - Except above, this would not introduce big changes in the SDK user
    codes since they use `AsyncSession` and `Session` in the
    `ai.backend.client.session` module.

### Features
* Features without explicit PR/issue numbers
  - Add SDK API (`SessionTemplate`) and CLI command set (`backend.ai sesstpl`)
* Support for unmanaged vfolders and token-based download API
  [(#77)](https://github.com/lablup/backend.ai-client-py/issues/77)
* `backend.ai config` command now displays the server/client component and API versions with negotiated API version if available.
  [(#79)](https://github.com/lablup/backend.ai-client-py/issues/79)
* Add `--format` and `--plain` options to `backend.ai ps` command to customize the output table format
  [(#80)](https://github.com/lablup/backend.ai-client-py/issues/80)
* Perform automatic API version negotiation when entering session contexts while keeping the functional API same
  [(#82)](https://github.com/lablup/backend.ai-client-py/issues/82)
* Support dotfiles management API and CLI
  [(#85)](https://github.com/lablup/backend.ai-client-py/issues/85)

### Fixes
* Refine details of the `app` command such as error handling
  [(#90)](https://github.com/lablup/backend.ai-client-py/issues/90)
* Improve exception handling in ``backend.ai app`` command and update backend.ai-cli package
  [(#94)](https://github.com/lablup/backend.ai-client-py/issues/94)

### Miscellaneous
* Adopt [towncrier](https://github.com/twisted/towncrier) for changelog management
  [(#95)](https://github.com/lablup/backend.ai-client-py/issues/95)
