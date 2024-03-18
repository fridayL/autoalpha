from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Union


TOOL_REGISTRY = {}

def register_tool(name, allow_overwrite=False):

    def decorator(cls):
        if name in TOOL_REGISTRY:
            if allow_overwrite:
                pass
            else:
                raise ValueError(
                    f'Tool `{name}` already exists! Please ensure that the tool name is unique.'
                )
        cls.name = name
        TOOL_REGISTRY[name] = cls

        return cls

    return decorator




class ToolsBase(ABC):
    name: str = ''
    description: str = ''
    parameters: List[Dict] = []

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}

        self.name_for_human = self.config.get('name_for_human', self.name)
        if not hasattr(self, 'args_format'):
            self.args_format = self.config.get('args_format', 'json need provide')
        self.function = self._build_function()

    @abstractmethod
    def call(self, params: Union[str, Dict], **kwargs):
        """
        workflow of the tool
        main api for function
        Args:
            params: The parameters of func_call.
            kwargs: Additional parameters for calling tools.
        """
        raise NotImplementedError

    def _build_function(self):
        return {
            'name_for_human': self.name_for_human,
            'name': self.name,
            'description': self.description,
            'parameters': self.parameters,
            'args_format': self.args_format
        }