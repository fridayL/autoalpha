import copy
import random
import time
from abc import ABC, abstractmethod
from typing import Dict, Iterator, List, Optional, Union
from schema import Message
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

    def _preprocess_data(self, messages):
        return messages

    def chat(self,
        messages: List[Union[Message, Dict]],
        functions: Optional[List[Dict]] = None) -> str:

        messages = self._preprocess_data(messages)
        if functions:
            fncall_mode = True
        else:
            fncall_mode = False

    def _chat(self, message):
        return self._chat_stream(message)

    @abstractmethod
    def _chat_stream(
        self,
        messages: List[Message],
        delta_stream: bool = False,
    ) -> Iterator[List[Message]]:
        raise NotImplementedError
