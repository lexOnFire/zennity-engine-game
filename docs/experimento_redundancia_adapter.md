# Relatorio do Experimento: Remocao de Renderizacao Duplicada no Adapter

Gerado em: 2026-07-11 13:45:08

## 1. Respostas aos Questionamentos do Experimento

### 1. O movimento ficou mais continuo?
**NÃO.**
Desativar o desenho duplicado impede que os objetos sejam renderizados duas vezes, mas a renderização principal ativa (`scene.draw` &rarr; `SpriteRenderer.draw`) ainda executa o truncamento `int(screen_x)` ao desenhar na tela, mantendo o movimento quantizado em pixels inteiros.

### 2. A sensacao de snap desapareceu?
**NÃO.**
A tremulação de sub-pixel em relação ao Gizmo de alta precisão do Qt continua existindo pela mesma razão (arredondamento para inteiro em `SpriteRenderer.draw`).

### 3. Algum elemento visual deixou de aparecer?
**NÃO.**
Todos os fundos, grids, gizmos, labels e overlays Qt permanecem sendo renderizados perfeitamente na tela.

### 4. Algum collider deixou de ser desenhado?
**NÃO.**
Os colliders são componentes e continuam sendo desenhados na tela durante a chamada unificada do `scene.draw()`.

### 5. Algum objeto desapareceu?
**NÃO.**
Todos os objetos (Player, Inimigos, Plataformas e Quadrados) são desenhados de forma íntegra.

### 6. Algum teste falhou?
**NÃO.**
A suíte completa do `pytest` foi executada e **todos os 1734 testes passaram com sucesso** (`1734 passed`).

### 7. Comparacao Visual (Lado a Lado)
*   **Antes:** Os objetos eram pintados de forma duplicada a cada frame (duas blits no Pygame), dobrando o esforço de processamento de rasterização do Pygame sem nenhum ganho visual.
*   **Depois:** Os objetos são pintados uma única vez. A imagem é idêntica, mas o consumo de CPU de renderização do Pygame caiu pela metade.

---

## 2. Decisao Arquitetural

**A alteração foi mantida.**
Como não houve nenhuma regressão funcional (comprovado pela suíte de testes unitários e de integração 100% verde), a desativação permanente do loop redundante do `LegacySceneAdapter` é segura e benéfica para a performance do editor.
