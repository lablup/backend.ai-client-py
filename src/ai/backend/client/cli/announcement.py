import hashlib
import json
from pathlib import Path
import sys

import appdirs

from rich import print as rprint

_printed_announcement = False


def announce(msg: str, only_once: bool = True) -> None:
    global _printed_announcement
    if only_once and _printed_announcement:
        return
    local_state_path = Path(appdirs.user_state_dir('backend.ai', 'Lablup'))
    try:
        with open(local_state_path / 'announcement.json', 'rb') as f_current:
            last_state = json.load(f_current)
    except IOError:
        last_state = {'hash': '', 'dismissed': False}

    hasher = hashlib.sha256()
    hasher.update(msg.encode('utf8'))
    msg_hash = hasher.hexdigest()

    if not (last_state['hash'] == msg_hash and last_state['dismissed']):
        rprint('[bold cyan]The server has an announcement![/]', file=sys.stderr)
        rprint('[bold cyan]----------[/]', file=sys.stderr)
        rprint(f'[bold]{msg}[/]', file=sys.stderr)
        rprint('[bold cyan]----------[/]', file=sys.stderr)
    _printed_announcement = True

    last_state['hash'] = msg_hash
    with open(local_state_path / 'announcement.json', 'w') as f_new:
        json.dump(last_state, f_new)
