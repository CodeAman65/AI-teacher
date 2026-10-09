with open(r'C:\Users\admin\Desktop\vietnam\AI_teacher\frontend\src\App.js', 'r', encoding='utf-8') as f:
    lines = f.read()

lines = lines.replace('import { useState, useEffect, useRef, useCallback } from \"react\";', 'import { useState, useEffect, useRef, useCallback } from \"react\";\nimport LiveSessionState from \"./LiveSessionState\";')

lines = lines.replace('setState(\"loading\");\n    setAttempt(1);\n\n    try {\n      const res = await fetch(\"http://localhost:8000/teach\", {', 'setState(\"live\"); return; \n    try {\n      const res = await fetch(\"http://localhost:8000/teach\", {')

lines = lines.replace('{state === \"loading\" && <LoadingState jobData={jobData} onCancel={handleCancel} />}', '{state === \"loading\" && <LoadingState jobData={jobData} onCancel={handleCancel} />}\n          {state === \"live\" && <LiveSessionState jobData={jobData} onCancel={handleCancel} />}')

with open(r'C:\Users\admin\Desktop\vietnam\AI_teacher\frontend\src\App.js', 'w', encoding='utf-8') as f:
    f.write(lines)

print('Updated App.js')
