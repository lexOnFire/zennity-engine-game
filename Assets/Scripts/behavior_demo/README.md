# Demo Behavior Controller

Abra `Assets/Scenes/BehaviorControllerDemo.zscene` e pressione Play.

O asset `Assets/Behaviors/EnemyDemo.zbehavior` demonstra três estados:

- `Patrol`: patrulha lenta.
- `Chase`: persegue o objeto com Tag `Player`.
- `Attack`: executa um ataque curto e retorna para a perseguição.

Cada script usa apenas `on_enter`, `on_update` e `on_exit`. O controller guarda
os parâmetros e decide quando trocar de estado. O HUD mostra o estado ativo e
a distância do Player, enquanto o Console registra cada transição.

Em scripts comuns, use `game.behavior.state`, `set_bool`, `set_float`,
`trigger` ou `play` para conversar com o controller do próprio objeto.
