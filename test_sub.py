import pygame
pygame.init()
class M(pygame.Surface):
    def blit(self, *a, **k):
        print('blit called')
        return super().blit(*a, **k)
m = M((10,10))
m.blit(pygame.Surface((5,5)), (0,0))

