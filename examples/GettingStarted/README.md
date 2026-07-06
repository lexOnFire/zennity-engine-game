# GettingStarted

Projeto exemplo oficial da v0.3.0-alpha da Zennity Engine.

Ele demonstra:

* um `GameObject` chamado `Player`;
* componentes `RigidBody`, `BoxCollider` e `Script`;
* script Python com `ScriptBehaviour`;
* leitura de Input durante Play Mode;
* câmera principal e `AudioSource`;
* Tilemap básico;
* UI Runtime com Canvas, Label e Button;
* Animator com keyframes simples;
* pacote local instalado em `Packages/com.zennity.gettingstarted`.

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
O pacote de exemplo fica em `examples/GettingStarted/Packages/com.zennity.gettingstarted/package.json`.
