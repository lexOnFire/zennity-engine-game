import json
res=json.load(open('check_runs.json'))
for run in res['check_runs']: print(f"{run['name']}: {run['conclusion']}\n{run['output']['text'] if run['output'] and 'text' in run['output'] else ''}")
