#!/usr/bin/env python3
"""
Script de validação do Logic Graph node database.

Verifica:
1. Se todos os nós em node_definitions.py estão documentados
2. Se há nós órfãos (descritos mas não definidos)
3. Se NODE_GROUPS cobre todos os nós principais
4. Se categorias são consistentes
"""

import sys
from pathlib import Path
from typing import Dict, Set, List

# Adiciona o projeto ao path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from engine.logic.node_definitions import NODE_DEFINITIONS
from editor.widgets.logic_graph.node_groups import NODE_GROUPS
from editor.widgets.logic_graph.definitions import NODE_DESCRIPTIONS


def flatten_groups(groups: Dict) -> Set[str]:
    """Flattena NODE_GROUPS para um set de node_types."""
    node_types = set()
    for category, subcategories in groups.items():
        for subcategory, nodes in subcategories.items():
            node_types.update(nodes)
    return node_types


def validate_node_definitions() -> tuple[List[str], List[str], List[str]]:
    """Valida node_definitions."""
    errors = []
    warnings = []
    info = []

    defined_nodes = set(NODE_DEFINITIONS.keys())
    grouped_nodes = flatten_groups(NODE_GROUPS)

    # Verificar nós não agrupados (fora de NODE_GROUPS)
    ungrouped = defined_nodes - grouped_nodes
    if ungrouped:
        warnings.append(f"[WARNING] {len(ungrouped)} nos nao agrupados em NODE_GROUPS:")
        for node in sorted(ungrouped):
            category = NODE_DEFINITIONS[node].get("category", "Custom")
            warnings.append(f"  - {node} ({category})")

    # Verificar nós órfãos (em NODE_GROUPS mas não em NODE_DEFINITIONS)
    orphaned = grouped_nodes - defined_nodes
    if orphaned:
        errors.append(f"[ERROR] {len(orphaned)} nos orfaos em NODE_GROUPS (nao existem em NODE_DEFINITIONS):")
        for node in sorted(orphaned):
            errors.append(f"  - {node}")

    # Verificar consistência de categorias
    category_mismatches = []
    for node_type in grouped_nodes:
        if node_type not in NODE_DEFINITIONS:
            continue
        defined_category = NODE_DEFINITIONS[node_type].get("category", "Custom")

        # Encontra a categoria no NODE_GROUPS
        grouped_category = None
        for cat, subcats in NODE_GROUPS.items():
            for subcat, nodes in subcats.items():
                if node_type in nodes:
                    grouped_category = cat
                    break
            if grouped_category:
                break

        if grouped_category and defined_category != grouped_category:
            category_mismatches.append((node_type, defined_category, grouped_category))

    if category_mismatches:
        errors.append(f"[ERROR] {len(category_mismatches)} incompatibilidades de categoria:")
        for node, defined_cat, grouped_cat in category_mismatches:
            errors.append(f"  - {node}: definida como '{defined_cat}' mas agrupada como '{grouped_cat}'")

    # Estatísticas
    info.append(f"[OK] {len(defined_nodes)} nos definidos")
    info.append(f"[OK] {len(grouped_nodes)} nos agrupados")
    info.append(f"[OK] {len(NODE_GROUPS)} categorias principais")

    total_subcats = sum(len(subcats) for subcats in NODE_GROUPS.values())
    info.append(f"[OK] {total_subcats} subcategorias")

    return errors, warnings, info


def validate_descriptions() -> tuple[List[str], List[str], List[str]]:
    """Valida se todos os nós têm descrições."""
    errors = []
    warnings = []
    info = []

    defined_nodes = set(NODE_DEFINITIONS.keys())

    # Nós sem descrição
    undocumented = []
    for node_type in sorted(defined_nodes):
        description = NODE_DESCRIPTIONS.get(node_type, "")
        if not description or description == "":
            undocumented.append(node_type)

    if undocumented:
        warnings.append(f"[WARNING] {len(undocumented)} nos sem descricao:")
        for node in undocumented[:10]:  # Mostra apenas os 10 primeiros
            warnings.append(f"  - {node}")
        if len(undocumented) > 10:
            warnings.append(f"  ... e mais {len(undocumented) - 10}")

    info.append(f"[OK] {len(defined_nodes) - len(undocumented)}/{len(defined_nodes)} nos documentados")

    return errors, warnings, info


def main():
    """Executa validação completa."""
    print("=" * 70)
    print("VALIDAÇÃO DO NODE DATABASE - LOGIC GRAPH")
    print("=" * 70)
    print()

    # Validar node_definitions
    print("[CHECK] Validando NODE_DEFINITIONS e NODE_GROUPS...")
    print("-" * 70)
    errors, warnings, info = validate_node_definitions()

    for line in info:
        print(f"  {line}")

    if warnings:
        print()
        for line in warnings:
            print(f"  {line}")

    if errors:
        print()
        for line in errors:
            print(f"  {line}")

    print()
    print("[CHECK] Validando DESCRIPTIONS...")
    print("-" * 70)
    errors2, warnings2, info2 = validate_descriptions()

    for line in info2:
        print(f"  {line}")

    if warnings2:
        print()
        for line in warnings2:
            print(f"  {line}")

    if errors2:
        print()
        for line in errors2:
            print(f"  {line}")

    print()
    print("=" * 70)

    # Resumo final
    all_errors = errors + errors2
    all_warnings = warnings + warnings2

    if not all_errors:
        if all_warnings:
            print("[OK] Validacao passou com AVISOS")
            return 1
        else:
            print("[OK] Validacao passou com SUCESSO")
            return 0
    else:
        print(f"[FAIL] Validacao FALHOU ({len(all_errors)} erro(s))")
        return 2


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
