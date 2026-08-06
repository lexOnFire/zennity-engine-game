"""Importador CSV para DialogueManager - converte CSV em .zdialogue."""

from __future__ import annotations
import csv
import json
from pathlib import Path
from typing import Any, Dict, List
import uuid


class CSVDialogueImporter:
    """Converte arquivo CSV em formato .zdialogue compatível."""

    def __init__(self):
        self.nodes: Dict[str, Any] = {}
        self.edges: List[Dict[str, Any]] = []
        self.node_id_map: Dict[str, str] = {}  # text_key → node_id

    @staticmethod
    def csv_to_dict(csv_path: str | Path) -> List[Dict[str, str]]:
        """Lê CSV e retorna lista de dicts."""
        rows = []
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    rows.append(row)
        except Exception as e:
            print(f"Erro ao ler CSV: {e}")
            return []
        return rows

    def import_from_csv(self, csv_path: str | Path, output_path: str | Path | None = None) -> str:
        """
        Importa CSV e gera .zdialogue JSON.

        CSV esperado:
        speaker,text,next_node,condition
        Merchant,Olá!,choice_1,
        Merchant,Qual você quer?,option_a,has_quest=true
        """
        rows = self.csv_to_dict(csv_path)
        if not rows:
            return "{}"

        # Processa linhas
        for row_idx, row in enumerate(rows):
            speaker = row.get("speaker", "").strip()
            text = row.get("text", "").strip()
            next_node = row.get("next_node", "").strip()
            condition = row.get("condition", "").strip()

            if not text:
                continue

            # Cria node_id único
            node_id = f"node_{row_idx:03d}"
            self.node_id_map[text] = node_id

            # Determina tipo de node
            node_type = "dialogue.speech"  # padrão

            # Cria node
            node = {
                "id": node_id,
                "type": node_type,
                "inputs": {
                    "speaker": speaker,
                    "text": text
                }
            }
            self.nodes[node_id] = node

        # Cria edges
        for row_idx, row in enumerate(rows):
            text = row.get("text", "").strip()
            next_node = row.get("next_node", "").strip()

            if not text or not next_node:
                continue

            source_id = self.node_id_map.get(text)
            target_id = self.node_id_map.get(next_node) or f"node_{next_node}"

            if source_id and target_id:
                edge = {
                    "source_node": source_id,
                    "source_port": "out",
                    "target_node": target_id,
                    "target_port": "in"
                }
                self.edges.append(edge)

        # Cria estrutura final
        dialogue_dict = {
            "format": "zennity.generic_graph",
            "category": "Dialogue",
            "metadata": {
                "name": Path(csv_path).stem,
                "description": "Imported from CSV",
                "created_from": str(csv_path)
            },
            "nodes": list(self.nodes.values()),
            "edges": self.edges
        }

        # Salva ou retorna JSON
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(dialogue_dict, f, indent=2, ensure_ascii=False)
            return str(output_path)

        return json.dumps(dialogue_dict, indent=2, ensure_ascii=False)

    @staticmethod
    def create_example_csv(output_path: str | Path) -> None:
        """Cria arquivo CSV de exemplo."""
        example_csv = """speaker,text,next_node,condition
Merchant,Olá! Bem-vindo à minha loja.,choices,
Player,O que você vende?,products,
Merchant,Temos várias poções e itens.,products,
Player,Qual é o preço?,price,
Merchant,Preços justos para aventureiros.,end,
Player,Adeus!,end,
"""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(example_csv)


# Exemplos de uso
if __name__ == "__main__":
    # Criar arquivo CSV de exemplo
    importer = CSVDialogueImporter()
    importer.create_example_csv("dialogue_example.csv")

    # Converter CSV para .zdialogue
    importer.import_from_csv(
        "dialogue_example.csv",
        "dialogue_example.zdialogue"
    )

    print("CSV convertido para .zdialogue com sucesso!")
