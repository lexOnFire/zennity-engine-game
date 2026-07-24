# Migração dos entrypoints do editor

## Contrato canônico

A partir da preparação da v1.0, existe um único entrypoint público:

    python -m editor.phase1_main
    zennity-editor

Esse bootstrap inicia o editor oficial com Viewport isolada. O módulo
`editor.isolated_editor_main` permanece como detalhe interno de implementação,
não como API pública.

## Compatibilidade

Os launchers `editor.main`, `editor.premium_main`, `editor.studio_main`,
`editor.mvp_main` e `editor.fixed_studio_main` agora emitem `FutureWarning` e
redirecionam para o entrypoint canônico. Eles não mantêm mais bootstraps Qt,
temas ou lifecycles paralelos.

O argumento `--legacy-embedded` do entrypoint canônico permanece disponível
somente para diagnóstico e migração durante a série 1.x. Não deve ser usado em
atalhos, documentação ou automações novas.

## Cronograma

- v1.0: redirects compatíveis e aviso de depreciação;
- v1.x: correções críticas apenas no caminho legado embutido;
- v2.0: remoção dos redirects e do modo `--legacy-embedded`.

## Métrica arquitetural

Antes desta migração havia seis launchers públicos com cinco bootstraps Qt
independentes. Depois dela há um bootstrap público e cinco redirects sem
inicialização própria. Um teste de arquitetura impede a reintrodução de
`QApplication` nesses launchers.
