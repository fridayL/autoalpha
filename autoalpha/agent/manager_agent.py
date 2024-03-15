import asyncio
import copy
import functools
import inspect
import json
import logging
import re
from collections import defaultdict
from typing import Any, Awaitable, Callable, Dict, List, Iterator, Literal, Optional, Tuple, Type, TypeVar, Union


from autoalpha.oai.schema import (CONTENT, DEFAULT_SYSTEM_MESSAGE, FUNCTION,
                                   ROLE, SYSTEM, Message)
from autoalpha.agent.agent_base import Agent

from autoalpha.oai.base import BaseChat




class AgentManager(Agent):

    def __init__(self,
                name: Optional[str] = None,
                system_message: Optional[str] = "You are a helpful AI Assistant.",
                description: Optional[str] = None,
                function_list: Optional[List[Union[str, Dict]]] = None,
                llm: Optional[Union[Dict, BaseChat]] = None):
        
        self.name = name

        self.llm = llm

    def run(self, messages:List[Dict, Message]) -> Union[Iterator[List], Iterator[List[Dict]]]:

        trans_object = []
        
        for rsp in self._run(messages=messages):
            yield rsp

    def _run(self, messages:List[Dict]):
        raise NotImplementedError
    

    


    

