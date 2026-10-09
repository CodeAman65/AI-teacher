with open(r'live.py', 'r', encoding='utf-8') as f:
    lines = f.read()

import re

# find the init section
old_code = '''                topic = msg['topic']
                clean_topic = normalize_query(topic)
                context = get_context(clean_topic)
                
                sys_prompt = SYSTEM_PROMPT.format(context=context)
                history.append({'role': 'system', 'content': sys_prompt})
                history.append({'role': 'user', 'content': f'Explain {topic} briefly.'})'''

new_code = '''                topic = msg.get('topic')
                doubt = msg.get('doubt')
                
                query_to_search = doubt if doubt else topic
                clean_topic = normalize_query(query_to_search)
                context = get_context(clean_topic)
                
                sys_prompt = SYSTEM_PROMPT.format(context=context)
                history.append({'role': 'system', 'content': sys_prompt})
                
                if doubt:
                    history.append({'role': 'user', 'content': f'Answer this doubt briefly in Hinglish: {doubt}'})
                else:
                    history.append({'role': 'user', 'content': f'Explain {topic} briefly in Hinglish.'})'''

if old_code in lines:
    lines = lines.replace(old_code, new_code)
else:
    print('Could not find old code')

with open(r'live.py', 'w', encoding='utf-8') as f:
    f.write(lines)
