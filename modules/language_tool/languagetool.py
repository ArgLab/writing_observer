'''
A thin, async wrapper to languagetool
'''

import asyncio
import inspect

import aiohttp

session = None


async def check(language, text):
    '''
    Takes a language (e.g. `en-US`), and a text.

    Returns a JSON object of the LanguageTool spell / grammar
    check
    '''

    global session
    if session is None:
        session = aiohttp.ClientSession()
    if inspect.iscoroutinefunction(session):
        session = await session

    query = {
        'language': language,
        'text': text
    }
    resp = await session.post(
        'http://localhost:8081/v2/check',
        data=query
    )

    return await resp.json()


async def main():
    '''
    A simple test case, and demo of syntax
    '''
    en = await check('en-US', 'This is a tset of the emergecny...')
    print(en['matches'])
    pl = await check('pl', 'Sprawdzamy awarje, ale nie ma...')
    print(en['matches'])
    await session.close()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
