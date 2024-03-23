import re
import json
import copy
from collections import OrderedDict
from typing import Dict, Iterator, List, Optional, Union

from autoalpha.agent.groupchat_manager import GroupChatManager
from autoalpha.agent.assistant_agent import AssistantAgent
from autoalpha.oai.schema import Message

GROUP_CHAT_TEMPLATE = """
在一个角色扮演中你是一个负责控制发言的角色，你可以根据角色对话控制下一轮对话的角色以及要做的事情,并且每次只能最多选一个speaker
在任务中有如下角色：
{agent_descs}
最终输出结果为：
json```{{"speaker":"", "task":""}}```
其中
speaker: 必须是[{agent_names}] 里面的
task: 是需要执行具体的任务
如果你觉得根据历史对话已经得到了答案,请只输出以下内容
json```{{"speaker":"FINISHED", "task":"最终输出结果"}}```
"""
PATTERN_JSON = r'```json(.*?)```'

def parse_json(msg):
    if re.findall("```json", msg.content):
        matches = re.findall(PATTERN_JSON, msg.content, re.DOTALL)
        cleaned_string_list = []
        for match in matches:
            cleaned_string_list.append(json.loads(match.strip()))
        return cleaned_string_list
    return []

class GroupChat(GroupChatManager):

    def __init__(self, configs, llm):

        self.agents = self._init_agents(configs)
        self.agent_names = ",".join([ x.name for k, x in self.agents.items()])
        self.agent_descs = "\n\n".join([ x.name + ":" + x.description for k, x in self.agents.items()]) + "\n\n"
        system_message = GROUP_CHAT_TEMPLATE.format(agent_descs=self.agent_descs, agent_names=self.agent_names)
        super(GroupChat, self).__init__(system_message=system_message, llm=llm)

    def _select_agents(self, messages: List[Message]) -> List[AssistantAgent]:
        msg = messages[-1]
        cleaned_string_list = parse_json(msg)
        print(cleaned_string_list)
        for result in cleaned_string_list[::-1]:
            if "speaker" in result:
                if result["speaker"] == "FINISHED":
                    return self
                else:
                    return self.agents[result["speaker"]]
            elif "task_to" in result:
                return self.agents[result["task_to"].strip()]

    # TODO
    # utils func 
    def _parse_next_agent(self, messages: List[Message]) -> Optional[AssistantAgent]:
        msg = messages[-1]
        if re.findall("```json", msg.content):
            cleaned_string = re.sub(r"""```.*?\n""", '', msg.content)
            cleaned_string = re.sub(r"""```""", '', cleaned_string).strip()
            parsed_json = json.loads(cleaned_string)

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
        max_round = 12
        round = 0
        # outputs = self._call_llm(messages)

        # for output in outputs:
        #     print("****************", output)
        while True and max_round> round:
            print("round ", round)
            if round == 0:
                for dt in self.agents["问题拆解工程师"].run(messages=messages):
                    if dt.function_call:
                        print("中间结果", dt)
                        continue
                    messages += [dt]
            else:
                agents_turn = self._select_agents(messages=messages)
                if not agents_turn:
                    new_msg = []
                    outputs = self._call_llm(messages)
                    for output in outputs:
                        new_msg.append(output)
                    agents_turn = self._select_agents(messages=new_msg)
                if agents_turn == self:
                    print("finished task")
                    break
                for dt in agents_turn.run(messages=messages):
                    if dt.function_call:
                        print("中间结果", dt)
                        continue
                    messages +=[dt]
            round +=1
        return [messages[-1]]

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
        
        agents = OrderedDict()
        background_system = """这是一个项目组,项目是为了解决用户问题 \n"""
        for config in configs['agents']:
            system, selected_tools, llm = _build_system_from_role_config(
                config)
                # Create npc agent by config
            other_agents = []
            for ag in configs['agents']:
                if ag['name'] != config['name']:
                    other_agents.append(ag['name'])
            agents.update({config['name']:
                AssistantAgent(
                    llm=llm,
                    system_message=background_system + system +
                    f'\n\n项目他成员包括：{", ".join(other_agents)}\n'
                    +
                    """
                    你的输出有三种格式选择：
                    1. 完成其他成员交给你的task并以```json{{"content": "", "task_from": ""}}```返回结果
                    2. 要求其他成员完成某项task并以```json{{"content": "", "task_to": ""}}
                    3. 如果你要使用工具请按照工具要求进行参数解析
                    注: task_from 和task_to必须是 [{other_agents}] 里面的
                    """,
                    function_list=selected_tools,
                    name=config['name'],
                    description=config['description'])})
        return agents


