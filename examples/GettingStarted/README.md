# GettingStarted

Projeto exemplo oficial da Beta 0.1 da Zennity Engine.

Ele demonstra:

* um `GameObject` chamado `Player`;
* componentes `RigidBody`, `BoxCollider` e `Script`;
* script Python com `ScriptBehaviour`;
* leitura de Input durante Play Mode.

## Como testar

1. Abra o editor:

```bash
python -m editor.phase1_main
```

2. Use `File > Open Scene`.
3. Abra `examples/GettingStarted/Assets/Scenes/GettingStarted.zscene`.
4. Pressione Play.
5. Segure `Space` para mover o Player no Runtime World.
6. Clique com o mouse na Viewport para registrar input de mouse no script.
7. Pressione Stop para voltar ao Editor World original.

O script fica em `examples/GettingStarted/Assets/Scripts/player_controller.py`.
