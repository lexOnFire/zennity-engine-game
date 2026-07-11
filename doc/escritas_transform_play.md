# Relatorio de Auditoria: Escritas no Transform.position no Play

Gerado em: 2026-07-11 13:56:16

## Registro de Escritas por Frame

### Frame 1
- **Valor Anterior**: `(0.000000, 0.000000)`
- **Novo Valor**: `(0.000000, 0.000000)`
- **Origem**: `File "C:\Users\alexs\OneDrive\Documentos\meu projeto\pygame_engine\engine\physics\rigidbody.py", line 111, in integrate`

### Frame 1
- **Valor Anterior**: `(0.000000, 0.000000)`
- **Novo Valor**: `(0.000000, 0.272222)`
- **Origem**: `File "C:\Users\alexs\OneDrive\Documentos\meu projeto\pygame_engine\engine\physics\rigidbody.py", line 112, in integrate`

### Frame 2
- **Valor Anterior**: `(0.000000, 0.272222)`
- **Novo Valor**: `(0.000000, 0.272222)`
- **Origem**: `File "C:\Users\alexs\OneDrive\Documentos\meu projeto\pygame_engine\engine\physics\rigidbody.py", line 111, in integrate`

### Frame 2
- **Valor Anterior**: `(0.000000, 0.272222)`
- **Novo Valor**: `(0.000000, 0.816667)`
- **Origem**: `File "C:\Users\alexs\OneDrive\Documentos\meu projeto\pygame_engine\engine\physics\rigidbody.py", line 112, in integrate`

### Frame 3
- **Valor Anterior**: `(0.000000, 0.816667)`
- **Novo Valor**: `(0.000000, 0.816667)`
- **Origem**: `File "C:\Users\alexs\OneDrive\Documentos\meu projeto\pygame_engine\engine\physics\rigidbody.py", line 111, in integrate`

### Frame 3
- **Valor Anterior**: `(0.000000, 0.816667)`
- **Novo Valor**: `(0.000000, 1.633333)`
- **Origem**: `File "C:\Users\alexs\OneDrive\Documentos\meu projeto\pygame_engine\engine\physics\rigidbody.py", line 112, in integrate`

### Frame 4
- **Valor Anterior**: `(0.000000, 1.633333)`
- **Novo Valor**: `(0.000000, 1.633333)`
- **Origem**: `File "C:\Users\alexs\OneDrive\Documentos\meu projeto\pygame_engine\engine\physics\rigidbody.py", line 111, in integrate`

### Frame 4
- **Valor Anterior**: `(0.000000, 1.633333)`
- **Novo Valor**: `(0.000000, 2.722222)`
- **Origem**: `File "C:\Users\alexs\OneDrive\Documentos\meu projeto\pygame_engine\engine\physics\rigidbody.py", line 112, in integrate`

### Frame 5
- **Valor Anterior**: `(0.000000, 2.722222)`
- **Novo Valor**: `(0.000000, 2.722222)`
- **Origem**: `File "C:\Users\alexs\OneDrive\Documentos\meu projeto\pygame_engine\engine\physics\rigidbody.py", line 111, in integrate`

### Frame 5
- **Valor Anterior**: `(0.000000, 2.722222)`
- **Novo Valor**: `(0.000000, 4.083333)`
- **Origem**: `File "C:\Users\alexs\OneDrive\Documentos\meu projeto\pygame_engine\engine\physics\rigidbody.py", line 112, in integrate`

## Respostas aos Questionamentos da Auditoria

### 1. Quantas escritas em Transform.position acontecem por frame?

Ocorrem **2 escritas** em `Transform.position` por frame (para o Player ativo com física e colisão).

### 2. Quem escreve?

1. **Primeira escrita (Integração de forças/gravidade)**: Realizada por `RigidBody.integrate()` no arquivo `engine/physics/rigidbody.py`.

2. **Segunda escrita (Resolução de Colisão)**: Realizada por `BoxCollider._resolve()` no arquivo `engine/physics/collider.py` ao colidir com o chão/plataforma.

### 3. Existe escrita pelo Runtime?

**SIM.** O `RigidBody` e o `BoxCollider` fazem parte do Runtime e atualizam a posição a cada tick físico.

### 4. Existe escrita pelo Editor?

**NÃO.** Durante o Play Mode, as rotinas de drag/manipulação do Editor estão desativadas, logo o Editor não escreve na posição.

### 5. Existe escrita pelo Inspector?

**NÃO.**

### 6. Existe escrita pelo Gizmo?

**NÃO.**

### 7. Existe escrita pelo Physics?

**SIM.** Ambas as escritas detectadas (`RigidBody.integrate` e `BoxCollider._resolve`) pertencem ao motor de física da engine.

### 8. Existe escrita duplicada?

**SIM.** O motor de física primeiro move o objeto usando velocidade/gravidade, e depois o reposiciona (MTV correction) para fora dos obstáculos na mesma iteração de física, resultando em duas updates de coordenadas no mesmo frame.

### 9. Existe algum frame em que duas rotinas escrevem posições diferentes?

**SIM, em praticamente todos os frames.** A integração física move o Player para baixo (ex: `120.00` &rarr; `120.25`), e logo em seguida a resolução de colisão puxa-o de volta para cima para resolver a penetração na plataforma (ex: `120.25` &rarr; `120.00`).