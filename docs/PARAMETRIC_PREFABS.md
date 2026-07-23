# Prefabs parametrizáveis e variantes

## Propriedades expostas

Um Prefab pode declarar em `exposed_properties` somente os valores que o usuário deve configurar ao criá-lo. Cada definição possui:

- `name`: identificador estável usado pelos grafos;
- `label`: nome amigável mostrado no editor;
- `type`: `number`, `bool`, `text`, `color`, `image`, `animation` ou `audio`;
- `default`: valor padrão;
- `target`: propriedade do objeto que receberá o valor, aceitando caminhos como `gameplay.damage`, `visual.texture` e `transform.scale.0`;
- `asset_kind`: opcional; abre o seletor correto para imagem, animação ou áudio;
- `semantic`: opcional; `lifetime`, `max_distance` e `max_instances` integram o valor ao ciclo de vida da instância.

Exemplo:

```json
{
  "format_version": 2,
  "prefab_name": "Projectile",
  "exposed_properties": [
    {"name": "speed", "label": "Velocidade", "type": "number", "default": 500, "target": "gameplay.speed"},
    {"name": "damage", "label": "Dano", "type": "number", "default": 1, "target": "gameplay.damage"},
    {"name": "lifetime", "label": "Tempo de vida", "type": "number", "default": 2, "target": "gameplay.lifetime", "semantic": "lifetime"},
    {"name": "image", "label": "Imagem", "type": "image", "default": "Assets/Textures/bullet.png", "target": "texture", "asset_kind": "image"}
  ],
  "object": {"name": "Projectile", "w": 24, "h": 8, "gameplay": {}}
}
```

Ao escolher esse arquivo no bloco **Criar Prefab**, o editor sincroniza automaticamente os valores e as portas `speed`, `damage`, `lifetime` e `image`. Propriedades internas não aparecem no bloco. Um duplo clique em imagem, animação ou som abre o seletor de assets.

O bloco **Ler parâmetro do Prefab** permite que a lógica da nova instância consuma os valores recebidos. Assim, um grafo de projétil pode multiplicar `speed` por `direction_x`, aplicar `damage` na colisão e tocar o `sound` configurado.

## Variantes com herança

Uma variante referencia um Prefab base e grava somente diferenças:

```json
{
  "format_version": 2,
  "prefab_name": "Missile",
  "base_prefab": "Assets/Prefabs/Projectile.zprefab",
  "property_overrides": {"speed": 280, "damage": 4, "lifetime": 5},
  "object_overrides": {"name": "Missile"}
}
```

Alterações futuras no Prefab base são herdadas automaticamente. Overrides da variante têm precedência. Referências fora do projeto, propriedades inexistentes e ciclos de herança são bloqueados pelo validador.

No painel **Adicionar Prefabs**, clique com o botão direito em um Prefab e use **Criar variante...**. Variantes aparecem com o indicador `↳`.

## Instâncias e overrides persistentes

Uma instância adicionada à cena registra:

- `prefab_guid`: identidade estável do asset;
- `prefab_source`: caminho portátil dentro de `Assets/`;
- `prefab_overrides`: somente valores alterados ou removidos em relação ao
  Prefab resolvido.

Os overrides usam caminhos JSON Pointer, portanto propriedades aninhadas e
nomes contendo `/` ou `~` continuam seguros. Antes de salvar a cena, o editor
recalcula o patch da instância. Ao atualizar uma instância, novos valores do
Prefab são incorporados e as diferenças locais permanecem. A reversão descarta
as diferenças, mas preserva o ID, o nome único da cena e o vínculo da instância.

O Inspector mostra a origem, o GUID e a lista de caminhos modificados.

## Compatibilidade e exportação

- Prefabs antigos continuam carregando normalmente.
- Prefabs criados pelos dois editores passam a usar `format_version: 2` e expõem escala, cor, imagem, Tag e Layer por padrão.
- Parâmetros resolvidos ficam em `prefab_parameters`, visíveis para depuração no runtime.
- O build inclui o resolvedor de herança e todos os `.zprefab` e assets referenciados.
- O pool preserva o isolamento: cada reutilização recebe novamente os parâmetros atuais.

## Demo

`Nebula Defense` usa `NebulaBolt.zprefab` como base. `NebulaMissile.zprefab` e `NebulaEnemyAttack.zprefab` são variantes. Espaço cria a bala comum e M cria o míssil, sem duplicar a lógica de movimento e colisão.
