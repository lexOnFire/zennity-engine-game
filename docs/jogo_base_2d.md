# Jogo Base 2D

Cena pronta: `Assets/Scenes/JogoBase2D.zscene`

## Como jogar

1. Abra a cena pelo menu **Arquivo → Open Scene**.
2. Entre na aba **Game**.
3. Clique em **Play**.
4. Use **A/D** ou as setas para andar, **Espaço** para pular e **R** para reiniciar.
5. Colete as cinco moedas e alcance o portal roxo.

Vida, moedas, controles, vitória e derrota aparecem no HUD da Game View. O
Console continua registrando os principais eventos.

## Sistemas incluídos

- Movimento e pulo com física.
- Plataformas estáticas e uma plataforma móvel.
- Cinco moedas coletáveis.
- Inimigo com patrulha e dano.
- Três pontos de vida.
- Portal com condição de vitória.
- HUD de vida, moedas, controles e resultado.
- Reinício instantâneo com R.
- Queda, derrota e reinício pelo Play Mode.
- Câmera, colliders, triggers e organização por tags.

## Onde aprender e modificar

Os scripts estão em `Assets/Scripts/base_game_2d/`. Cada arquivo cuida de uma
única responsabilidade e possui uma seção `CONFIG` com os valores mais úteis.

- Para aumentar a velocidade: `player.py` → `speed`.
- Para mudar o pulo: `player.py` → `jump_force`.
- Para exigir mais moedas: altere `coins_to_win` e adicione moedas na cena.
- Para mudar a patrulha: `enemy.py` → `distance` e `speed`.
- Para mover outra plataforma: anexe `moving_platform.py` ao objeto.
