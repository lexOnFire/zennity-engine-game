# Zennity Editor - Alvo visual e funcional

Este documento define o alvo de interface para o editor da Zennity Engine.

A referência aprovada é uma interface estilo engine profissional, próxima de Unity/Unreal/Godot, com foco em criação real de jogos 2D e 3D.

## Direção visual aprovada

O editor deve parecer uma engine de jogos, não apenas uma aplicação PySide6 genérica.

Elementos principais:

- Barra superior com menus reais: Arquivo, Editar, Janela, Criar, Ferramentas, Build, Executar e Ajuda.
- Toolbar com ações rápidas: novo, abrir, salvar, ferramentas de seleção/move/rotate/scale e botões Play/Pause/Stop.
- Viewport central grande, com abas `Viewport` e `Cena`.
- Hierarchy à esquerda com árvore da cena.
- Assets/Recursos à esquerda ou abaixo da Hierarchy.
- Inspector à direita para editar objeto selecionado.
- Console, saída e depurador na parte inferior.
- Asset Preview e Profiler na parte inferior.
- Status bar com FPS, memória, contagem de objetos e estado do projeto.

## Layout alvo

```text
+--------------------------------------------------------------------------------+
| Menu: Arquivo Editar Janela Criar Ferramentas Build Executar Ajuda             |
+--------------------------------------------------------------------------------+
| Toolbar: New Open Save | Select Move Rotate Scale | Play Pause Stop | Settings |
+-----------------------+--------------------------------------+-----------------+
| Hierarchy             | Viewport / Cena                       | Inspector       |
| - MainScene           |                                      | Transform       |
| - Environment         |                                      | Renderer        |
| - Player              |                                      | Collider        |
| - Enemies             |                                      | Scripts         |
+-----------------------+--------------------------------------+-----------------+
| Assets/Recursos       | Console / Saida / Depurador           | Profiler        |
| Preview               | Logs e comandos                       | FPS/Mem/CPU     |
+--------------------------------------------------------------------------------+
| Status: Projeto salvo | FPS | Memoria | Objetos | Estado                       |
+--------------------------------------------------------------------------------+
```

## Fluxo mínimo de criação

O usuário deve conseguir fazer isto sem procurar recursos escondidos:

1. Criar nova cena.
2. Criar objeto pelo painel `Criar` ou menu `Criar`.
3. Ver o objeto na Viewport.
4. Ver o objeto na Hierarchy.
5. Selecionar o objeto.
6. Editar Transform no Inspector.
7. Apertar Play.
8. Parar e voltar ao estado de edição.

## MVP 2D obrigatório

Antes de evoluir o 3D, o modo 2D precisa estar confiável.

Presets obrigatórios:

- Empty Object
- Sprite 2D
- Player 2D
- Platform 2D
- Enemy 2D
- Trigger 2D
- Camera 2D

Templates obrigatórios:

- Plataforma 2D
- Top-down 2D

Critérios:

- Criar objetos atualiza Viewport, Hierarchy e Inspector.
- Inspector edita posição, rotação e escala.
- Play não deve quebrar a cena.
- Stop deve restaurar a cena editável.

## MVP 3D experimental

O 3D deve existir, mas marcado como experimental até estabilizar.

Presets mínimos:

- Cube 3D
- Plane 3D
- Camera 3D
- Light 3D

Critérios:

- Alternar para 3D não pode causar crash.
- Criar Cube/Plane deve aparecer na Viewport e Hierarchy.
- Inspector deve editar Transform.
- Recursos avançados de 3D ficam para etapa posterior.

## Próximas tarefas sugeridas

1. Reorganizar `MainWindow` para esse layout alvo.
2. Criar dock/painel `Criar` fixo e visível.
3. Melhorar `HierarchyDock` para mostrar árvore com ícones e visibilidade.
4. Melhorar `AssetBrowserDock` para parecer navegador de projeto.
5. Melhorar `InspectorDock` com seções: Transform, Renderer, Collider, Script.
6. Consolidar `ViewportWidget` para modo 2D estável.
7. Tratar o modo 3D como experimental.
8. Adicionar testes para criação de objetos no editor.
