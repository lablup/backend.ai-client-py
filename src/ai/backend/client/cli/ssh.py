import contextlib
import os
from pathlib import Path
import secrets
import signal
import subprocess
import sys
from typing import Iterator, List

import click

from . import main
from .pretty import print_info, print_fail, print_error


@contextlib.contextmanager
def container_ssh_ctx(session_ref: str, port: int) -> Iterator[Path]:
    random_id = secrets.token_hex(16)
    key_filename = "id_container"
    key_path = Path(f"~/.ssh/id_{random_id}").expanduser()
    try:
        subprocess.run(
            ["backend.ai", "download", session_ref, key_filename],
            shell=False,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
    except subprocess.CalledProcessError as e:
        print_fail(f"Failed to download the SSH key from the session (exit: {e.returncode}):")
        print(e.stdout.decode())
        sys.exit(1)
    os.rename(key_filename, key_path)
    try:
        print_info(f"running a temporary sshd proxy at localhost:{port} ...", file=sys.stderr)
        # proxy_proc is a background process
        proxy_proc = subprocess.Popen(
            [
                "backend.ai", "app", session_ref,
                "sshd", "-b", f"127.0.0.1:{port}",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        assert proxy_proc.stdout is not None
        lines: List[bytes] = []
        while True:
            line = proxy_proc.stdout.readline(1024)
            if not line:
                proxy_proc.wait()
                print_fail(f"Unexpected early termination of the sshd app command "
                           f"(exit: {proxy_proc.returncode}):")
                print((b"\n".join(lines)).decode())
                sys.exit(1)
            if f"127.0.0.1:{port}".encode() in line:
                break
            lines.append(line)
        lines.clear()
        yield key_path
    finally:
        proxy_proc.send_signal(signal.SIGINT)
        proxy_proc.wait()
        os.unlink(key_path)


@main.command(
    context_settings={
        "ignore_unknown_options": True,
        "allow_extra_args": True,
        "allow_interspersed_args": True,
    },
)
@click.argument("session_ref",  type=str, metavar='SESSION_REF')
@click.option('-p', '--port',  type=int, metavar='PORT', default=9922,
              help="the port number for localhost")
@click.pass_context
def ssh(ctx: click.Context, session_ref: str, port: int) -> None:
    """Execute the ssh command against the target compute session

    \b
    SESSION_REF: The user-provided name or the unique ID of a running compute session.

    All remaining options and arguments not listed here are passed to the ssh command as-is.
    """
    try:
        with container_ssh_ctx(session_ref, port) as key_path:
            ssh_proc = subprocess.run(
                [
                    "ssh",
                    "-o", "StrictHostKeyChecking=no",
                    "-i", key_path,
                    "work@localhost",
                    "-p", str(port),
                    *ctx.args,
                ],
                shell=False,
                check=False,  # be transparent against the main command
            )
            sys.exit(ssh_proc.returncode)
    except Exception as e:
        print_error(e)


@main.command(
    context_settings={
        "ignore_unknown_options": True,
        "allow_extra_args": True,
        "allow_interspersed_args": True,
    },
)
@click.argument("session_ref", type=str, metavar='SESSION_REF')
@click.argument("src", type=str, metavar='SRC')
@click.argument("dst", type=str, metavar='DST')
@click.option('-p', '--port',  type=str, metavar='PORT', default=9922,
              help="the port number for localhost")
@click.option('-r',  '--recursive', default=False, is_flag=True,
              help="recursive flag option to process directories")
@click.pass_context
def scp(ctx: click.Context, session_ref: str, src: str, dst: str, port: int, recursive: bool) -> None:
    """Execute the scp command against the target compute session

    \b
    The SRC and DST have the same format with the original scp command,
    either a remote path as "work@localhost:path" or a local path.

    SESSION_REF: The user-provided name or the unique ID of a running compute session.
    SRC: the source path
    DST: the destination path

    All remaining options and arguments not listed here are passed to the ssh command as-is.

    Examples:

    * Uploading a local directory to the session:

      > backend.ai scp mysess -p 9922 -r tmp/ work@localhost:tmp2/

    * Downloading a directory from the session:

      > backend.ai scp mysess -p 9922 -r work@localhost:tmp2/ tmp/
    """
    recursive_args = []
    if recursive:
        recursive_args.append("-r")
    try:
        with container_ssh_ctx(session_ref, port) as key_path:
            scp_proc = subprocess.run(
                [
                    "scp",
                    "-o", "StrictHostKeyChecking=no",
                    "-i", key_path,
                    "-P", str(port),
                    *recursive_args,
                    src, dst,
                    *ctx.args,
                ],
                shell=False,
                check=False,  # be transparent against the main command
            )
            sys.exit(scp_proc.returncode)
    except Exception as e:
        print_error(e)
