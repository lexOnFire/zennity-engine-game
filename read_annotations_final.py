import json
res=json.load(open('annotations_final.json'))
for a in res: print(f"{a['path']}:{a['start_line']} - {a['message']}")
