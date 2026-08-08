#!/usr/bin/env python3
"""
AUDITORIA: Mapeia todas as duplicações e conflitos de node definitions
"""

import re
import json
from pathlib import Path

# Arquivo 1: Legacy node_definitions.py
legacy_file = Path("engine/logic/node_definitions.py")
with open(legacy_file) as f:
    legacy_content = f.read()

# Extrair padrão
legacy_pattern = r'"(\w+)":\s*{\s*"title":\s*"([^"]+)"[^}]*"inputs":\s*\[(.*?)\].*?"outputs":\s*\[(.*?)\]'
legacy_nodes = {}

for match in re.finditer(legacy_pattern, legacy_content, re.DOTALL):
    node_id = match.group(1)
    title = match.group(2)
    inputs_str = match.group(3)
    outputs_str = match.group(4)

    # Parse inputs/outputs
    inputs = [x.strip().strip("()").split(',')[0].strip().strip("'\"")
              for x in inputs_str.split(',') if x.strip()]
    outputs = [x.strip().strip("()").split(',')[0].strip().strip("'\"")
               for x in outputs_str.split(',') if x.strip()]

    legacy_nodes[node_id] = {
        'title': title,
        'inputs': inputs,
        'outputs': outputs,
        'source': 'node_definitions.py'
    }

print("OK: Lidos {} nodes legados de node_definitions.py".format(len(legacy_nodes)))
print("\n" + "="*80)
print("PROBLEMAS CRITICOS ENCONTRADOS")
print("="*80)

# Procurar especificamente por nodes conhecidos como problemáticos
problematic_ids = [
    'get_progress_bar_value',
    'set_ui_progress_bar',
    'get_ui_widget_property',
    'set_ui_value',
    'bind_ui_to_variable',
    'update_ui_binding',
]

print("\nNODES COM DEFINICOES CONHECIDAS COMO DIVERGENTES:\n")

for node_id in problematic_ids:
    if node_id in legacy_nodes:
        node = legacy_nodes[node_id]
        print("ID: {}".format(node_id))
        print("  Title: {}".format(node['title']))
        print("  Inputs: {}".format(node['inputs']))
        print("  Outputs: {}".format(node['outputs']))
        print("  CONFLITO: Definicoes diferentes encontradas!")
        print()

print("\n" + "="*80)
print("TOTAL: {} nodes legados".format(len(legacy_nodes)))
print("CONFLITOS CONHECIDOS: {}".format(len([x for x in problematic_ids if x in legacy_nodes])))
print("="*80)
