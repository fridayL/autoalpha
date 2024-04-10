import os
import pathlib
import re
import sys
import json
import subprocess
import traceback
from hashlib import md5
from pathlib import Path
from typing import Dict, List, Optional, Union, Tuple
from concurrent.futures import ThreadPoolExecutor, TimeoutError

from autoalpha.oai.schema import ASSISTANT, Message
from autoalpha.tools.tools_base import ToolsBase, register_tool


UNKNOWN = "unknown"
TIMEOUT_MSG = "Timeout"
WIN32 = sys.platform == "win32"
PATH_SEPARATOR = WIN32 and "\\" or "/"
DEFAULT_TIMEOUT = 600
WORKING_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "extensions")


def get_powershell_command():
    try:
        result = subprocess.run(["powershell", "$PSVersionTable.PSVersion.Major"], capture_output=True, text=True)
        if result.returncode == 0:
            return "powershell"

    except FileNotFoundError:
        # This means that 'powershell' command is not found so now we try looking for 'pwsh'
        try:
            result = subprocess.run(
                ["pwsh", "-Command", "$PSVersionTable.PSVersion.Major"], capture_output=True, text=True
            )
            if result.returncode == 0:
                return "pwsh"

        except FileNotFoundError:
            if WIN32:
                logging.warning("Neither powershell nor pwsh is installed but it is a Windows OS")
            return None


powershell_command = get_powershell_command()


def _cmd(lang):
    if lang.startswith("python") or lang in ["bash", "sh", powershell_command]:
        return lang
    if lang in ["shell"]:
        return "sh"
    if lang in ["ps1", "pwsh", "powershell"]:
        return powershell_command

    raise NotImplementedError(f"{lang} not recognized in code execution")


def execute_code(
    code: Optional[str] = None,
    timeout: Optional[int] = None,
    filename: Optional[str] = None,
    work_dir: Optional[str] = None,
    use_docker: Union[List[str], str, bool] = False,
    lang: Optional[str] = "python",
) -> Tuple[int, str, Optional[str]]:
    """Execute code in a docker container.
    This function is not tested on MacOS.

    Args:
        code (Optional, str): The code to execute.
            If None, the code from the file specified by filename will be executed.
            Either code or filename must be provided.
        timeout (Optional, int): The maximum execution time in seconds.
            If None, a default timeout will be used. The default timeout is 600 seconds. On Windows, the timeout is not enforced when use_docker=False.
        filename (Optional, str): The file name to save the code or where the code is stored when `code` is None.
            If None, a file with a randomly generated name will be created.
            The randomly generated file will be deleted after execution.
            The file name must be a relative path. Relative paths are relative to the working directory.
        work_dir (Optional, str): The working directory for the code execution.
            If None, a default working directory will be used.
            The default working directory is the "extensions" directory under
            "path_to_autogen".
        use_docker (list, str or bool): The docker image to use for code execution.
            Default is True, which means the code will be executed in a docker container. A default list of images will be used.
            If a list or a str of image name(s) is provided, the code will be executed in a docker container
            with the first image successfully pulled.
            If False, the code will be executed in the current environment.
            Expected behaviour:
                - If `use_docker` is not set (i.e. left default to True) or is explicitly set to True and the docker package is available, the code will run in a Docker container.
                - If `use_docker` is not set (i.e. left default to True) or is explicitly set to True but the Docker package is missing or docker isn't running, an error will be raised.
                - If `use_docker` is explicitly set to False, the code will run natively.
            If the code is executed in the current environment,
            the code must be trusted.
        lang (Optional, str): The language of the code. Default is "python".

    Returns:
        int: 0 if the code executes successfully.
        str: The error message if the code fails to execute; the stdout otherwise.
        image: The docker image name after container run when docker is used.
    """
    if all((code is None, filename is None)):
        error_msg = f"Either {code=} or {filename=} must be provided."
        raise AssertionError(error_msg)


    timeout = timeout or 1000
    original_filename = filename
    if filename is None:
        code_hash = md5(code.encode()).hexdigest()
        # create a file with a automatically generated name
        filename = f"tmp_code_{code_hash}.{'py' if lang.startswith('python') else lang}"
    if work_dir is None:
        work_dir = WORKING_DIR

    filepath = os.path.join(work_dir, filename)
    file_dir = os.path.dirname(filepath)
    os.makedirs(file_dir, exist_ok=True)

    if code is not None:
        with open(filepath, "w", encoding="utf-8") as fout:
            fout.write(code)

    if not use_docker:
        # already running in a docker container or env
        cmd = [
            sys.executable if lang.startswith("python") else _cmd(lang),
            f".\\{filename}" if WIN32 else filename,
        ]
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(
                subprocess.run,
                cmd,
                cwd=work_dir,
                capture_output=True,
                text=True,
            )
            try:
                result = future.result(timeout=timeout)
            except TimeoutError:
                if original_filename is None:
                    os.remove(filepath)
                return 1, TIMEOUT_MSG, None
        if original_filename is None:
            os.remove(filepath)
        if result.returncode:
            logs = result.stderr
            if original_filename is None:
                abs_path = str(pathlib.Path(filepath).absolute())
                logs = logs.replace(str(abs_path), "").replace(filename, "")
            else:
                abs_path = str(pathlib.Path(work_dir).absolute()) + PATH_SEPARATOR
                logs = logs.replace(str(abs_path), "")
        else:
            logs = result.stdout
        return result.returncode, logs, None

def extract_code(text):
    # Match triple backtick blocks first
    triple_match = re.search(r'```[^\n]*\n(.+?)```', text, re.DOTALL)
    if triple_match:
        text = triple_match.group(1)
    else:
        try:
            text = json.loads(text)['code']
        except Exception:
            traceback.format_exception(*sys.exc_info())
    # If no code blocks found, return original text
    return text

@register_tool("code_interpreter")
class CodeInterpreter(ToolsBase):
    description = "python代码执行器，可以用于执行任意python代码"
    parameters = [{
        'name': 'code',
        'type': 'string',
        'description': '可以执行的python代码片段',
        'required': True
    }]

    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self.file_access = True
        self.use_docker = False

    def call(self,
             params: Union[str, dict],
             files: List[str] = None,
             timeout: Optional[int] = 30,
             **kwargs) -> str:
        try:
            code = params[0]['value']
        except Exception:
            code = extract_code(params)

        if not code.strip():
            return ''
        # download file
        # if files:
        #     os.makedirs(WORK_DIR, exist_ok=True)
        #     for file in files:
        #         try:
        #             save_url_to_local_work_dir(file, WORK_DIR)
        #         except Exception:
        #             traceback.format_exception(*sys.exc_info())
        fixed_code = code + '\n\n'  # Prevent code not executing in notebook due to no line breaks at the end
        result_state, result, _ = execute_code(fixed_code)
        print(result)
        return [Message(ASSISTANT, result)]
