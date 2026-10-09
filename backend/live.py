import json
import asyncio
import os
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import httpx
from pydantic import BaseModel
import tempfile
import base64

from rag import get_context, normalize_query
from llm import groq_client
GROQ_MODEL="qwen/qwen3.8-27b"
from tts import generate_voice, clean_script_for_tts

router = APIRouter()

# Store active sessions
sessions = {}

SYSTEM_PROMPT = """You are Priya ma'am, an Indian AI Science Teacher for Class 10.
Speak in Hinglish (a mix of Hindi and English).
Keep your explanations VERY brief (2-3 sentences max per turn), conversational, and interactive.
Always end by asking a short question to check understanding.
Base your explanations on the following NCERT context:
{context}
"""

async def process_audio_to_text(audio_bytes):
    # Use Groq Whisper
    try:
        client = groq_client
        with tempfile.NamedTemporaryFile(suffix='.webm', delete=False) as f:
            f.write(audio_bytes)
            tmp_path = f.name
            
        with open(tmp_path, 'rb') as f:
            transcription = client.audio.transcriptions.create(
                file=('audio.webm', f.read()),
                model='whisper-large-v3',
                response_format='json',
                language='en',
                temperature=0.0
            )
        os.remove(tmp_path)
        return transcription.text
    except Exception as e:
        print('STT Error:', e)
        return ''

async def generate_llm_response(history):
    client = groq_client
    try:
        completion = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=history,
            temperature=0.7,
            max_tokens=150,
        )
        return completion.choices[0].message.content
    except Exception as e:
        print('LLM Error:', e)
        return 'Network issue ho gaya. Phir se bolo?'

@router.websocket('/ws/live')
async def websocket_live_endpoint(websocket: WebSocket):
    await websocket.accept()
    history = []
    
    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            
            if msg['type'] == 'init':
                topic = msg.get('topic')
                doubt = msg.get('doubt')
                
                query_to_search = doubt if doubt else topic
                clean_topic = normalize_query(query_to_search)
                context = get_context(clean_topic)
                
                sys_prompt = SYSTEM_PROMPT.format(context=context)
                history.append({'role': 'system', 'content': sys_prompt})
                
                if doubt:
                    history.append({'role': 'user', 'content': f'Answer this doubt briefly in Hinglish: {doubt}'})
                else:
                    history.append({'role': 'user', 'content': f'Explain {topic} briefly in Hinglish.'})
                
                # Get initial response
                await websocket.send_json({'type': 'status', 'text': 'Thinking...'})
                response_text = await generate_llm_response(history)
                history.append({'role': 'assistant', 'content': response_text})
                
                await websocket.send_json({'type': 'status', 'text': 'Speaking...'})
                audio_bytes = generate_voice(clean_script_for_tts(response_text))
                
                audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
                await websocket.send_json({"type": "audio", "audio": audio_b64, "text": response_text})
                
            elif msg['type'] == 'audio':
                await websocket.send_json({'type': 'status', 'text': 'Listening...'})
                audio_b64 = msg['data']
                audio_bytes = base64.b64decode(audio_b64)
                
                await websocket.send_json({'type': 'status', 'text': 'Transcribing...'})
                user_text = await process_audio_to_text(audio_bytes)
                if not user_text.strip():
                    await websocket.send_json({'type': 'status', 'text': 'Could not hear you.'})
                    continue
                    
                await websocket.send_json({'type': 'user_text', 'text': user_text})
                history.append({'role': 'user', 'content': user_text})
                
                await websocket.send_json({'type': 'status', 'text': 'Thinking...'})
                response_text = await generate_llm_response(history)
                history.append({'role': 'assistant', 'content': response_text})
                
                await websocket.send_json({'type': 'status', 'text': 'Speaking...'})
                audio_bytes = generate_voice(clean_script_for_tts(response_text))
                
                audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
                await websocket.send_json({"type": "audio", "audio": audio_b64, "text": response_text})
                
    except WebSocketDisconnect:
        print('Client disconnected')
    except Exception as e:
        print('WS Error:', e)

