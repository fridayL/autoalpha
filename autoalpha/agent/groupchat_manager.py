import copy
import random
from typing import Dict, Iterator, List, Optional, Union



from autoalpha.oai.base import BaseChat
from autoalpha.agent.assistant_agent import AssistantAgent

DEFAULT_SYSTEM_MESSAGE = """You are a helpful AI assistant.
Solve tasks using your coding and language skills."""

class GroupChatManager(AssistantAgent):

    def __init__(self, 
                 function_list: Optional[List[Union[str, Dict]]] = None,
                 llm: Optional[Union[Dict, BaseChat]] = None,
                 system_message: Optional[str] = DEFAULT_SYSTEM_MESSAGE,
                 name: Optional[str] = None,
                 description: Optional[str] = None
                 ):
        super(GroupChatManager, self).__init__(function_list, llm, system_message, name, description)
        # self.agents = self._init_agents(configs)