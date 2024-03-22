import copy
import random
from typing import Dict, Iterator, List, Optional, Union

from autoalpha.agent.assistant_agent import AssistantAgent


class GroupChatManager(AssistantAgent):

    def __init__(self, 
                 agents: Union[List[AssistantAgent], Dict] = None,
                 configs = None,
                 ):
        super(GroupChatManager, self).__init__()
        self.agents = self._init_agents(configs=configs)

    def _init_agents(self, configs):

        def _build_system_from_role_config(config):
            role_chat_prompt = """你是{name}。{description}\n\n{instructions}"""

            name = config.get('name', '').strip()
            llm = config.get('llm', '')
            description = config.get('description', '').lstrip('\n').rstrip()
            instructions = config.get('instructions', '').lstrip('\n').rstrip()
            selected_tools = config.get('selected_tools', [])
            description = f'你的简介是：{description}'
            prompt = role_chat_prompt.format(name=name,
                                             description=description,
                                             instructions=instructions)
            return prompt, selected_tools, llm
        
        agents = []
        background_system = """这是一个项目组,项目是为了解决用户问题 \n"""
        for config in configs['agents']:
            system, selected_tools, llm = _build_system_from_role_config(
                config)
                # Create npc agent by config
            other_agents = []
            for ag in config['agents']:
                if ag['name'] != config['name']:
                    other_agents.append(ag['name'])
            agents.append(
                AssistantAgent(
                    llm=llm,
                    system_message=background_system + system +
                    f'\n\n项目他成员包括：{", ".join(other_agents)}\n'
                    +
                    """你可以要求项目其他成员完成具体任务，也可以根据上下文来完成其他项目成员要求你完成的任务,最终输出格式为
                    {{"content": "输出的内容", "recipient": ""}}
                    注： recipient可以为空当你仅仅完成别人任务时
                    """,
                    function_list=selected_tools,
                    name=config['name'],
                    description=config['description']))
        return agents

