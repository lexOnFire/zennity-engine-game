# Zennity Editor — UI Foundation

O tema oficial vive em `editor/ui/`. Novos painéis não devem declarar paletas
ou estilos completos com `setStyleSheet()`.

## Regras

- Cores, raios, alturas e espaçamentos vêm de `tokens.py`.
- O stylesheet global é gerado por `build_editor_stylesheet()`.
- Variações de botão usam a propriedade dinâmica `uiRole`:
  `primary`, `danger`, `dangerAction`, `icon`, `play`, `pause` ou `stop`.
- Widgets estruturais usam `objectName`, por exemplo
  `InspectorComponentHeader`, `InspectorComponentBody` e `HierarchyTree`.
- `setStyleSheet()` local fica reservado a conteúdo realmente dinâmico, como
  a amostra da cor selecionada pelo usuário.
- Ícones vêm do pacote SVG `editor/ui/svg/` e são acessados por
  `editor_icon()`; não misturar emojis de sistemas diferentes em controles.
- `premium_theme.PREMIUM_QSS` continua disponível somente por compatibilidade.

## Ordem de migração

1. ✅ Barra de comandos, Hierarchy, Assets e Inspector.
2. ✅ Animation Workspace, Console, Profiler e Build Report.
3. ✅ Relatórios restantes, diálogos, estados vazios e Asset Preview.
4. ✅ Pacote SVG consistente substituindo os glifos temporários da toolbar e animação.

Os painéis migrados usam nomes semânticos e o tema global também durante o
redimensionamento. Cores de status são expressas por `uiState`, sem criar uma
folha de estilo local para cada resultado.

Estados sem conteúdo usam `EmptyStateWidget`. Assim, cada painel informa o que
está vazio e qual ação fará os dados aparecerem, sem inventar um placeholder ou
uma paleta diferente.

Eventos contínuos de redimensionamento da viewport são agrupados em uma janela
curta de 24 ms. O último tamanho sempre é enviado e tamanhos repetidos são
ignorados, evitando inundar a fila entre Qt e Pygame durante o arraste.

O workspace de animação usa um splitter próprio com Biblioteca, Prévia/Timeline
e Propriedades roláveis. Ações de arquivo ficam compactas e separadas das ações
que alteram o objeto selecionado, reduzindo ambiguidades para iniciantes.

## Critério de aceitação

Uma nova tela precisa ser legível em estado normal, hover, foco, selecionado e
desabilitado sem criar uma segunda paleta ou sobrescrever o tema global.
