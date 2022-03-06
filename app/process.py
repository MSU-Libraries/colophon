"""
Process handling
"""
import os
import subprocess
import pathlib
import app

def exec_command(cmd: str|list, shell: bool=False, redirect_stderr: bool=False):
    """
    Run the given command or shell commands.
    args:
        cmd: The command and arguments
        shell: If set to true, then the command will be shell interpreted
        redirect_stderr: If set to true, then redirect stderr to stdout
    returns:
        tuple(int, list, list): Exit code, stdout lines as list, stderr lines as list
    """
    cmd = cmd if isinstance(cmd, list) else ([cmd] if shell else cmd.split())
    cmd[0] = os.path.join(app.install_path, cmd[0])
    app.logger.debug(f"Executing (shell={shell}): {cmd}")
    stderr_tgt=subprocess.STDOUT if redirect_stderr else subprocess.PIPE
    with subprocess.Popen(cmd, shell=shell, stdout=subprocess.PIPE, stderr=stderr_tgt) as proc:
        stdout, stderr = proc.communicate()
        app.logger.debug(f"Command exited with code: {proc.returncode}")
        return (
            proc.returncode,
            stdout.splitlines(keepends=True),
            [] if not stderr else stderr.splitlines(keepends=True)
        )

def write_output(
    directory: str,
    rcode: int,
    stdout: list,
    stderr: list,
    stdout_file: str="stdout.log",
    stderr_file: str="stderr.log"
) -> int:
    """
    Append the given output lines to files within the directory, creating the
    directory and files if needed. Create/append to an rcode file the given
    rcode provided.
    Returns:
        The rcode passed in
    """
    pathlib.Path(directory).mkdir(parents=True, exist_ok=True)
    with open(os.path.join(directory, f"rcode.{rcode}"), 'a', encoding='utf8') as rof:
        rof.write(f"{rcode}")
    with open(os.path.join(directory, stdout_file), 'ab') as sof:
        sof.writelines(stdout)
    with open(os.path.join(directory, stderr_file), 'ab') as sef:
        sef.writelines(stderr)
    return rcode
