# Governança Arquitetural & Estabilidade de APIs — Zennity Engine

> **Versão:** 1.0.0  
> **Status:** Oficial & Ativo  
> **Escopo:** Todo o desenvolvimento e evolução da Zennity Engine a partir da Fase 5 (Engenharia de Produto).

---

## 📜 1. Princípios de Governança

A infraestrutura principal da Zennity Engine é considerada **oficial, estável e consolidada**. Toda evolução futura deve focar na **entrega de produto e ferramentas**, reaproveitando estritamente os pilares de infraestrutura existentes:

- **Engine Core** (`engine.core`)
- **Metadata Framework** (`MetadataManager`)
- **Localization Framework** (`LocalizationManager`)
- **Plugin Framework** (`PluginManager`)
- **Graph Framework** (`NodeDefinition`, `GraphCanvas`)
- **Asset Pipeline** (`AssetHandle`, `AssetDatabase`, `RuntimeAssetManager`)
- **Animation Platform & Track Framework** (`AnimationPlayerService`, `AnimationTrack`)

---

## 🔒 2. Classificação de APIs & Módulos

### 2.1 APIs Públicas Estáveis (Contrato Garantido)
Estas APIs possuem estabilidade garantida. Alterações incompatíveis (*breaking changes*) só são permitidas em versões *Major*:

- `engine.core`: `Application`, `Scene`, `GameObject`, `Component`, `Transform`, `Time`, `EventBus`, `EngineContext`, `EngineServices`, `IService`.
- `engine.metadata`: `MetadataManager`, `MetadataDefinition`, `NodeDefinition`, `PinDefinition`, `AssetTypeDefinition`, `TrackDefinition`, `PreviewDefinition`.
- `engine.assets`: `AssetHandle`, `AssetDatabase`, `RuntimeAssetManager`, `AssetImporter`, `AssetMeta`.
- `engine.animation`: `AnimationPlayerService`, `AnimationTrack`, `TransformTrack`, `SpriteTrack`, `AudioTrack`, `EventTrack`, `PropertyTrack`, `AnimationCurveEngine`.

### 2.2 APIs Internas / Privadas (`_` prefix ou submódulos de suporte)
Módulos marcados como internos podem sofrer refatoração sem aviso prévio, contanto que não afetem a API Pública:
- Implementações de adaptadores gráficos ou Pygame específicos (`engine/graphics/renderer.py`).
- Utilitários internos de parsing JSON e IO local em `editor/`.

---

## 🚫 3. Regras Estritas de Não-Duplicação (Governança)

Antes de implementar qualquer funcionalidade ou ferramenta nova (ex: *Behavior Tree*, *Dialogue Graph*, *Material Graph*, *UI Builder*):

1. **PROIBIDO:** Criar novos `Managers`, `Registries`, `EventBus` ou fontes de verdade paralelas.
2. **OBRIGATÓRIO:** Registrar todos os dados e tipos via `MetadataManager`.
3. **OBRIGATÓRIO:** Utilizar o `Graph Framework` oficial para todos os editores visuais de grafos/nós.
4. **OBRIGATÓRIO:** Utilizar `AssetHandle` (GUID imutável) para todas as referências de arquivos e recursos.
5. **OBRIGATÓRIO:** Toda nova ferramenta no Editor deve atuar como cliente puro (*Data-Driven*), consumindo serviços do `EngineServices`.

---

## 🔄 4. Política de Depreciação & Versionamento (SemVer)

### 4.1 Processo de Depreciação (`@deprecated`)
Quando uma função ou classe da API pública for descontinuada:

1. **Aviso:** Deve ser marcado com `DeprecationWarning` e anotado com o decorator `@deprecated(reason="...")`.
2. **Shim:** Deve manter um shim de compatibilidade na camada de entrada (`engine/*.py`) re-exportando o símbolo correto.
3. **Prazo:** O símbolo legado permanecerá ativo por pelo menos uma versão Minor completa antes da remoção final.

### 4.2 Versionamento Semântico
A Zennity Engine adota o **Semantic Versioning 2.0.0 (MAJOR.MINOR.PATCH)**:
- **MAJOR:** Mudanças incompatíveis de API no Engine Core (ex: `v1.0.0`).
- **MINOR:** Novas ferramentas de produto ou novos metadados sem quebrar retrocompatibilidade (ex: `v0.5.0` - Behavior Tree).
- **PATCH:** Correções de bugs e otimizações de performance sem alteração de contrato.
