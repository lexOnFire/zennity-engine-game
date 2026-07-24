# Prefabs seguros e exportação da Lógica Visual

## Criar Prefab

O bloco **Criar Prefab** permite escolher diretamente um arquivo `.zprefab` pelo seletor de assets. A instância criada vira o alvo implícito dos próximos blocos e também é disponibilizada pela saída `object`.

### Overrides de Transform

- **Sobrescrever posição** usa X e Y do bloco. Desmarcado, preserva a posição gravada no Prefab.
- **Posição relativa** soma X e Y à posição do objeto que executa o grafo.
- **Sobrescrever rotação** aplica a rotação indicada no bloco.
- **Sobrescrever tamanho** aplica largura e altura. Ambos precisam ser maiores que zero.

Os overrides são independentes: é possível trocar somente a posição e preservar rotação e tamanho, por exemplo.

### Componentes globais protegidos

Por segurança, Prefabs criados por grafos não copiam automaticamente:

- câmera;
- fonte de áudio;
- Logic Graphs anexados ao próprio Prefab.

Cada item possui uma opção explícita no bloco. Isso evita criar câmeras principais, músicas em autoplay ou controladores duplicados ao instanciar projéteis, inimigos e efeitos. Collider, Rigidbody, sprite, animação e demais propriedades continuam preservados.

## Play e Stop

As instâncias são independentes e existem somente no Play Mode. Ao pressionar Stop, o snapshot original da cena é restaurado; Prefabs criados, movimentos permanentes, áudio temporário e lógica anexada em runtime não permanecem no modo de edição.

## Exportação

O exportador copia e confere os assets usados pelo runtime:

- `.zlogic` e `.zblackboard`;
- `.zanim` e `.zanimator`;
- `.zprefab`;
- imagens;
- áudio.

O `package_manifest.json` agora contém `asset_roots` e `asset_counts`, facilitando a conferência do build. O exportador compara tamanho e presença dos arquivos relevantes na origem e no destino. A validação de projeto também abre todos os Prefabs, verifica o JSON e valida suas referências internas.
