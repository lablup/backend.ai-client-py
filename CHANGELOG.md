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

## 21.09.2 (2022-01-10)

### Features
* Add support for session renaming ([#189](https://github.com/lablup/backend.ai-client-py/issues/189))

### Fixes
* Warn explicitly when there are missing args in the `session download` command ([#191](https://github.com/lablup/backend.ai-client-py/issues/191))
* Fix a regression of "ssh" command due to command hierarchy reorganization ([#192](https://github.com/lablup/backend.ai-client-py/issues/192))
* Remove bogus known-host checks when using `ssh` and `scp` commands ([#193](https://github.com/lablup/backend.ai-client-py/issues/193))

### Miscellaneous
* Update mypy to 0.930 ([#190](https://github.com/lablup/backend.ai-client-py/issues/190))


## 21.09.1 (2021-12-15)

### Features
* Improve formatting of announcements using box-drawing characters and a Markdown formatter ([#186](https://github.com/lablup/backend.ai-client-py/issues/186))

### Fixes
* Fix missing auto-creation of local-state directory when storing server announcements ([#185](https://github.com/lablup/backend.ai-client-py/issues/185))


## 21.09.0.post1 (2021-11-08)

* A hotfix release to apply missing updates of package dependencies


## 21.09.0 (2021-11-08)

### Features
* Add `--agent-list` option to `run` and `create` commands so that superadmins can manually assign the agent(s) for new sessions to debug and diagnose the cluster and scheduler. ([#178](https://github.com/lablup/backend.ai-client-py/issues/178))

### Fixes
* Fix a regression of progress display in the `admin image rescan` command ([#182](https://github.com/lablup/backend.ai-client-py/issues/182))
* Fix handling of null values in some output formatters, which caused regression of `backend.ai info` command ([#183](https://github.com/lablup/backend.ai-client-py/issues/183))


## 21.09.0a2 (2021-09-28)

### Breaking Changes
* Multiple breaking changes related to pagination and CLI outputs:
  - The CLI command hierarchy and arguments are revamped to be much more consistent with enumeration and item queries, and to support global options such as `--output=json` and `-y`/`--yes` flags. This is not backward-compatible due to parsing ambiguity.
  - When invoking the functional APIs to retrieve the details and lists, you need to change your `fields` arguments to be a list of `FieldSpec` objects instead of strings.  You may refer `ai.backend.client.output.fields` for predefined field definitions and individual functional API modules for their default list/detail field sets.
    You may also define and pass your own `FieldSpec` and `OutputFormatter` objects as well.
  - It requires the Backend.AI Manager API v5.20191215 (release 20.03) or later.  If used with older managers, it will show a warning.
  - It requires Python 3.8 or higher to run. ([#163](https://github.com/lablup/backend.ai-client-py/issues/163))

### Features
* Utilize Rich as a formatting library for server announcements ([#174](https://github.com/lablup/backend.ai-client-py/issues/174))

### Fixes
* Fix handling of default values for JSON string CLI arugments (`client.cli.params.JSONParamType`) ([#180](https://github.com/lablup/backend.ai-client-py/issues/180))


## 21.09.0a1 (2021-08-25)

### Features
* Add commands to share/unshare a group virtual folder directly to specific users. This is to allow specified users (usually teachers with user account) can upload data/materials to a virtual folder while it is shared as read-only for other group users. ([#159](https://github.com/lablup/backend.ai-client-py/issues/159))
* Add support for the `SCHEDULED` status in `ps` (including `admin sessions`), `run`, and `start` commands ([#161](https://github.com/lablup/backend.ai-client-py/issues/161))
* Add `admin groups-by-name` to resolve group information by the name ([#170](https://github.com/lablup/backend.ai-client-py/issues/170))
* Add support for queryfilter (`--filter`) and ordering (`--order`) arguments for paginated lists (e.g., `ps`, `admin agents`, `admin users` commands) ([#171](https://github.com/lablup/backend.ai-client-py/issues/171))

### Fixes
* Remove the legacy `-p/--protocol` option from the `app` command sicne it now works as the TCP protocol always ([#156](https://github.com/lablup/backend.ai-client-py/issues/156))
* Gracefully skip null-metric when printing statistics ([#157](https://github.com/lablup/backend.ai-client-py/issues/157))
* Update dependencies to embrace security patches in PyYAML ([#158](https://github.com/lablup/backend.ai-client-py/issues/158))
* Rename ScalingGroupInput to CreateScalingGroupInput, which was changed in Manager by recent commit. ([#160](https://github.com/lablup/backend.ai-client-py/issues/160))
* Fix desynchronized parameters of the `info` command alias of the `admin session` command ([#162](https://github.com/lablup/backend.ai-client-py/issues/162))
* Update backend.ai-cli version to make it working with Click 8.0 ([#164](https://github.com/lablup/backend.ai-client-py/issues/164))
* Fix a missing `py.typed` marker in the wheel package ([#166](https://github.com/lablup/backend.ai-client-py/issues/166))
* Fix a wrong field name (`last_updated`) for `status_changed` when `ComputeSession.paginated_list()` is executed without the explicit field list. ([#167](https://github.com/lablup/backend.ai-client-py/issues/167))
* Support the new standard-compliant GQL endpoint in the manager with the API version v6.20210815 ([#168](https://github.com/lablup/backend.ai-client-py/issues/168))
* Fix regression of `vfolder upload` and other commands using `ByteSizeParamType` with the default values given as `int` ([#169](https://github.com/lablup/backend.ai-client-py/issues/169))
* Fix wrong type and default value of `status` argument for `User.create()` and `User.update()` functional APIs and let `role` and `status` arguments accept explicit enum types in addition to raw strings ([#172](https://github.com/lablup/backend.ai-client-py/issues/172))
* Fix a missing comman that breaks `User.detail()` functional API when called without an explicit field list ([#173](https://github.com/lablup/backend.ai-client-py/issues/173))
* Fix CORS errors when running `backend.ai proxy` in a non-localhost IP address due to missing HTTP headers in the upstream API requests ([#176](https://github.com/lablup/backend.ai-client-py/issues/176))

### Miscellaneous
* Update the package requirements for documentation builds ([#154](https://github.com/lablup/backend.ai-client-py/issues/154))
* Update dependencies and change the version ranges to specify the minimum to allow more flexibility in the components relying on this SDK ([#175](https://github.com/lablup/backend.ai-client-py/issues/175))


## Older changelogs

* [21.03](https://github.com/lablup/backend.ai-client-py/blob/21.03/CHANGELOG.md)
* [20.09](https://github.com/lablup/backend.ai-client-py/blob/20.09/CHANGELOG.md)
* [20.03](https://github.com/lablup/backend.ai-client-py/blob/20.03/CHANGELOG.md)
