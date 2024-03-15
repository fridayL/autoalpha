import copy
from typing import Dict, Iterator, List, Optional, Union

from autoalpha.agent.agent_base import Agent
from autoalpha.oai.base import BaseChat


DEFAULT_SYSTEM_MESSAGE = """You are a helpful AI assistant.
Solve tasks using your coding and language skills."""

class AssistantAgent(Agent):

    def __init__(self, 
                 function_list: Optional[List[Union[str, Dict]]] = None,
                 llm: Optional[Union[Dict, BaseChat]] = None,
                 system_message: Optional[str] = DEFAULT_SYSTEM_MESSAGE,
                 name: Optional[str] = None,
                 description: Optional[str] = None,
                 files: Optional[List[str]] = None):
        pass
