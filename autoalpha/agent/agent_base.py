import copy
from abc import ABC, abstractmethod
from typing import Dict, Iterator, List, Optional, Tuple, Union, Protocol

class Agent(Protocol):

    @property
    def name(self):
        pass
    
    @property
    def description(self,):
        pass

    def run(self, ):
        pass

    def _run(self, ):
        pass


# class LLMAgent(Agent, Protocol):

#     def __init__(self):
#         super().__init__()


#     def _run(self, ):
#         pass