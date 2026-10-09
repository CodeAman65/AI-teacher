import asyncio
import websockets
import os
import json
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv('OPENAI_API_KEY')

async def test():
    url = 'wss://api.openai.com/v1/realtime?model=gpt-realtime'
    headers = {
        'Authorization': f'Bearer {API_KEY}'
    }
    try:
        async with websockets.connect(url, additional_headers=headers) as ws:
            print('Connected to OpenAI Realtime!')
            setup = {
                'type': 'session.update',
                'session': {
                    'modalities': ['text', 'audio'],
                    'voice': 'shimmer'
                }
            }
            await ws.send(json.dumps(setup))
            
            for _ in range(2):
                msg = await ws.recv()
                print('Received:', msg[:150])
    except Exception as e:
        print('Error:', e)

if __name__ == '__main__':
    asyncio.run(test())
