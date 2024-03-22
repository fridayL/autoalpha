from typing import Dict, Iterator, List, Optional, Union

from autoalpha.agent.groupchat_manager import GroupChatManager
from autoalpha.oai.schema import Message

GROUP_CHAT_TEMPLATE = """
在一个角色扮演中你是一个负责控制发言的角色，你可以根据角色对话控制下一轮对话的角色以及要做的事情
在任务重有如下角色：
{agent_descs}
最终输出结果为：
```json{{"speaker":"", "task":""}}```
其中
speaker: 必须是
[{agent_names}] 
里面的
task: 是需要执行具体的任务
如果你觉得能够解决最初的用户问题了，那么请返回
```json{{"speaker":"FINISHED", "task":"最终返回结果"}}```
"""


class GroupChat(GroupChatManager):

    def __init__(self, configs):
        super(GroupChat, self).__init__(configs)

    def _run(self, messages: List[Message]) -> Iterator[List[Message]]:
        