# Organização dos Logic Graphs e estabilização da Viewport

Data: 16 de julho de 2026  
Branch: `zen/fix-phase1-tests`

## Resumo

Esta etapa melhorou a organização de grafos grandes e reduziu responsabilidades
concentradas na Viewport e na janela principal. O formato `.zlogic` continua
compatível com assets antigos: os novos dados visuais ficam em `editor` e não
interferem na execução do jogo.

## Editor de Lógica Visual

- grupos persistentes, móveis e redimensionáveis;
- comentários persistentes e editáveis por duplo clique;
- minimapa clicável;
- organização automática por ordem de dependência;
- alinhamento e distribuição de blocos selecionados;
- recolhimento e redimensionamento individual dos blocos;
- histórico de até 80 estados com `Ctrl+Z`, `Ctrl+Y` e `Ctrl+Shift+Z`;
- autosave mantido, com alterações de movimento agrupadas no histórico.

## Diagnóstico antes do Play

O validador agora identifica e apresenta diretamente no canvas:

- portas inexistentes e tipos incompatíveis;
- entradas com mais de uma origem;
- blocos desconectados;
- fluxos conectados, mas inalcançáveis a partir de um evento;
- ciclos de execução que podem repetir indefinidamente.

Erros deixam blocos e conexões vermelhos; avisos usam amarelo. A mensagem
detalhada fica disponível no tooltip.

## Sistemas extraídos da Viewport

`editor/runtime/viewport_systems.py` contém serviços independentes:

- `FixedStepScheduler`: limita recuperação de frames e fornece passos fixos;
- `AudioPlaybackSystem`: possui mixer, canais, sons, play e stop;
- `AnimationPlaybackSystem`: calcula frames e eventos atravessados;
- `HudRuntimeSystem`: mantém e agrupa elementos do HUD.

O exportador e o validador incluem esse módulo no runtime autocontido.

## Integração com o ECS

`RuntimeWorldECSAdapter` é a fronteira explícita entre os dicionários leves do
Play Mode e `GameObject`/`Transform`. A conversão preserva nome, tag, estado,
posição, rotação e escala, sem fingir que componentes ainda incompatíveis são
iguais nos dois modelos.

## Janela principal

A descoberta, cache, filtro por objeto/tag e salvamento de Logic Graphs foram
movidos para `LogicAssetRepository`. Isso reduz o crescimento de
`isolated_editor_main.py` e estabelece o padrão para extrair outros
controladores gradualmente.

## Compatibilidade e validação

- grafos antigos recebem listas vazias de grupos e comentários;
- novos dados editoriais são ignorados pelo runtime;
- o pacote exportado recebe os mesmos sistemas usados no editor;
- a alteração local de assets do usuário não faz parte desta entrega;
- a execução física do gate em Windows 3.12 permanece dependente de uma máquina
  Windows ou do GitHub Actions.

