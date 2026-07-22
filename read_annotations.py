import json
res=json.load(open('annotations.json'))
for a in res: print(f"{a['path']}:{a['start_line']} - {a['message']}")
