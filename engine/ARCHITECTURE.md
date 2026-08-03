# Zennity Engine Architecture

A Zennity Engine é construída sobre um **Service Locator Pattern (IoC Container)**.

## EngineServices
Nenhum sistema da engine (Localization, Plugins, Audio) instancia a si mesmo ou opera como um Singleton global isolado.
Toda a infraestrutura é acessada puramente pelo `EngineServices`.

```python
from engine.core.services import EngineServices
from engine.localization import LocalizationManager

# Pegando o serviço instanciado e gerenciado pelo Core
loc_manager = EngineServices.get(LocalizationManager)
```

## Ciclo de Vida (IService)
Quando você criar um novo subsistema (ex: `AssetManager`), faça-o herdar de `IService` e defina `initialize()` e `shutdown()`.

## Metadata Unificada
Todo e qualquer metadado (Nodes, Pins, Components) está obrigatoriamente centralizado em `engine/core/metadata/`.
Isso garante que o Front-End de UI possa inspecionar a engine sem importar pacotes pesados de runtime.
