# Alvos e ciclo de vida no Editor de Lógica

## Alvo visual do fluxo

Os blocos que alteram objetos agora exibem o alvo diretamente no cartão:

- `ALVO ATUAL`: objeto definido no cabeçalho do Logic Graph.
- `ALVO IMPLÍCITO`: instância produzida anteriormente por Criar objeto, Criar Prefab, Clonar objeto ou pelo evento Ao objeto ser criado.
- `ALVO → referência conectada`: a porta `target` recebeu uma conexão explícita de objeto.
- `NOVO ALVO`: nome que passará a acompanhar o fluxo depois de um bloco de criação.

Conexões de fluxo são linhas contínuas. Referências de objeto são linhas turquesa tracejadas. Uma conexão explícita em `target` sempre substitui o alvo implícito.

Durante o Play, os valores de depuração dos blocos mostram `Alvo atual=<Nome>`.

## Controle das instâncias criadas

Criar objeto, Criar Prefab e Clonar objeto oferecem estas propriedades:

- `Destruir após`: tempo de vida em segundos; zero desativa.
- `Máximo de instâncias`: limite de objetos vivos criados por aquele bloco; zero deixa ilimitado.
- `Distância máxima`: distância permitida a partir do ponto de criação; zero desativa.
- `Reutilizar por pool`: guarda instâncias descartadas para reutilização posterior.

Quando o limite é atingido, a saída `limit_reached` é executada e nenhum objeto é criado. A saída `next` continua sendo usada quando a criação funciona.

O bloco `Destruir depois de um tempo` permite agendar o descarte de qualquer alvo no meio do fluxo.

## Evento de criação

`Ao objeto ser criado` é disparado sempre que o próprio grafo cria ou clona uma instância. Sua saída `object` fornece uma referência explícita, e o fluxo `next` já recebe essa instância como alvo implícito.

Isso permite centralizar inicialização de velocidade, imagem, animação, som ou componentes sem repetir os mesmos blocos depois de cada criação.

## Receita recomendada

A receita `Disparar projétil seguro com pool` demonstra o fluxo completo:

1. Espaço é pressionado uma vez.
2. Um `Projectile` é criado.
3. O limite mantém no máximo 20 instâncias vivas.
4. O projétil é descartado após 3 segundos ou 1200 unidades.
5. A instância descartada volta ao pool.
6. O movimento permanente recebe automaticamente o projétil recém-criado.

Stop e reinício restauram o snapshot original da cena, portanto instâncias temporárias e o pool não permanecem no modo de edição.
