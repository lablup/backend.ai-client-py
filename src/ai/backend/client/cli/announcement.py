import hashlib
import json
from pathlib import Path
import sys

import appdirs

from .pretty import print_info


_printed_announcement = False


def announce(msg: str, only_once: bool = True) -> None:
    global _printed_announcement
    if only_once and _printed_announcement:
        return
    local_state_path = Path(appdirs.user_state_dir('backend.ai', 'Lablup'))
    try:
        with open(local_state_path / 'announcement.json', 'rb') as f:
            last_state = json.load(f)
    except IOError:
        last_state = {'hash': '', 'dismissed': False}

    hasher = hashlib.sha256()
    hasher.update(msg.encode('utf8'))
    msg_hash = hasher.hexdigest()

    if not (last_state['hash'] == msg_hash and last_state['dismissed']):
        print_info("The server has an announcement!", file=sys.stderr)
        print('----------', file=sys.stderr)
        print(msg, file=sys.stderr)
        print('----------', file=sys.stderr)
    _printed_announcement = True

    last_state['hash'] = msg_hash
    with open(local_state_path / 'announcement.json', 'w') as f:
        json.dump(last_state, f)
