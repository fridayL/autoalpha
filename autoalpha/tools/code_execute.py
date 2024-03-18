import asyncio
import atexit
import base64
import glob
import io
import json
import os
import queue
import re
import shutil
import signal
import stat
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Union



from autoalpha.tools.tools_base import ToolsBase, register_tool


@register_tool("code_interpreter")
class CodeInterpreter(ToolsBase):
    description = "python 代码执行器，可以用于执行任意python代码"
    parameters = [{
        'name': 'code',
        'type': 'string',
        'description': '可以执行的代码',
        'required': True
    }]

    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)

        
