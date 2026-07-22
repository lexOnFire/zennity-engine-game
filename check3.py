import json
res=json.load(open('api3.json'))
run=res['workflow_runs'][0]
print('Run ID:', run['id'], 'Status:', run['status'], 'Conclusion:', run['conclusion'])
