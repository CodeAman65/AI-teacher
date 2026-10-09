with open(r'live.py', 'r', encoding='utf-8') as f:
    lines = f.read()

lines = lines.replace('from llm import get_groq_client', 'from llm import groq_client')
lines = lines.replace('client = get_groq_client()', 'client = groq_client')

with open(r'live.py', 'w', encoding='utf-8') as f:
    f.write(lines)
