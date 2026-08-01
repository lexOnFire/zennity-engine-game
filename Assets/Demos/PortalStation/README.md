# Portal Station: Reactor Run — jogo completo de todas as abas

Abra primeiro `PortalStation.zscene`. A cena reúne cenário, terminal, portal,
drone, câmera e HUD. Ao abrir o Editor de Lógica Visual, os seis documentos
abaixo são carregados automaticamente:

1. **Logic Graph** — `PortalPilot.zlogic`, `EnergyCell.zlogic` e `PortalTerminal.zlogic`: movimento, coleta, energia e condição de vitória.
2. **Behavior Tree** — `StationDrone.zbehavior`: patrulha, espera e investiga.
3. **Dialogue** — `StationGuide.zdialogue`: diálogo de acesso ao portal.
4. **Material** — `PortalGlow.zmat`: material emissivo azul do portal.
5. **Animator Graph** — `PortalAnimator.zanimator`: portal fechado e ativo.
6. **UI & HUD** — `PortalHUD.zui`: painel, título, objetivo e botão.

Selecione uma aba, clique em **Abrir** e carregue seu arquivo desta pasta.

## Interação

1. Abra `PortalStation.zscene`.
2. Pressione **Play** e mantenha a Game View ativa.
3. Use **WASD** para conduzir o piloto até as três células amarelas.
4. Cada coleta atualiza o Blackboard, a barra de energia e toca um efeito sonoro.
5. Clique em **ATIVAR PORTAL**. Antes de 3/3 o terminal recusa a ativação;
   com energia completa o núcleo gira, toca o som de partida e conclui a missão.

O painel inferior do Editor de Lógica mostra logs, timeline e profiler durante toda a sessão.
