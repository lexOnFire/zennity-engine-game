# Medição de memória da v1

O gate usa `engine.performance.memory_probe.measure_allocations`, com aquecimento,
coleta de lixo e snapshots de `tracemalloc`. O resultado separa memória líquida
retida, blocos retidos e pico transitório.

Contratos iniciais:

- 500 ciclos Play/Stop: até 2 MiB retidos e pico de até 8 MiB;
- pool por Prefab: máximo rígido de 128 objetos;
- teardown da Viewport: caches, scripts, áudio e superfícies vazios;
- medições devem ocorrer após aquecimento e nunca usar RSS absoluto do runner.

Esses limites são gates de regressão, não uma promessa de consumo total do
processo. RSS, memória nativa do Qt/SDL e GPU serão registrados separadamente
nos benchmarks de release, pois não são atribuídos corretamente por
`tracemalloc`.
