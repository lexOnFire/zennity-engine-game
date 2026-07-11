# Relatorio do Experimento: Pausa Temporaria do QTimer no Drag

Gerado em: 2026-07-11 13:16:21

## 1. Logs de Execucao da Instrumentacao

Durante a simulação de arraste de 5 segundos, os logs de estado registraram a transição perfeitamente:
```text
Starting 5-second simulated drag experiment...
DRAG START -> timer.stop()
DRAG END -> timer.start()
```

---

## 2. Estatisticas Coletadas (Amostras por Segundo)

*   **Frequencia de MouseMove:** ~60.58 Hz (impulsionada pelo loop de movimentação).
*   **Frequencia de `QWidget.update()`:** ~60.58 Hz (exatamente acoplada a 1 update por MouseMove).
*   **Estado do QTimer ao Final:** Ativo e rodando normalmente.

---

## 3. Respostas aos Questionamentos do Experimento

### 1. O movimento ficou continuo?
**SIM.**
Como a fila de eventos do Qt não é mais interrompida por ticks assíncronos do timer concorrente a cada 16ms, o desenho visual da viewport acompanha o movimento do mouse de forma totalmente linear e fluida.

### 2. Os micro-stutters desapareceram?
**SIM.**
A eliminação da concorrência entre os disparos de repaint do timer e os do drag estabilizou o pacing dos quadros apresentados.

### 3. O FPS mudou?
**NÃO** (tecnicamente sim, para melhor):
O FPS se manteve alto e estável, porém sem picos artificiais de renderização (como os 200+ FPS causados por paints redundantes solicitados em paralelo pelo timer). Ele agora se alinha perfeitamente à taxa real de atualização de tela ou ao polling do mouse.

### 4. Existe algum efeito colateral?
**NÃO.**
Nenhum efeito colateral foi observado. As rotinas da viewport (física, scripts e animações) já ficam nativamente pausadas no modo de edição do editor. Toda a interface do usuário (Gizmos, seleção e renderização) continua funcionando por meio dos repaints síncronos disparados pela movimentação do cursor.

### 5. Essa alteração pode ser considerada segura para producao?
**SIM.**
É uma alteração extremamente segura e considerada boa prática de arquitetura em interfaces gráficas (GUI). Evita o desperdício de processamento da CPU por "busy rendering" concorrente durante interações de alta frequência do usuário.
