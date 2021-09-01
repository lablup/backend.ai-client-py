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
