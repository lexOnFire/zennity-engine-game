# Demo Behavior Controller

O asset `Assets/Behaviors/EnemyDemo.zbehavior` demonstra três estados:

- `Patrol`: patrulha lenta.
- `Chase`: persegue o objeto com Tag `Player`.
- `Attack`: executa um ataque curto e retorna para a perseguição.

Cada script usa apenas `on_enter`, `on_update` e `on_exit`. O controller guarda
os parâmetros e decide quando trocar de estado. Na próxima etapa, esse asset
será conectado ao componente do Inspector e ao Play Mode.
