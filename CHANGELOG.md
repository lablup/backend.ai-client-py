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

<!-- towncrier release notes start -->

## 22.03.0 (2022-04-25)

### Fixes
* Fix broken wheel build workflow due to cached build packages by updating them ([#219](https://github.com/lablup/backend.ai-client-py/issues/219))


## 22.03.0b1 (2022-04-12)

### Features
* Allow specifying the architecture when setting image aliases ([#211](https://github.com/lablup/backend.ai-client-py/issues/211))
* Add `callback_url` parameter in session creation API/CLI to support session event webhook. ([#217](https://github.com/lablup/backend.ai-client-py/issues/217))

### Fixes
* Remove invalid "uuid" field from `groups` model. ([#216](https://github.com/lablup/backend.ai-client-py/issues/216))
* Remove access key option in vfolder list command since manager does not support the field. ([#218](https://github.com/lablup/backend.ai-client-py/issues/218))


## 22.03.0a2 (2022-03-29)

### Features
* Display the architecture field in agent and image lists ([#212](https://github.com/lablup/backend.ai-client-py/issues/212))
* Add `--depends` CLI option to the `start` &amp; `session create` commands and the corresponding functional API arguments ([#214](https://github.com/lablup/backend.ai-client-py/issues/214))

### Fixes
* Fix missing propagation of `starts_at` and `bootstrap_script` arguments to the session creation API, which have been supported since v20.03 ([#213](https://github.com/lablup/backend.ai-client-py/issues/213))
* Remove remaining traces of `keypair.concurrency_limit` which has been replaced with `keypair_resource_policy.max_concurrenct_sessions` ([#215](https://github.com/lablup/backend.ai-client-py/issues/215))


## 22.03.0a1 (2022-03-14)

### Features
* Add storage proxy address overriding option ([#194](https://github.com/lablup/backend.ai-client-py/issues/194))
* Print a jsonified result of mutation. ([#198](https://github.com/lablup/backend.ai-client-py/issues/198))
* Refactor and move `ask_yn()` and other CLI user input validation functions to the backend.ai-cli package ([#199](https://github.com/lablup/backend.ai-client-py/issues/199))
* Add a new functional API `vfolder.move_file()` and CLI command `vfolder mv` to move files and folders within a vfolder ([#208](https://github.com/lablup/backend.ai-client-py/issues/208))
* Improve CLI error formatting to use more sensible "message" and "data" fields ([#209](https://github.com/lablup/backend.ai-client-py/issues/209))

### Fixes
* Fix a `KeyError` for `agent_list` when the user don't use the `--assign-agent` option against the managers without support for the option ([#196](https://github.com/lablup/backend.ai-client-py/issues/196))
* Append a backup file extension to the `-i` option of `sed` command to prevent branch substitution errors when tested on macOS ([#202](https://github.com/lablup/backend.ai-client-py/issues/202))
* Update the docs and help texts of vfolder mount options to reflect allowance of arbitrary paths. ([#204](https://github.com/lablup/backend.ai-client-py/issues/204))
* Use the bgtask APIs to track progress of vfolder clone operation if available. ([#205](https://github.com/lablup/backend.ai-client-py/issues/205))
* Relax the minimum required version of `attrs` from 21.2 to 20.3 to better support co-installation with other Python packages ([#206](https://github.com/lablup/backend.ai-client-py/issues/206))

### Miscellaneous
* Update CI workflows to install the matching version of PR and release branches of `backend.ai-cli` ([#200](https://github.com/lablup/backend.ai-client-py/issues/200))
* Include Python 3.10 in the CI and make it officially supported ([#210](https://github.com/lablup/backend.ai-client-py/issues/210))


## 22.03.0.dev0 (2022-01-05)

### Features
* Improve formatting of announcements using box-drawing characters and a Markdown formatter ([#186](https://github.com/lablup/backend.ai-client-py/issues/186))
* Add support for session renaming ([#189](https://github.com/lablup/backend.ai-client-py/issues/189))

### Fixes
* Fix missing auto-creation of local-state directory when storing server announcements ([#185](https://github.com/lablup/backend.ai-client-py/issues/185))
* Warn explicitly when there are missing args in the `session download` command ([#191](https://github.com/lablup/backend.ai-client-py/issues/191))
* Fix a regression of "ssh" command due to command hierarchy reorganization ([#192](https://github.com/lablup/backend.ai-client-py/issues/192))
* Remove bogus known-host checks when using `ssh` and `scp` commands ([#193](https://github.com/lablup/backend.ai-client-py/issues/193))

### Miscellaneous
* Update mypy to 0.930 ([#190](https://github.com/lablup/backend.ai-client-py/issues/190))


## Older changelogs

* [21.09](https://github.com/lablup/backend.ai-client-py/blob/21.09/CHANGELOG.md)
* [21.03](https://github.com/lablup/backend.ai-client-py/blob/21.03/CHANGELOG.md)
* [20.09](https://github.com/lablup/backend.ai-client-py/blob/20.09/CHANGELOG.md)
* [20.03](https://github.com/lablup/backend.ai-client-py/blob/20.03/CHANGELOG.md)
