# Estabilização do Runtime e da Lógica Visual

Data: 16 de julho de 2026  
Branch: `zen/fix-phase1-tests`

## Resumo geral

Esta etapa consolidou a base necessária para continuar criando jogos pela
Lógica Visual sem voltar a espalhar regras de runtime pela interface, pela
Viewport e pelo exportador. A criação e o ciclo de vida de objetos agora passam
por um Runtime World compartilhado, a física usa passo fixo, os comandos entre
Qt e Pygame são identificados e coalescidos, os grafos ganharam operações de
objetos e controle de fluxo, e o exportador leva a mesma implementação para o
jogo independente.

O comportamento do editor continua compatível com cenas e componentes antigos.
O runtime histórico de scripts Python permanece no núcleo para leitura de
projetos legados, mas o editor isolado usa os Logic Graphs como caminho de
gameplay recomendado.

## 1. Runtime World único

Foi criado `engine/runtime/runtime_world.py`. A classe `RuntimeWorld` é a fonte
única da Viewport isolada para:

- criar objetos com nomes e IDs únicos;
- clonar objetos sem compartilhar dicionários de componentes;
- instanciar Prefabs;
- adicionar e remover componentes em Play Mode;
- destruir objetos sem alterar o Editor World;
- reciclar instâncias de Prefab por um pool limitado a 128 itens por asset;
- expor contadores de objetos criados, destruídos e reutilizados.

O carregador aceita os dois formatos de Prefab já presentes no projeto:

1. o formato canônico de `engine.prefabs`, com `transform`, `visual` e
   `components`;
2. o formato salvo pelo editor isolado, com o objeto dentro da chave `object`.

`sprite_path` e `texture` são aceitos para manter a compatibilidade visual.

## 2. API de gameplay da Viewport

`PlayScriptAPI` passou a compartilhar a mesma instância de `RuntimeWorld` entre
o objeto atual, objetos encontrados, clones e objetos criados. Foram adicionadas
as operações:

- `create_prefab(path, x, y)`;
- `clone_object(obj, name)`;
- `add_component(type, properties)`;
- `remove_component(type)`;
- destruição delegada ao Runtime World.

Ao parar o Play, a cena original ainda é restaurada por cópia. Objetos criados
durante a execução não vazam para o modo de edição.

Prefabs criados durante o Play são hidratados no frame seguinte: seus Logic
Graphs, Animator Controller e Audio Source com início automático entram no
ciclo de runtime. Definições duplicadas e trechos inalcançáveis do antigo ciclo
de scripts foram removidos da Viewport, deixando uma única implementação de
start, stop, câmera, colisão e transformação da vista.

## 3. Novos blocos da Lógica Visual

Foram integrados ao formato, editor, prévia de código, runtime e validação:

- Criar Prefab;
- Clonar objeto;
- Adicionar componente;
- Remover componente;
- Executar uma vez;
- Intervalo / Cooldown;
- Reiniciar cena.

Também foi adicionada a receita **Criar Prefab ao apertar Espaço**. O seletor de
assets reconhece `.zprefab` e o validador do projeto verifica referências usadas
por Prefab, sprite, som e animação.

As conexões de saída agora carregam `order` e são executadas por ordem estável.
Isso torna previsível o fan-out de um único bloco **A cada frame** para várias
ações, sem criar eventos duplicados.

## 4. Física e ciclo de execução

A física da Viewport passou a usar passo fixo de `1/60 s`. O acumulador aceita
no máximo cinco passos atrasados por frame, evitando uma sequência ilimitada de
atualizações depois de uma pausa do sistema operacional. Movimentos controlados
por Logic Graph continuam prevalecendo no eixo correspondente.

Objetos inativos deixam de participar da integração e da lista de colisores.
O encerramento envia primeiro o comando `shutdown`, aguarda a saída normal do
processo Pygame e só usa terminação forçada como fallback.

## 5. Comunicação Qt ↔ Pygame

Foi criado `editor/runtime/viewport_command_bus.py`. O barramento:

- gera uma sequência crescente para cada comando enviado;
- copia o payload antes de enviá-lo;
- elimina apenas estados pequenos e idênticos consecutivos, como seleção,
  tamanho da Viewport, ferramenta e input;
- nunca elimina snapshots ou mutações da cena;
- fornece contadores de comandos enviados e coalescidos.

Essa redução é deliberadamente conservadora: não muda a ordem das mutações e
não altera o resultado visual.

## 6. Persistência e recuperação

O salvamento de cenas escreve primeiro em `.zscene.tmp` e depois substitui o
arquivo de destino. Quando já existe uma cena, a versão anterior é copiada para
`.zscene.bak`. O mesmo procedimento foi aplicado ao salvamento feito pela
interface isolada.

Arquivos temporários e backups locais não entram no Git.

## 7. Exportação e validação externa

O exportador agora inclui `runtime_world.py` no pacote autocontido. O launcher
exportado carrega a cena antes de abrir a Viewport e aceita:

```bash
python main.py --validate-only
```

Esse comando valida o carregamento em outro processo e encerra sem abrir
Pygame. O validador também analisa todos os `.zlogic` em `Assets/Logic`, detecta
JSON inválido, eventos duplicados, conexões quebradas e assets ausentes.

## 8. CI, compatibilidade e higiene do repositório

Os três workflows sobrepostos foram consolidados em
`.github/workflows/python-tests.yml`:

- Ruff para erros críticos de Python;
- pytest no Linux com Python 3.10, 3.11 e 3.12;
- bibliotecas de sistema necessárias ao Qt headless;
- gate Windows com Python 3.12 para exportação, Play Mode, lógica e runtime.

A árvore duplicada `assets/scripts` foi removida. `Assets` é a raiz canônica,
mas o exportador ainda reconhece caminhos minúsculos de projetos antigos. O
gitlink órfão `zennity-engine-game`, que não tinha `.gitmodules` nem conteúdo
utilizável, também foi removido.

Essas exclusões podem ser recuperadas pelo histórico do Git.

## 9. Cobertura de regressão

Foram adicionados testes para:

- criação, clone, componentes, destruição, formatos de Prefab e pool;
- coalescência segura e sequência do barramento de comandos;
- novos blocos e validações da Lógica Visual;
- referências inválidas em `.zlogic`;
- exportação e execução `--validate-only` fora do editor;
- backup e substituição atômica de cenas;
- contratos do seletor de componentes sem reintroduzir scripts na interface.

A regressão headless disponível localmente passou com **1.747 testes**. Os testes de Qt
que exigem `libEGL.so.1` ficam cobertos pela matriz Linux do GitHub Actions,
onde a dependência é instalada pelo workflow. A validação final no Windows 3.12
é executada pelo gate específico após a publicação.

## 10. Acoplamentos que permanecem

Ainda existem pontos que devem ser migrados gradualmente, sem reescrita brusca:

- `editor/isolated_viewport.py` ainda reúne loop, áudio, animação, física e
  desenho no mesmo processo;
- `editor/isolated_editor_main.py` ainda centraliza muitos fluxos da interface;
- o modelo leve da Viewport usa dicionários, enquanto o runtime ECS oficial usa
  `GameObject` e `Component`;
- o sistema de scripts Python continua no núcleo para compatibilidade;
- o contato físico básico da Viewport ainda não é o mesmo `PhysicsWorld` usado
  pelo runtime oficial.

## Próximos candidatos à migração

1. Extrair o passo físico da Viewport para um serviço testável sem Pygame.
2. Criar um adaptador explícito entre `RuntimeWorld` e o ECS oficial.
3. Separar áudio, animação e HUD em sistemas de execução independentes.
4. Dividir `isolated_editor_main.py` em controladores de cena, Inspector, assets
   e Play Mode.
5. Adicionar histórico gráfico às métricas de IPC e do Runtime World já exibidas
   no Profiler.
6. Executar um teste de jogo completo empacotado em uma máquina Windows real.

## Conclusão

A engine agora possui uma base mais previsível para jogos feitos por blocos:
um evento pode alimentar várias ações ordenadas, Prefabs podem ser instanciados
e reciclados em runtime, componentes podem ser alterados visualmente, e o mesmo
código acompanha o projeto exportado. As alterações desta etapa priorizam
estabilidade e organização; não removem a compatibilidade necessária para abrir
conteúdo legado.
