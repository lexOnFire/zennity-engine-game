# Criação independente e entrada de uma única vez

## Criar objeto

O bloco **Criar objeto** agora possui duas opções:

- **Copiar objeto original**: cria uma cópia profunda do objeto conectado em
  `source`; sem conexão, usa o próprio objeto dono do grafo.
- **Copiar Logic Graphs também**: vem desativada para impedir que um spawner
  copiado execute o mesmo grafo e crie cópias recursivamente.

Visual, transform, collider, rigidbody, áudio, animação, UI, comportamento e
propriedades públicas são copiados. Listas e dicionários não são compartilhados:
alterar a cópia não modifica o original. A saída `object` permite continuar o
fluxo manipulando especificamente o novo objeto.

Desmarcar **Copiar objeto original** mantém o modo antigo, que cria uma forma
simples usando tamanho, cor, textura e tag configurados no bloco.

## Entrada de teclado

Existem três comportamentos diferentes:

- **Ao apertar tecla (uma vez)**: evento que dispara somente na transição de
  solta para pressionada.
- **Tecla apertada agora?**: condição de uma única vez para fluxos que já usam
  `A cada frame`.
- **Tecla está segurada?**: permanece verdadeira enquanto a tecla estiver
  pressionada.

## Movimento permanente

**Iniciar movimento permanente** registra as velocidades X/Y e continua
movendo o alvo a cada atualização, mesmo após a tecla ser solta.
**Parar movimento permanente** remove esse movimento do alvo.

A receita **Apertar D uma vez e continuar andando** cria o fluxo:

`Ao apertar D (uma vez) → Iniciar movimento permanente (X = 120)`

O estado é descartado ao parar ou reiniciar o Play Mode e nunca altera a cena
salva no modo de edição.

