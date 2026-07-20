import json
res=json.load(open('jobs.json'))
for job in res['jobs']: print(f"Job {job['name']}: {job['conclusion']}")
