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
- Ícones temporários vêm de `editor.ui.icons`; não misturar emojis de sistemas
  diferentes em novos controles.
- `premium_theme.PREMIUM_QSS` continua disponível somente por compatibilidade.

## Ordem de migração

1. ✅ Barra de comandos, Hierarchy, Assets e Inspector.
2. ✅ Animation Workspace, Console, Profiler e Build Report.
3. Relatórios restantes, diálogos, estados vazios e Asset Preview.
4. Pacote SVG definitivo substituindo os glifos monocromáticos.

Os painéis migrados usam nomes semânticos e o tema global também durante o
redimensionamento. Cores de status são expressas por `uiState`, sem criar uma
folha de estilo local para cada resultado.

## Critério de aceitação

Uma nova tela precisa ser legível em estado normal, hover, foco, selecionado e
desabilitado sem criar uma segunda paleta ou sobrescrever o tema global.
