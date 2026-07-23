# Plugins na Zennity Engine

A Zennity Engine suporta um ecossistema de extensões ricas e plugins por meio de pacotes locais (v1.2).

## Estrutura de um Pacote (Package)

Todo pacote deve residir num diretório e possuir um arquivo `package.json` na sua raiz.

### Exemplo de `package.json`

```json
{
    "name": "meu_plugin_incrivel",
    "version": "1.0.0",
    "description": "Um plugin de exemplo.",
    "author": "Zennity Dev",
    "engine_version_min": "1.2.0",
    "engine_version_max": "1.9.9",
    "dependencies": {
        "outro_pacote": ">=1.0.0"
    },
    "capabilities": [
        "file_system_read"
    ],
    "components": [],
    "inspector_plugins": [
        "meu_plugin_incrivel.inspector.MeuCustomInspector"
    ],
    "editor_extensions": [
        "meu_plugin_incrivel.extension.MinhaExtensaoDeEditor"
    ]
}
```

> **Nota de Segurança:** O nome (`name`) do pacote só pode conter caracteres alfanuméricos, hífens e underlines (`_`), evitando vulnerabilidades de path traversal no motor.

## Editor Extensions (Ciclo de Vida)

As extensões de editor têm acesso global à interface do motor e são regidas por um ciclo de vida robusto.

```python
class MinhaExtensaoDeEditor:
    name = "minha_extensao"

    def load(self, editor):
        # Carrega recursos ou estado inicial sem afetar a UI.
        pass

    def enable(self, editor):
        # Ativa hooks na UI, atalhos, etc.
        pass

    def disable(self, editor):
        # Desativa hooks (ex: antes de um hot reload).
        pass

    def unload(self, editor):
        # Remove a extensão da memória.
        pass
```

Se `enable` falhar, a engine fará o rollback seguro chamando `disable` seguido de `unload`.

## Inspector Plugins

Plugins de inspetor permitem customizar como um componente específico é exibido no painel de propriedades.

```python
class MeuCustomInspector:
    component_type = "Transform" # Nome do componente suportado

    def supports(self, component):
        return type(component).__name__ == self.component_type
        
    def build_ui(self, inspector, component):
        # Constrói UI do Qt dinamicamente
        pass
```

Os plugins determinam precedência. Se houver mais de um plugin registrando o mesmo `component_type`, uma mensagem será gravada no DiagnosticCenter e o último registrado será ativado.
