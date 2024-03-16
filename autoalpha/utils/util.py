
import datetime
import hashlib
import json
import os
import re
import shutil
import socket
import sys
import traceback
import urllib
from typing import Dict, List, Literal, Optional, Union
from urllib.parse import urlparse



def get_function_description(function: Dict) -> str:
    """
    Text description of function
    """
    tool_desc_template = """### {name_for_human}\n\n{name_for_model}: {description_for_model} 输入参数：{parameters} {args_format}"""

    name = function.get('name', None)
    name_for_human = function.get('name_for_human', name)
    name_for_model = function.get('name_for_model', name)
    assert name_for_human and name_for_model
    args_format = function.get('args_format', '')
    return tool_desc_template.format(name_for_human=name_for_human,
                            name_for_model=name_for_model,
                            description_for_model=function['description'],
                            parameters=json.dumps(function['parameters'],
                                                  ensure_ascii=False),
                            args_format=args_format).rstrip()