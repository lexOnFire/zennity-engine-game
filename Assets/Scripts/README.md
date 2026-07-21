# assets/scripts

Pasta de **scripts de jogo** da Zennity Engine.

Cada arquivo aqui é um `Component` pronto para ser anexado a um `GameObject`.

## Regras do formato

1. Herda de `Component` (ou subclasse).
2. Chama `super().__init__()` no `__init__`.
3. Implementa os hooks necessários: `start`, `update`, `draw`, `destroy`.
4. Implementa `serialize()` / `deserialize()` para suportar save/load.
5. Registra-se no `ComponentRegistry` com `@ComponentRegistry.component`.

## Modelos disponíveis

| Arquivo | Descrição |
|---|---|
| `player_controller.py` | Movimento WASD + pulo com Rigidbody |
| `enemy_ai.py` | IA básica de perseguição ao player |
| `health.py` | Sistema de vida, dano e morte |
| `collectible.py` | Item coletável com detecção por overlap |
| `camera_follow.py` | Câmera suave que segue um alvo |
| `timer_component.py` | Timer reutilizável com callback |
| `animator.py` | Troca de sprites por estado (idle/run/jump) |
| `projectile.py` | Projétil com velocidade, lifetime e dano |
