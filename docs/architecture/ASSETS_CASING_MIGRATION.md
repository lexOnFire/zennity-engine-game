# Consolidação do diretório Assets

O repositório da engine usa exclusivamente a raiz canônica `Assets/`.
A antiga árvore `assets/scripts` foi removida e seus nove arquivos exclusivos
foram movidos para `Assets/Scripts`. O `animator.py` legado não foi copiado
porque já existia uma versão canônica com o mesmo caminho lógico; a resolução
anterior já priorizava essa versão e, portanto, o arquivo legado estava
sombreado.

Projetos externos antigos continuam compatíveis: `AssetPathResolver` aceita
qualquer casing da raiz, encontra componentes do caminho sem diferenciar
maiúsculas/minúsculas e serializa referências novamente com prefixo
`Assets/`.

Métrica: duas raízes físicas no repositório foram reduzidas para uma, eliminando
a diferença de comportamento entre Windows e Linux. Um gate de arquitetura
impede que a raiz minúscula volte a ser versionada.
