import asyncio
import functools
import openai
import os
from concurrent.futures import ThreadPoolExecutor

import learning_observer.communication_protocol.integration
import learning_observer.settings

model = 'gpt-3.5-turbo-16k'
template = """[Task]\n{question}\n\n[Essay]\n{text}"""
rubric_template = """{task}\n\n[Rubric]\n{rubric}"""
openai.api_key = learning_observer.settings.module_setting('writing_observer', 'openai_api_key', os.getenv('OPENAI_API_KEY'))


@learning_observer.communication_protocol.integration.publish_function('writing_observer.gpt_essay_prompt')
async def process_student_essay(text, prompt, system_prompt, rubric):
    '''
    This method processes text with a prompt through GPT.

    We use a closure to allow the system to connect to the memoization KVS.
    '''

    executor = ThreadPoolExecutor()

    @learning_observer.cache.async_memoization()
    async def gpt(gpt_prompt):
        loop = asyncio.get_event_loop()
        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': gpt_prompt}
        ]
        partial = functools.partial(openai.ChatCompletion.create, model=model, messages=messages)
        completion = await loop.run_in_executor(executor, partial)
        return completion["choices"][0]["message"]["content"]

    if len(prompt) == 0:
        output = {
            'text': text,
            'feedback': 'No prompt provided yet.',
            'prompt': prompt
        }
    elif len(text) == 0:
        output = {
            'text': text,
            'feedback': 'No text available for this student.',
            'prompt': prompt
        }
    else:
        formatted_prompt = template.format(question=prompt, text=text)
        if len(rubric) > 0:
            formatted_prompt = rubric_template.format(task=formatted_prompt, rubric=rubric)

        output = {
            'text': text,
            'feedback': await gpt(formatted_prompt),
            'prompt': prompt
        }
    return output
