with open(r'live.py', 'r', encoding='utf-8') as f:
    lines = f.read()

lines = lines.replace('from tts import generate_audio', 'from tts import generate_voice, clean_script_for_tts')

lines = lines.replace('audio_file = generate_audio(response_text)', 'audio_bytes = generate_voice(clean_script_for_tts(response_text))')

lines = lines.replace('with open(audio_file, \'rb\') as f:\n                    audio_b64 = base64.b64encode(f.read()).decode(\'utf-8\')\n                    \n                await websocket.send_json({\n                    \'type\': \'audio\', \n                    \'audio\': audio_b64,\n                    \'text\': response_text\n                })\n                os.remove(audio_file)', 'audio_b64 = base64.b64encode(audio_bytes).decode(\"utf-8\")\n                await websocket.send_json({\"type\": \"audio\", \"audio\": audio_b64, \"text\": response_text})')

with open(r'live.py', 'w', encoding='utf-8') as f:
    f.write(lines)
