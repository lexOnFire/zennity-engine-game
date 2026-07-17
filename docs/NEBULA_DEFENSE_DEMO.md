# Nebula Defense — demo completa com Logic Graphs

`Nebula Defense` é um shooter 2D jogável criado para demonstrar os modelos atuais da Zennity: Logic Graphs, Blackboard, Prefabs seguros, pooling, movimento persistente, colisões por Tag, HUD, áudio e exportação. A jogabilidade não usa scripts Python.

## Como abrir e jogar

1. Inicie o editor com `python -m editor.phase1_main` na raiz do projeto.
2. Abra `Assets/Scenes/NebulaDefense.zscene`.
3. Pressione **Play**.
4. Use **WASD** para mover, **Espaço** para disparar, **M** para lançar a variante de míssil e **R** para reiniciar.
5. Destrua dez drones para vencer. O jogador começa com três vidas.

## Organização

| Recurso | Arquivo | Responsabilidade |
|---|---|---|
| Cena | `Assets/Scenes/NebulaDefense.zscene` | câmera, fundo, jogador, gerenciador, spawner, limites e música |
| Jogador | `Assets/Logic/NebulaDefense/NebulaPlayer.zlogic` | movimento, disparo, dano, vidas e derrota |
| Spawner | `Assets/Logic/NebulaDefense/NebulaSpawner.zlogic` | criação periódica de inimigos com posição aleatória |
| Inimigo | `Assets/Logic/NebulaDefense/NebulaEnemy.zlogic` | avanço, filtro de colisão, pontuação e destruição |
| Projétil | `Assets/Logic/NebulaDefense/NebulaProjectile.zlogic` | filtro de colisão e destruição segura |
| Gerenciador | `Assets/Logic/NebulaDefense/NebulaGameManager.zlogic` | placar, vidas, vitória, derrota e reinício |
| Fundo | `Assets/Logic/NebulaDefense/NebulaBackground.zlogic` | rolagem contínua da textura |
| Blackboard | `Assets/Logic/ProjectBlackboard.zblackboard` | variáveis compartilhadas `score` e `lives` |
| Prefabs | `Assets/Prefabs/NebulaDefense/` | disparo parametrizável, variantes de míssil/ataque inimigo e drone reutilizável |

## Decisões de segurança

- Projéteis usam pool, vida útil de 2,2 segundos, distância máxima e limite de 24 instâncias.
- Inimigos usam pool, vida útil de 10 segundos, distância máxima e limite de 9 instâncias.
- Prefabs não copiam câmera, áudio ou lógica do criador.
- Colisões verificam Tags antes de aplicar dano, pontuação ou destruição.
- O Stop do editor restaura a cena e encerra os objetos criados no Play Mode.

## Regerar a demo

Execute `python tools/generate_nebula_defense_demo.py`. O gerador é determinístico e recria a cena, os seis grafos, os dois Prefabs e o Blackboard da demo.

## Exportar

Com a cena aberta, use o comando de publicação/exportação do editor. O pacote inclui automaticamente `.zlogic`, `.zblackboard`, `.zprefab`, imagens e áudio. A suíte de testes também valida uma exportação completa da demo.
