import copy
import random
import time
from abc import ABC, abstractmethod
from typing import Dict, Iterator, List, Optional, Union
from .schema import ASSISTANT, Message
"""
message
[{"role", "content", "name", "function_call"}]
"""

class BaseLLM(ABC):
    pass
    
class BaseChat(BaseLLM):

    def __init__(self, cfg: Optional[Dict] = None):
        cfg = cfg or {}
        self.model = cfg.get('model', '')
        generate_cfg = copy.deepcopy(cfg.get('generate_cfg', {}))
        self.max_retries = generate_cfg.pop('max_retries', 0)
        self.generate_cfg = generate_cfg

    def _preprocess_data(self, messages: List[Union[Message, Dict]]):
        return messages

    def _postprocess_data(self, messages: List[Union[Message, Dict]]):
        return messages

    def chat(self,
        messages: List[Union[Message, Dict]],
        functions: Optional[List[Dict]] = None,
        stream: bool = True) -> str:

        messages = self._preprocess_data(messages)
        if functions:
            fncall_mode = True
        else:
            fncall_mode = False
        if fncall_mode:
            output = self._chat_with_functions(
                messages=messages,
                functions=functions
            )
            if isinstance(output, list):
                output = self._postprocess_data(output,
                                                fncall_mode=fncall_mode)
                return output
        return self._chat(messages, functions, fncall_mode)

    def _chat(self, messages: List[Message],
              functions: Optional[List[Dict]] = None, 
              fncall_mode: bool = False):
        return self._chat_no_stream(messages)
    

    def _chat_stream(
        self,
        messages: List[Message],
        delta_stream: bool = False,
    ) -> Iterator[List[Message]]:
        raise NotImplementedError


    def _chat_no_stream(
        self,
        messages: List[Message],
        delta_stream: bool = False,
    ) -> Iterator[List[Message]]:
        raise NotImplementedError


    def _chat_with_functions(
        self,
        messages: List[Union[Message, Dict]],
        functions: List[Dict],
        stream: bool = True,
        delta_stream: bool = False
    ) -> Union[List[Message], Iterator[List[Message]]]:
        raise NotImplementedError