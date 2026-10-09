with open(r'C:\Users\admin\Desktop\vietnam\AI_teacher\backend\rag.py', 'r', encoding='utf-8') as f:
    lines = f.read()

lines = lines.replace('\u2713', '[OK]')
lines = lines.replace('?', '[OK]')

with open(r'C:\Users\admin\Desktop\vietnam\AI_teacher\backend\rag.py', 'w', encoding='utf-8') as f:
    f.write(lines)
