# Auditoria: Causa Raiz do Snap (Cordenadas vs Rasterizacao)

Gerado em: 2026-07-11 14:23:28

## Resultados do Experimento A (Floats sem Antialiasing)

O Grid/Sprite move-se com deltas fracionários contínuos:
- Frame 1: Coordenada X usada = `400.3000`
- Frame 2: Coordenada X usada = `400.6000`
- Frame 3: Coordenada X usada = `400.9000`
- Frame 4: Coordenada X usada = `401.2000`
- Frame 5: Coordenada X usada = `401.5000`
**Resultado:** O movimento continuou perfeitamente suave (`Contínuo = True`).

## Resultados do Experimento B (Quantização Manual com Antialiasing)

As coordenadas foram truncadas manualmente para inteiros:
- Frame 1: Coordenada X usada = `400`
- Frame 2: Coordenada X usada = `400`
- Frame 3: Coordenada X usada = `400`
- Frame 4: Coordenada X usada = `401`
- Frame 5: Coordenada X usada = `401`
**Resultado:** O snap reapareceu imediatamente (`Contínuo = False`).

## Conclusão Final

**Conclusão:** A causa exclusiva do snap é a perda das coordenadas fracionárias (coordenadas float).