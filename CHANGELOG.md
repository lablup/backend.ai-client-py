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
