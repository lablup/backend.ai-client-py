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

def ssh_exec(user, host, path_id, port):

    if user is None or user =="":
        user = "work"
        
    if host is None or host == "":
        host="localhost"

    if path_id is None or path_id == "":
        path_id="~/.ssh/id_container"

    # Ports are handled in ~/.ssh/config since we use OpenSSH
    

    ssh = subprocess.Popen(["ssh", "-o", "StrictHostKeyChecking=no", "-i", path_id,  "{}@{}".format(user, host), "-p", str(port)],
                        shell=False)
    
    (stdoutdata, stderrdata) = ssh.communicate()
    
    return 1


def main():
    # connect to server
    print(1)
    user = 'work'
    host = 'localhost'
    port = 9922
    path_id = None

    ssh_exec(user, host, path_id, port)
    print("Done")

    return 1



if __name__=="__main__":
    main()