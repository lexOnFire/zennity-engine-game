import os
import re

def audit():
    targets = [
        "Registry", "Manager", "List", "Dict", "Menu", "Toolbar", "Command", "Inspector", "Component"
    ]
    
    findings = []
    
    for r, d, files in os.walk('engine'):
        if '__pycache__' in r: continue
        for f in files:
            if not f.endswith('.py'): continue
            path = os.path.join(r, f)
            with open(path, 'r', encoding='utf-8') as file:
                try:
                    lines = file.readlines()
                    for i, line in enumerate(lines):
                        # Look for class definitions that might be parallel registries
                        if re.search(r'class \w+(Registry|Manager)', line):
                            findings.append(f"{path}:{i+1} -> {line.strip()}")
                        # Look for static dictionaries or lists that might be configurations
                        elif re.search(r'^[ \t]*[A-Z_]+[ \t]*:[ \t]*(dict|list)[ \t]*=', line):
                            findings.append(f"{path}:{i+1} -> {line.strip()}")
                        # Look for decorators that might be registering things outside of metadata
                        elif re.search(r'@[a-z_]*register', line) and 'register_node' not in line and 'register_graph' not in line:
                            findings.append(f"{path}:{i+1} -> {line.strip()}")
                except Exception as e:
                    pass

    for finding in findings:
        print(finding)

if __name__ == '__main__':
    audit()
