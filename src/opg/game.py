import pygame
import asyncio
import logging

from . import assets, util
from .event_manager import EventManager


class MainMenu:

    _DEFAULT_DISPLAY = 0

    _DEFAULT_WINDOW_OPTIONS = {
        'flags': pygame.SRCALPHA | pygame.DOUBLEBUF | pygame.RESIZABLE | pygame.SHOWN,
        'display': _DEFAULT_DISPLAY,
        'vsync': 1}

    def __init__(self, event_manager):
        self._LOGGER = logging.getLogger(
            f"{self.__class__.__qualname__}#{id(self)}")

        self._event_manager = event_manager
        self._loop = asyncio.get_running_loop()
        self._screen = None
        self._running = False

        def compute_min_size():
            d_size = pygame.display.get_desktop_sizes()[self._DEFAULT_DISPLAY]
            target_size_ratio = (5, 4)
            size_unit = min(i / j / 2 for i, j in zip(d_size, target_size_ratio))
            return tuple(int(size_unit * i) for i in target_size_ratio)

        self._MIN_SIZE = compute_min_size()

    async def draw(self):
        background_image = pygame.image.load(assets.get_asset_path('orb.pond.png'))
        background_image = pygame.transform.scale(
            background_image, self._screen.get_size())
        self._LOGGER.info(
            'Drawing background image of size %s',
            background_image.get_size())
        self._LOGGER.info('Screen size is %s', self._screen.get_size())
        self._screen.blit(background_image, (0, 0))
        pygame.display.flip()

    async def watch_for_quit(self, tg):
        _sub = self._event_manager.get_subscription(pygame.QUIT)
        async with _sub as sub:
            await sub.get()
        util.terminate_task_group(tg)

    async def watch_for_resize(self, tg):
        _sub = self._event_manager.get_subscription(pygame.VIDEORESIZE)
        async with _sub as sub:
            while True:
                event = await sub.get()
                self._screen = await self._event_manager.call(
                    lambda: pygame.display.set_mode(
                        size=max(event.size, self._MIN_SIZE), **self._DEFAULT_WINDOW_OPTIONS
                    )
                )
                self._LOGGER.info('Window resized to %s', self._screen.get_size())
                await self.draw()

    async def watch_for_button(self, tg):
        _sub = self._event_manager.get_subscription(pygame.MOUSEBUTTONDOWN)
        async with _sub as sub:
            while True:
                event = await sub.get()
                self._LOGGER.info('Mouse button clicked')

    async def run(self):
        assert self._loop is asyncio.get_running_loop()

        self._running = True

        async def init_screen() -> pygame.Surface:
            pygame.display.set_caption('ORB.POND')
            pygame.display.set_icon(
                pygame.image.load(assets.get_asset_path('icon.png'))
            )
            return pygame.display.set_mode(
                size=self._MIN_SIZE,
                **self._DEFAULT_WINDOW_OPTIONS
            )
        self._screen = await self._event_manager.call(init_screen)

        try:
            await self.draw()
            async with asyncio.TaskGroup() as tg:
                tg.create_task(self.watch_for_quit(tg))
                tg.create_task(self.watch_for_resize(tg))
                tg.create_task(self.watch_for_button(tg))
        except* util.TerminateTaskGroup as e:
            pass
