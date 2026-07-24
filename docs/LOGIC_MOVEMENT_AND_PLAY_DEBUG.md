# Movimento permanente e depuração no Play Mode

Esta etapa completa o controle de movimentos permanentes da Lógica Visual e torna os objetos criados durante o Play visíveis no editor.

## Movimentos identificáveis

O bloco **Iniciar movimento permanente** agora recebe um nome em `Movimento` e devolve uma referência pela saída `movement`. O nome pode ser usado diretamente nos demais blocos; a referência pode ser conectada quando o fluxo permitir.

Um mesmo objeto pode manter vários movimentos ao mesmo tempo. Por exemplo, `Corrida` pode controlar o eixo X enquanto `Subida` controla o eixo Y. Alterar ou parar `Corrida` não interfere em `Subida`.

Blocos disponíveis:

- **Iniciar movimento permanente**: define velocidade, espaço, aceleração e desaceleração.
- **Alterar movimento permanente**: troca a velocidade-alvo de um movimento ativo.
- **Pausar movimento permanente**: reduz a velocidade até zero usando a desaceleração.
- **Continuar movimento permanente**: volta à velocidade-alvo usando a aceleração.
- **Parar movimento permanente**: remove imediatamente ou desacelera antes de remover.
- **Consultar movimento permanente**: informa X, Y, velocidade, pausa e atividade.

Deixar o nome vazio em **Parar movimento permanente** mantém a compatibilidade anterior e para todos os movimentos permanentes do objeto.

## Espaço global e local

- `global`: X e Y seguem os eixos da Scene View.
- `local`: X e Y acompanham a rotação atual do objeto. Um movimento para a direita gira junto com ele.

## Aceleração e desaceleração

Valor zero aplica a velocidade imediatamente e preserva o comportamento antigo. Valores positivos aproximam a velocidade atual da velocidade-alvo em unidades por segundo ao quadrado.

A desaceleração é usada ao pausar ou ao solicitar uma parada suave. Se for zero, a mudança ocorre imediatamente.

## Depuração durante o Play

Enquanto o jogo executa, a Hierarchy mostra o grupo **Runtime** com as instâncias criadas pela lógica. É possível selecionar uma delas sem interromper o Play.

O Inspector exibe um cartão somente de leitura com:

- posição atual;
- origem da criação;
- objeto criador e grafo criador;
- idade e tempo de vida;
- movimentos ativos, seus nomes, espaço, velocidades e estado de pausa.

Os dados são atualizados de forma limitada pelo processo da viewport para não transformar a depuração em uma carga por frame. Ao pressionar Stop, o grupo Runtime e os dados temporários são removidos junto com a restauração da cena.

## Receita pronta

A receita **Controlar movimento permanente** demonstra aceleração, alteração de velocidade, pausa, retomada e parada suave usando um movimento chamado `Corrida`.
