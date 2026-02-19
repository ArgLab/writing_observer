import asyncio

import learning_observer.kvs
import learning_observer.offline
import learning_observer.stream_analytics.helpers as sa_helpers

import writing_observer.writing_analysis


def create_key(email):
    return f'email-studentID-mapping:{email}'


async def run():
    learning_observer.offline.init('creds.yaml')
    kvs = learning_observer.kvs.KVS()
    reducer_function_name = sa_helpers.fully_qualified_function_name(writing_observer.writing_analysis.student_profile)
    all_keys = await kvs.keys()
    keys = [k for k in all_keys if 'Internal' in k and reducer_function_name in k]
    values = await kvs.multiget(keys)
    for profile in values:
        if 'email' not in profile or 'google_id' not in profile:
            continue
        await kvs.set(create_key(profile['email']), profile['google_id'])


if __name__ == '__main__':
    asyncio.run(run())
