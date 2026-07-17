# Demo do Animator Controller

Abra `Assets/Scenes/AnimatorControllerDemo.zscene` no editor.

- A/D ou setas: mover.
- Espaço: pular.
- S ou seta para baixo: atacar.
- Abra `PlayerDemo.zanimator` na aba Animação para acompanhar o estado ativo.
- O ataque habilita `AttackHitbox` somente entre os eventos `ataque_inicio` e `ataque_fim`.
- Stop restaura Player, alvo, hitbox, HUD e parâmetros.

Os clips repetem a textura existente para que a demo valide controller, timeline,
eventos, scripts, física, áudio e exportação sem exigir outro sprite sheet.
