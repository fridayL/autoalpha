import copy
from typing import Dict, Iterator, List, Optional, Union

from autoalpha.oai.base import BaseChat
from autoalpha.agent.manager_agent import AgentManager


DEFAULT_SYSTEM_MESSAGE = """You are a helpful AI assistant.
Solve tasks using your coding and language skills."""

class AssistantAgent(AgentManager):

    def __init__(self, 
                 function_list: Optional[List[Union[str, Dict]]] = None,
                 llm: Optional[Union[Dict, BaseChat]] = None,
                 system_message: Optional[str] = DEFAULT_SYSTEM_MESSAGE,
                 name: Optional[str] = None,
                 description: Optional[str] = None):
        super().__init__(
            function_list=function_list,
            llm=llm,
            system_message=system_message,
            name=name,
            description=description
        )
