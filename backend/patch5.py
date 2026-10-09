with open(r'C:\Users\admin\Desktop\vietnam\AI_teacher\frontend\src\LiveSessionState.js', 'r', encoding='utf-8') as f:
    lines = f.read()

lines = lines.replace('type: \'init\', topic: jobData.chapter', 'type: \'init\', topic: jobData.chapter, doubt: jobData.doubt')

with open(r'C:\Users\admin\Desktop\vietnam\AI_teacher\frontend\src\LiveSessionState.js', 'w', encoding='utf-8') as f:
    f.write(lines)
