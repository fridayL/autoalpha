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
from autoalpha.oai.openai_chat import OpenaiChat




class AgentManager(Agent):

    def __init__(self,
                name: Optional[str] = None,
                system_message: Optional[str] = "You are a helpful AI Assistant.",
                description: Optional[str] = None,
                function_list: Optional[List[Union[str, Dict]]] = None,
                llm: Optional[Union[Dict, BaseChat]] = None):
        
        # self.name = name
        self.system_message = system_message
        if isinstance(llm, dict):
            self.llm = OpenaiChat(llm)

    def run(self, messages:List[Union[Dict, Message]]) -> Union[Iterator[List], Iterator[List[Dict]]]:

        trans_object = []
        messages = copy.deepcopy(messages)
        for msg in messages:
            if isinstance(msg, dict):
                trans_object.append(Message(**msg))
            else:
                trans_object.append(msg)


        print(trans_object)
        for rsp in self._run(messages=trans_object):
            yield rsp

    def _run(self, messages:List[Message]) -> Iterator[List[Message]]:
        repsonse = []
        return self._call_llm(messages)

    def _call_llm(
        self,
        messages: List[Message],
        functions: Optional[List[Dict]] = None,
        stream: bool = True,
    ) -> Iterator[List[Message]]:
        """The interface of calling LLM for the agent.

        We prepend the system_message of this agent to the messages, and call LLM.

        Args:
            messages: A list of messages.
            functions: The list of functions provided to LLM.
            stream: LLM streaming output or non-streaming output.
              For consistency, we default to using streaming output across all agents.

        Yields:
            The response generator of LLM.
        """
        messages = copy.deepcopy(messages)
        if messages[0][ROLE] != SYSTEM:
            messages.insert(0, Message(role=SYSTEM,
                                       content=self.system_message))
        elif isinstance(messages[0][CONTENT], str):
            messages[0][CONTENT] = self.system_message + messages[0][CONTENT]
            
        return self.llm.chat(messages=messages,
                             functions=functions,
                             stream=stream)
    

    


    

