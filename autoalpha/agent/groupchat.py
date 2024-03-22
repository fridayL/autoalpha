import copy
from typing import Dict, Iterator, List, Optional, Union

from autoalpha.agent.groupchat_manager import GroupChatManager
from autoalpha.agent.assistant_agent import AssistantAgent
from autoalpha.oai.schema import Message

GROUP_CHAT_TEMPLATE = """
在一个角色扮演中你是一个负责控制发言的角色，你可以根据角色对话控制下一轮对话的角色以及要做的事情
在任务中有如下角色：
{agent_descs}
最终输出结果为：
json```{{"speaker":"", "task":""}}```
其中
speaker: 必须是
[{agent_names}] 
里面的
task: 是需要执行具体的任务
如果你觉得能够解决最初的用户问题，那么请直接返回以下
json```{{"speaker":"FINISHED", "task":"最终返回结果"}}```
"""


class GroupChat(GroupChatManager):

    def __init__(self, configs, llm):

        self.agents = self._init_agents(configs)
        self.agent_names = ",".join([ x.name for x in self.agents])
        self.agent_descs = "\n\n".join([ x.name + ":" + x.description for x in self.agents]) + "\n\n"
        system_message = GROUP_CHAT_TEMPLATE.format(agent_descs=self.agent_descs, agent_names=self.agent_names)
        print(system_message)
        super(GroupChat, self).__init__(system_message=system_message, llm=llm)

    def _parse_next_agent(self, messages: List[Message]) -> Optional[AssistantAgent]:
        return None

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

    def _run(self, messages: List[Message]) -> Iterator[List[Message]]:
        max_round = 10
        round = 0
        print("outputs***************************")
        outputs = self._call_llm(messages)

        for output in outputs:
            print("****************", output)
                

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
            for ag in configs['agents']:
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


