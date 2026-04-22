import learning_observer.communication_protocol.integration
import learning_observer.cache
import learning_observer.prestartup
import learning_observer.settings

import lo_gpt.gpt

template = """[Task]\n{question}\n\n[Essay]\n{text}"""
rubric_template = """{task}\n\n[Rubric]\n{rubric}"""


@learning_observer.communication_protocol.integration.publish_function('wo_bulk_essay_analysis.gpt_essay_prompt')
async def process_student_essay(text, prompt, system_prompt, tags):
    '''
    This method processes text with a prompt through GPT.

    We use a closure to allow the system to connect to the memoization KVS.
    '''
    copy_tags = tags.copy()

    @learning_observer.cache.async_memoization()
    async def gpt(gpt_prompt):
        completion = await lo_gpt.gpt.gpt_responder.chat_completion(gpt_prompt, system_prompt)
        return completion

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
        copy_tags['student_text'] = text
        formatted_prompt = prompt.format(**copy_tags)

        output = {
            'text': text,
            'feedback': await gpt(formatted_prompt),
            'prompt': prompt
        }
    return output
