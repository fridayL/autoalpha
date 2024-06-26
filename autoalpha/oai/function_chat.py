import re
import json
import copy
from abc import ABC
from typing import Dict, Iterator, List, Optional, Union


from autoalpha.oai.base import BaseChat
from autoalpha.oai.schema import ASSISTANT,SYSTEM, Message, FunctionCall
from autoalpha.utils.util import get_function_description


FN_CALL_TEMPLATE = """
# 工具调用
## 你拥有如下工具可以调用：
{tool_descs}
如果需要调用工具,名称必须是[{tool_names}]之一。
如果需要调用python解析器工具时parameters里面必须有有效的代码片段
并且输出的结果必须是以下格式其中一个
第一种：
json```
{{"function_name": "", "parameters": []\}}
```
需要调用的function_name，api tool名称
第二种：
json```
{{"function_name": "code_interpreter", "parameters": []\}}
```
如果你觉得需要生成代码才能回复问题，必须调用code_interpreter工具， parameters中的字段必须是可以执行的代码片段而不是任何参数
"""

PATTERN_JSON = r'```json(.*?)```'


class BaseFnChat(BaseChat, ABC):

    def __init__(self, cfg: Optional[Dict] = None):
        super().__init__(cfg)

    def _chat_with_functions(
        self,
        messages: List[Union[Message, Dict]],
        functions: List[Dict]
    ) -> Union[List[Message], Iterator[List[Message]]]:
        
        messages = self._prepare_fncall_system(messages, functions)

        return self._chat(messages)

    def _prepare_fncall_system(self, messages: List[Message],
                               functions: List[Dict]) -> List[Message]:
        tool_descs = '\n\n'.join(
        get_function_description(function) for function in functions)
        tool_names = ','.join(
            function.get('name', function.get('name_for_model', ''))
            for function in functions)
        tool_system = FN_CALL_TEMPLATE.format(tool_descs=tool_descs,
                                                tool_names=tool_names)

        assert messages[0].role == SYSTEM
        messages = copy.deepcopy(messages[:1]) + messages[1:]
        if isinstance(messages[0].content, str):
            messages[0].content += tool_system
        return messages

    def _preprocess_fncall_messages(self,
                                    messages: List[Message]) -> List[Message]:
        return messages

    def _preprocess_data(self, messages: List[Message]) -> List[Message]:
        messages = super()._preprocess_data(messages)
        messages = self._preprocess_fncall_messages(messages)
        return messages
    
    def  _postprocess_data(self, messages: List[Message]) -> List[Message]:
        messages = self._postprocess_fncall_messages(messages)
        return messages
    
    def _postprocess_fncall_messages(self, messages: List[Message]) -> List[Message]:
        new_messages = []
        for msg in messages:
            if re.findall("function_name", msg.content) and re.findall("```json", msg.content):
                print("******", msg)
                matches = re.findall(PATTERN_JSON, msg.content, re.DOTALL)
                cleaned_string = ''
                for match in matches:
                    cleaned_string = match
                    break
                parsed_json = json.loads(cleaned_string)
                new_messages.append(Message(msg.role,
                                            content=[], 
                                            function_call=FunctionCall(name=parsed_json["function_name"], arguments=parsed_json["parameters"])
                                            ))

            else:
                new_messages.append(msg)
        return new_messages
