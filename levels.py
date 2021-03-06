import simplegui

from typing import List, TYPE_CHECKING, Tuple
from constants import GRID_SIZE, BLOCK_SIZE
from geom import Vector
from level_items import LevelItem

from constants import LEVEL_BACKGROUND_IMAGE, WINDOW_SIZE, LEVEL_BACKGROUND_STRETCH_X, \
    LEVEL_USE_BACKGROUND
from util import load_image
from math import floor

# Work around cyclic imports.
if TYPE_CHECKING:
    from world import World

__all__ = ['Level']


# FIXME: rendering background image has a game breaking affect on the fps and cpu usage;
# FIXME: until we can find a fix this'll need to remain commented out


class Level(object):
    """
    A game level.
    """

    def __init__(self, world: 'World', level: int, start_pos: Tuple[int, int],
                 scroll: Vector = Vector(0.05, 0)):
        self.level = level
        self.start_pos = Vector(
            start_pos[0] * BLOCK_SIZE,
            (GRID_SIZE[1] - start_pos[1] - 1) * BLOCK_SIZE
        )

        self.offset = Vector(0, 0)
        self.scroll = scroll

        self.items: List[LevelItem] = []
        self.finished = False

        self.counter = 0
        self.world = world
        self.world.source.last_active_level = self

        self.window_size = world.window.get_size()

        # Just some initialisation stuff here; less to compute later.
        self.background_offset = self.window_size[0] / 2
        self.background_image = load_image(LEVEL_BACKGROUND_IMAGE)
        self.bg_size = (self.background_image.get_width(), self.background_image.get_height())
        self.bg_center = (self.bg_size[0] / 2, self.bg_size[1] / 2)

    def get_score(self):
        return self.world.player.score

    def add_item(self, item: LevelItem):
        """
        Adds the item to the level.
        """
        self.items.append(item)

    def finish(self):
        """
        Finishes the level.
        """
        self.finished = True

    def render(self, world: 'World', canvas: simplegui.Canvas):
        """
        Called on every game tick to render the level.
        """

        # Draw background
        if LEVEL_USE_BACKGROUND:
            center_dest1 = (
                -(self.offset.x % self.window_size[0]) + self.background_offset,
                self.window_size[1] / 2
            )
            center_dest2 = (
                center_dest1[0] + self.window_size[0],
                center_dest1[1]
            )
            canvas.draw_image(self.background_image, self.bg_center, self.bg_size,
                              center_dest1, self.window_size)
            canvas.draw_image(self.background_image, self.bg_center, self.bg_size,
                              center_dest2, self.window_size)

        self.counter += 1

        if self.counter % BLOCK_SIZE == 0:
            self.counter = 0
            world.player.score += 1

        dpi_factor = world.window.hidpi_factor

        font = world.text_font
        font_color = world.text_font_color
        score_text = "SCORE // {0:d}".format(world.player.score)
        lives_text = "LIVES // {0:d}".format(world.player.lives)

        canvas.draw_text(score_text, (10 * dpi_factor, 20 * dpi_factor), font.get_size(),
                         str(font_color),
                         font.get_face())
        canvas.draw_text(lives_text, (10 * dpi_factor, 40 * dpi_factor), font.get_size(),
                         str(font_color),
                         font.get_face())

        # Render items
        for item in self.items:
            bounds = item.get_bounds()
            if bounds.max.x > 0 and bounds.min.x < WINDOW_SIZE[0]:
                item.render(canvas)

        # Render player
        world.player.render(canvas)

        # Add the level scroll, mutating the current offset.
        self.offset.add(self.scroll * BLOCK_SIZE)

        # Load next level.
        if self.finished:
            levels = world.levels

            next_level = self.level + 1
            if len(levels) >= next_level:
                target_level = levels[next_level - 1]
                world.player.pos = target_level.start_pos
                world.level = target_level
            else:
                world.level = None
