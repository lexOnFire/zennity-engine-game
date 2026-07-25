# Zennity Engine — Governança de Arquitetura & Congelamento de API Pública

## 🏛️ Diretrizes de Estabilidade e Governança

1. **Congelamento da API Pública:**
   - Todos os serviços do `EngineServices` (`MetadataManager`, `DiagnosticsService`, `SceneStreamingService`, `ResourceManagerCache`, `JobScheduler`, `ExtensionProvider`, `GraphValidationService`) têm suas assinaturas congeladas para garantir compatibilidade com plugins de terceiros.

2. **Política de Depreciação:**
   - Módulos ou funções marcados como legados devem emitir `DeprecationWarning` de forma não bloqueante antes da remoção definitiva em versões futuras.

3. **Arquitetura Baseada em Providers:**
   - Todo novo subsistema deve ser registrado via `EngineProvider` e autodescoberto via `pkgutil.iter_modules()` em `EngineBootstrap`.

4. **Infraestrutura Unificada de Pipeline:**
   - Todos os fluxos de transformação (`Asset Pipeline`, `Build Pipeline`, `Graph Compiler`, `Animation Import`, `Extension Loading`) devem herdar de `PipelineStage` e ser executados por `PipelineEngine`.
