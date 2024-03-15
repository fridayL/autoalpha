import copy
import os
from pprint import pformat
from typing import Dict, Iterator, List, Optional

import openai


if openai.__version__.startswith('0.'):
    from openai.error import OpenAIError
else:
    from openai import OpenAIError

from autoalpha.oai.base import BaseChat
from autoalpha.oai.schema import ASSISTANT, Message

OAI_PRICE1K = {
    "text-ada-001": 0.0004,
    "text-babbage-001": 0.0005,
    "text-curie-001": 0.002,
    "code-cushman-001": 0.024,
    "code-davinci-002": 0.1,
    "text-davinci-002": 0.02,
    "text-davinci-003": 0.02,
    "gpt-3.5-turbo-instruct": (0.0015, 0.002),
    "gpt-3.5-turbo-0301": (0.0015, 0.002),  # deprecate in Sep
    "gpt-3.5-turbo-0613": (0.0015, 0.002),
    "gpt-3.5-turbo-16k": (0.003, 0.004),
    "gpt-3.5-turbo-16k-0613": (0.003, 0.004),
    "gpt-35-turbo": (0.0015, 0.002),
    "gpt-35-turbo-16k": (0.003, 0.004),
    "gpt-35-turbo-instruct": (0.0015, 0.002),
    "gpt-4": (0.03, 0.06),
    "gpt-4-32k": (0.06, 0.12),
    "gpt-4-0314": (0.03, 0.06),  # deprecate in Sep
    "gpt-4-32k-0314": (0.06, 0.12),  # deprecate in Sep
    "gpt-4-0613": (0.03, 0.06),
    "gpt-4-32k-0613": (0.06, 0.12),
    # 11-06
    "gpt-3.5-turbo": (0.0015, 0.002),  # default is still 0613
    "gpt-3.5-turbo-1106": (0.001, 0.002),
    "gpt-35-turbo-1106": (0.001, 0.002),
    "gpt-4-1106-preview": (0.01, 0.03),
    "gpt-4-1106-vision-preview": (0.01, 0.03),  # TODO: support vision pricing of images
}



class OpenaiChat(BaseChat):

    def __init__(self, cfg: Optional[Dict] = None):
        super().__init__(cfg)
        self.model = self.model or 'gpt-3.5-turbo'
        cfg = cfg or {}

        api_base = cfg.get(
            'api_base',
            cfg.get(
                'base_url',
                cfg.get('model_server', ''),
            ),
        ).strip()


        api_key = cfg.get('api_key', '')
        if not api_key:
            api_key = os.getenv('OPENAI_API_KEY', 'EMPTY')
        api_key = api_key.strip()

        if openai.__version__.startswith('0.'):
            if api_base:
                openai.api_base = api_base
            if api_key:
                openai.api_key = api_key
            self._chat_complete_create = openai.ChatCompletion.create
        else:
            api_kwargs = {}
            if api_base:
                api_kwargs['base_url'] = api_base
            if api_key:
                api_kwargs['api_key'] = api_key

            # OpenAI API v1 does not allow the following args, must pass by extra_body
            extra_params = ['top_k', 'repetition_penalty']
            if any((k in self.generate_cfg) for k in extra_params):
                self.generate_cfg['extra_body'] = {}
                for k in extra_params:
                    if k in self.generate_cfg:
                        self.generate_cfg['extra_body'][
                            k] = self.generate_cfg.pop(k)
            if 'request_timeout' in self.generate_cfg:
                self.generate_cfg['timeout'] = self.generate_cfg.pop(
                    'request_timeout')

            def _chat_complete_create(*args, **kwargs):
                client = openai.OpenAI(**api_kwargs)
                return client.chat.completions.create(*args, **kwargs)

            self._chat_complete_create = _chat_complete_create

    def _chat_no_stream(self, messages: List[Message]) -> List[Message]:
        messages = [msg.model_dump() for msg in messages]
        response = self._chat_complete_create(model=self.model,
                                                messages=messages,
                                                stream=False,
                                                **self.generate_cfg)
        return [Message(ASSISTANT, response.choices[0].message.content)]