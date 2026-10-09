with open(r'C:\Users\admin\Desktop\vietnam\AI_teacher\backend\main.py', 'r', encoding='utf-8') as f:
    lines = f.read()

lines = lines.replace('version=\"1.0.0\"\n)', 'version=\"1.0.0\"\n)\n\napp.include_router(live.router)')

with open(r'C:\Users\admin\Desktop\vietnam\AI_teacher\backend\main.py', 'w', encoding='utf-8') as f:
    f.write(lines)
