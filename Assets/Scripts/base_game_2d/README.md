# Scripts do Jogo Base 2D

- `player.py`: movimento, pulo, vida, moedas, vitória e derrota.
- `coin.py`: coletável com rotação.
- `enemy.py`: patrulha e dano.
- `goal.py`: condição de vitória.
- `moving_platform.py`: exemplo de plataforma animada por script.

Para personalizar, altere apenas os valores dentro de `CONFIG` no topo dos
scripts. O formato usa `on_start`, `on_update`, `on_trigger` e
`on_instruction`, compatíveis com o Play Mode atual.

