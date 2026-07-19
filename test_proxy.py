import pygame, unittest.mock; pygame.init(); class SurfaceProxy:
    def __init__(self, s):
        self.s=s; self.blit_mock=unittest.mock.MagicMock(wraps=s.blit)
    def blit(self, *a, **k): return self.blit_mock(*a, **k)
    def __getattr__(self, n): return getattr(self.s, n)
s = SurfaceProxy(pygame.Surface((10,10)))
s.blit(pygame.Surface((5,5)), (0,0))
s.blit_mock.assert_called()
print('OK')
