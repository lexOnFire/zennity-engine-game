# Custom Rules for Zennity Engine


Antes de iniciar qualquer tarefa:

1. Execute:

git branch
git status
git rev-parse --abbrev-ref HEAD

2. Confirme que está na branch informada pela Issue.

3. Se a branch não existir:

NÃO continue.

Solicite orientação.

Nunca escolha outra branch por conta própria.


## Root Cause Policy

É proibido corrigir um bug baseado apenas em leitura do código.

Toda correção deve ser baseada em:

- traceback;
- logs;
- execução do teste;
- reprodução do problema.

Hipóteses devem ser claramente identificadas como hipóteses e nunca utilizadas para modificar o código sem confirmação.

Implementa
↓
Executa testes
↓
Gera relatório
↓
Aguarda revisão
↓
Você aprova
↓
git commit
↓
git push

Ao final de cada tarefa:

- Execute os testes afetados.
- Gere um relatório:
  - arquivos modificados;
  - motivo das alterações;
  - possíveis impactos;
  - riscos.
- Aguarde aprovação para realizar commit e push.

## Source of Truth

O estado oficial do projeto é o repositório LOCAL.

Nunca assuma que o GitHub está sincronizado.

Antes de qualquer análise:

- utilize os arquivos locais;
- somente utilize o GitHub como backup ou histórico;
- caso exista divergência, considere o projeto local como a versão oficial.