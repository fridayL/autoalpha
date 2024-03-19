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
from autoalpha.tools.tools_base import register_tool, ToolsBase, TOOL_REGISTRY
from autoalpha.agent.agent_base import Agent

from autoalpha.oai.base import BaseChat
from autoalpha.oai.openai_chat import OpenaiChat


print("*****************",TOOL_REGISTRY)

class AgentManager(Agent):

    def __init__(self,
                name: Optional[str] = None,
                system_message: Optional[str] = "You are a helpful AI Assistant.",
                description: Optional[str] = None,
                function_list: Optional[List[Union[str, Dict]]] = None,
                llm: Optional[Union[Dict, BaseChat]] = None):
        super().__init__(name=name, system_message=system_message, description=description)
        self.name = name
        self.description = description
        self.system_message = system_message
        if isinstance(llm, dict):
            self.llm = OpenaiChat(llm)
        self.function_map = {}
        if function_list is not None:
            for func in function_list:
                self._load_tool(func)

    def run(self, messages:List[Union[Dict, Message]]) -> Union[Iterator[List], Iterator[List[Dict]]]:

        trans_object = []
        messages = copy.deepcopy(messages)
        for msg in messages:
            if isinstance(msg, dict):
                trans_object.append(Message(**msg))
            else:
                trans_object.append(msg)
        for rsp in self._run(messages=trans_object):
            yield rsp

    def _run(self, messages:List[Message]) -> Iterator[List[Message]]:
        repsonse = []
        return self._call_llm(messages, functions=[
                    func.function for func in self.function_map.values()
                ])

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
            
        outputs = self.llm.chat(messages=messages,
                             functions=functions,
                             stream=stream)
        for output in outputs:
            yield output
        output = outputs[-1]
        use_tool, action, action_input = self._parse_output(output)
        if use_tool:
            tools_results = self._call_tool(action, action_input)
            for tool_output in tools_results:
                yield tool_output

    def _call_tool(self,
                   tool_name: str,
                   tool_args: Union[str, dict] = '{}',
                   **kwargs):
        """The interface of calling tools for the agent.

        Args:
            tool_name: The name of one tool.
            tool_args: Model generated or user given tool parameters.

        Returns:
            The output of tools.
        """
        if tool_name not in self.function_map:
            return f'Tool {tool_name} does not exists.'
        return self.function_map[tool_name].call(tool_args, **kwargs)
    

    def _load_tool(self, tool: Union[str, Dict]):
        tool_name = tool
        tool_cfg = None
        if isinstance(tool, dict):
            tool_name = tool['name']
            tool_cfg = tool
        if tool_name not in TOOL_REGISTRY:
            raise NotImplementedError
        if tool_name not in self.function_map:
            self.function_map[tool_name] = TOOL_REGISTRY[tool_name](tool_cfg)


    def _parse_output(self, message: Message) -> Tuple[bool, str, str, str]:
        if message.function_call:
            use_tool = message.function_call
            tool_name = message.function_call.name
            tool_args = message.function_call.arguments
            return use_tool, tool_name, tool_args
        return False, '', ''
    


    

