# Portal Station — demo de todas as abas

Abra primeiro `PortalStation.zscene`. A cena reúne cenário, terminal, portal,
drone, câmera e HUD. Ao abrir o Editor de Lógica Visual, os seis documentos
abaixo são carregados automaticamente:

1. **Logic Graph** — `PortalTerminal.zlogic`: inicializa o objetivo no HUD.
2. **Behavior Tree** — `StationDrone.zbehavior`: patrulha, espera e investiga.
3. **Dialogue** — `StationGuide.zdialogue`: diálogo de acesso ao portal.
4. **Material** — `PortalGlow.zmat`: material emissivo azul do portal.
5. **Animator Graph** — `PortalAnimator.zanimator`: portal fechado e ativo.
6. **UI & HUD** — `PortalHUD.zui`: painel, título, objetivo e botão.

Selecione uma aba, clique em **Abrir** e carregue seu arquivo desta pasta.

## Interação

1. Abra `PortalStation.zscene`.
2. Pressione **Play** e mantenha a Game View ativa.
3. Clique em **ATIVAR PORTAL**.
4. O botão emite `activate_portal`; o Logic Graph encontra o objeto com a tag
   `Portal`, gira o núcleo em 45 graus, atualiza o HUD e registra a ativação.
