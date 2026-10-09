with open(r'live.py', 'r', encoding='utf-8') as f:
    lines = f.read()

lines = lines.replace('from llm import get_groq_client, GROQ_MODEL', 'from llm import get_groq_client\nGROQ_MODEL=\"qwen/qwen3.8-27b\"')

with open(r'live.py', 'w', encoding='utf-8') as f:
    f.write(lines)
