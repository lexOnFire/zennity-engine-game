# Arquitetura do Engine Core

O **Engine Core** da Zennity é a espinha dorsal de todo o motor. Ele fornece o contêiner de Injeção de Dependências (IoC), ciclos de vida rígidos, ordenação matemática de boot e escopos dinâmicos. Nenhum módulo do motor opera isoladamente do Core.

## 1. EngineContext

O `EngineContext` é o receptáculo global da execução. Ao invés de dependermos de dezenas de `Singletons` (que dificultam testes e vazam memória entre recarregamentos), toda a árvore de execução reside em uma única instância do Contexto.

O contexto abriga:
- `self.services` -> A instância Mestre do `EngineServices` (Service Locator / IoC Container).
- `self.diagnostics` -> Dicionário de telemetria contendo:
  - Tempos de carregamento de Providers e Services.
  - O Profile Ativo.
  - `health_reports`: Relatório detalhado se um serviço falhou.
- Diretórios padrões (Ex: `locales_dir`).

## 2. Boot Profiles

Você não precisa carregar ferramentas de UI (Editor) quando o jogador rodar o game final.
Os **BootProfiles** (`EDITOR`, `RUNTIME`, `HEADLESS`, `TEST`, `CLI`, `ALL`) controlam a descoberta.
- Quando chamamos `EngineBootstrap.boot(profile=BootProfile.RUNTIME)`, apenas `EngineProviders` que possuam `BootProfile.RUNTIME` ou `ALL` na sua propriedade `profiles` serão instanciados.

## 3. O Ciclo de Vida do Bootstrap (Ordem Topológica)

Quando você chama `EngineBootstrap.boot()`, ocorre a seguinte dança matemática:

1. **Descoberta:** O engine varre todos os submódulos procurando subclasses de `EngineProvider`.
2. **Filtragem:** Descarta provedores que não pertencem ao `BootProfile` requisitado.
3. **Ordenação Topológica:** Lê a propriedade `depends_on = [ProviderType]` de cada Provider, montando um Grafo Direcionado Acíclico (DAG). Se houver um ciclo (A exige B, B exige A), a engine trava imediatamente com um `RuntimeError`.
4. **Registro:** Invoca `register_services(context)` na ordem topológica correta. O provider instancia os serviços no contêiner.
5. **Boot:** Invoca `boot(context)` em todos os provedores.
6. **Inicialização de Serviços:** Invoca `context.services.initialize_all()`. Aqui, a **mesma ordenação topológica** ocorre, mas a nível de Serviços.

## 4. Criando Serviços (IService) e Dependências

Para expor uma funcionalidade, você deve implementar um `IService`.

```python
from engine.core.services import IService
from engine.core.lifecycle import ServiceScope, ServiceState

class AudioService(IService):
    def __init__(self):
        super().__init__()
        # Se dependermos do sistema de Arquivos, forçamos a engine a criá-lo primeiro!
        self.depends_on = [FileSystemService]
        self.scope = ServiceScope.ENGINE # Vive para sempre
        
    def initialize(self):
        # Alocar recursos de áudio...
        pass
        
    def validate(self):
        # Verifica se a placa de som está conectada. 
        # Retornar False abortará silenciosamente o serviço sem derrubar a engine inteira.
        return True
```

### 4.1 Escopos (Scopes) e Hierarquia

O `EngineServices` pode ser hierárquico.
Se você carregar uma Cena, você cria um `EngineServices(parent=master_services)`.
Todos os serviços registrados no filho com `ServiceScope.SCENE` poderão ler serviços globais (através da resolução fallback para o `parent`), mas, ao descartar o contêiner filho, a memória da cena evaporará sem tocar na raiz da Engine.

## 5. Observabilidade (Grafos Mermaid)

Para visualizar as dependências complexas dos seus serviços:
```python
mermaid_str = context.services.generate_dependency_graph_mermaid()
print(mermaid_str)
```
Isso produz um código MermaidJS válido contendo nós de sucesso em verde/cinza e serviços falhos demarcados em vermelho.

---
**Status da API:** ESTÁVEL (V1.0)
Nenhuma alteração estrutural nas assinaturas destas classes é permitida sem discussão arquitetural.
