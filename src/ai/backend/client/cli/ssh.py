from datetime import datetime
from pathlib import Path
import sys

import click
import humanize

import subprocess
import sys

"""
from . import main
from .interaction import ask_yn
from .pretty import print_done, print_error, print_fail, print_info, print_wait
from ..session import Session

@main.group()
def ssh():
    '''Provides ssh operations.'''


"""

def ssh(user, host, port):

    
    # Ports are handled in ~/.ssh/config since we use OpenSSH
    COMMAND="uname -a"

    ssh = subprocess.Popen(["ssh", "-o", "StrictHostKeyChecking=no", "-i", "id_container",  "work@localhost", "-p", "9922"],
                        shell=False,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE)
    result = ssh.stdout.readlines()
    if result == []:
        error = ssh.stderr.readlines()
        print (sys.stderr, "ERROR: %s" % error)
    else:
        print (result)

    return 1


def main():
    # connect to server
    print(1)
    user = 'work'
    host = 'localhost2'
    port = 9922
    ssh(user, host, port)
    print("Done")

    return 1



if __name__=="__main__":
    main()