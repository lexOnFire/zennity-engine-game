import json
res=json.load(open('check_runs_final3.json'))
for run in res['check_runs']: print(f"{run['name']}: {run['status']} - {run['conclusion']}")
