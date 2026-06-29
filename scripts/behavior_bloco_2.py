import pygame# Script de Comportamento para o objeto: Bloco_2
# Voce pode editar este arquivo para programar o comportamento do objeto em tempo de execucao.

def start(obj):
    # Executado uma unica vez ao iniciar a simulacao (PLAY)
    print(f"Iniciando comportamento de {obj.name}!")
    obj.start_pos = obj.transform.position.copy()
    obj.script_time = 0.0
def update(obj, dt):
    # Executado a cada frame durante a simulacao (PLAY)
    obj.script_time = getattr(obj, "script_time", 0.0) + dt
    
    # Exemplo: Rotacao suave no eixo Y
    velocidade = 0.5
    teclas = pygame.key.get_pressed()

    if teclas[pygame.K_LEFT]:
        obj.transform.position[0] -= velocidade
    if teclas[pygame.K_RIGHT]:
        obj.transform.position[0] +=velocidade