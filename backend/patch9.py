with open(r'C:\Users\admin\Desktop\vietnam\AI_teacher\backend\main.py', 'r', encoding='utf-8') as f:
    lines = f.read()

lines = lines.replace('allow_origins=[\"http://localhost:3000\", \"http://127.0.0.1:3000\"], allow_origin_regex=\".*\",', 'allow_origins=[\"*\"],')
lines = lines.replace('allow_credentials=True,', 'allow_credentials=False,')

with open(r'C:\Users\admin\Desktop\vietnam\AI_teacher\backend\main.py', 'w', encoding='utf-8') as f:
    f.write(lines)
