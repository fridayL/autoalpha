import copy
from abc import ABC, abstractmethod
from typing import Dict, Iterator, List, Optional, Tuple, Union, Protocol

class Agent(Protocol):

    def _call_tool(self,
                   *args,
                   **kwargs):
        pass
    def _call_llm(
        self
    ):
        pass

    def run(self, ):
        pass

    def _run(self, ):
        pass

    def _load_tool(self,):
        pass

# class LLMAgent(Agent, Protocol):

#     def __init__(self):
#         super().__init__()


#     def _run(self, ):
#         pass