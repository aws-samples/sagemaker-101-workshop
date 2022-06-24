# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""An ipycanvas-based interactive widget for drawing PIL-compatible doodles in JupyterLab
"""

# Python Built-Ins:
from math import floor
from typing import Tuple, Union

# External Dependenices:
import numpy as np
from ipycanvas import Canvas, hold_canvas
from IPython.display import display
from ipywidgets import HTML, Button, Layout, Output, VBox
from matplotlib.colors import to_hex, to_rgb
from PIL import Image, ImageDraw


class ValidatedColor:
    """Canvas expects different color repr from PIL/image, so this class stores both"""

    hexa: str
    np_8bit: np.ndarray

    def __init__(self, color: Union[Tuple[float], np.ndarray]):
        self.set_color(color)

    def set_color(self, color: Union[Tuple[float], np.ndarray]):
        """Use this method to update all stored representations at once"""
        self.hexa = to_hex(color)
        self.np_8bit = (255 * np.array(to_rgb(color))).astype(int)


class PixelDrawCanvas:
    """JupyterLab widget to interactively draw on a canvas and export the pixel data to Python

    This widget maintains a buffer of pixel values and draws individual pixel rects to canvas (in
    batches, at least) to canvas on each mouse event... More toy/demo than an optimized design!

    Usage
    -----
    After creating the PixelDrawCanvas you can either call `.display()` to directly display it in
    the notebook, or access the `.widget` property if you want to embed the UI it in another
    ipywidgets widget.

    Draw on the canvas by clicking and dragging, or press the "Clear" button to start again.

    You can read the 0-255, 3-channel (height, width, 3) pixel data numpy array from `.data`.
    `matplotlib.pyplot.imshow(data)` should confirm that what you see in the widget matches this.

    You can also programmatically `.clear()` the drawing from Python if you like.
    """

    def __init__(
        self,
        width: int = 28,
        height: int = 28,
        color_bg: Tuple[float, float, float] = (0, 0, 0),
        color_fg: Tuple[float, float, float] = (1.0, 1.0, 1.0),
        pen_size: int = 3,
        title_html: str = "<h3>Draw a digit!</h3>",
    ):
        """Create a PixelDrawCanvas"""
        self.col_bg = ValidatedColor(color_bg)
        self.col_fg = ValidatedColor(color_fg)

        # -- Create individual widget components:
        self.canvas = Canvas(width=width, height=height, image_smoothing_enabled=False)
        # (Without explicit canvas.layout width, VBox/HBox fills full available width)
        self.canvas.layout.height = f"{max(200, min(1000, height))}px"
        self.canvas.layout.width = f"{max(200, min(1000, width))}px"
        self.canvas.image_smoothing_enabled = False
        self._clear_button = Button(
            description="Clear",
            icon="eraser",
            tooltip="Clear the drawing to a blank image",
        )
        self._console = Output(
            layout=Layout(
                max_height="140px",
                overflow_y="auto",
            )
        )
        self._title = HTML(title_html)

        # -- Initialize state:
        self.is_drawing = False
        # (Temporary data __init__ to be overridden by clear() shortly:)
        self.data = np.zeros((height, width, 3))
        self.set_pen(pen_size=pen_size)

        # -- Set up listeners:
        # Wrap widget event listener member functions so they have access to this `self` instance
        # when called and are also able to `print()` to the console output if needed.
        @self._console.capture()
        def on_mouse_down(*args, **kwargs):
            return self._on_mouse_down(*args, **kwargs)

        @self._console.capture()
        def on_mouse_move(*args, **kwargs):
            return self._on_mouse_move(*args, **kwargs)

        @self._console.capture()
        def on_mouse_out(*args, **kwargs):
            return self._on_mouse_out(*args, **kwargs)

        @self._console.capture()
        def on_mouse_up(*args, **kwargs):
            return self._on_mouse_up(*args, **kwargs)

        @self._console.capture()
        def on_clear_click(*args, **kwargs):
            return self.clear()

        self.canvas.on_mouse_down(on_mouse_down)
        self.canvas.on_mouse_move(on_mouse_move)
        self.canvas.on_mouse_out(on_mouse_out)
        self.canvas.on_mouse_up(on_mouse_up)
        self._clear_button.on_click(on_clear_click)

        # Set up composite view with the different widget components:
        self.widget = VBox(
            [self._title, self._clear_button, self.canvas, self._console],
            width=f"{width}px",
        )

        # Finally initialize to clear state ready to use:
        with self._console:
            self.clear()

    def clear(self):
        """Clear the drawing"""
        height = self.canvas.height
        width = self.canvas.width
        with hold_canvas(self.canvas):
            self.canvas.clear()
            self.canvas.fill_style = self.col_bg.hexa
            self.canvas.fill_rect(0, 0, width, height)
            self.canvas.fill_style = self.col_fg.hexa
        self.data = np.tile(self.col_bg.np_8bit, (height, width, 1))
        print("Cleared drawing")

    def draw_from_buffer(self):
        """Draw the contents of the .data buffer to the canvas

        This reproduces steps from clear() instead of calling it internally, to avoid flicker. Only
        pixels of the current col_fg in the buffer will be drawn (doesn't support changing col_fg
        dynamically or drawing multiple colors).
        """
        height = self.canvas.height
        width = self.canvas.width
        fg_mask = (self.data == np.expand_dims(self.col_fg.np_8bit, (0, 1))).all(-1)
        with hold_canvas(self.canvas):
            self.canvas.clear()
            self.canvas.fill_style = self.col_bg.hexa
            self.canvas.fill_rect(0, 0, width, height)
            self.canvas.fill_style = self.col_fg.hexa
            fg_coords = np.argwhere(fg_mask)  # N entries of (x, y) pairs
            self.canvas.fill_rects(fg_coords[:, 1], fg_coords[:, 0], 1, 1)

    def display(self):
        """Display the widget (in a Jupyter/Lab notebook)"""
        display(self.widget)

    def _on_mouse_down(self, x, y):
        self.is_drawing = True
        self.paint(x, y)

    def _on_mouse_move(self, x, y):
        if self.is_drawing:
            self.paint(x, y)

    def _on_mouse_out(self, x, y):
        """Re-draw from data buffer on each mouse-out in case anything weird happened"""
        self.is_drawing = False
        self.draw_from_buffer()

    def _on_mouse_up(self, x, y):
        self.is_drawing = False

    def set_pen(self, pen_size: int = 15) -> np.ndarray:
        """Set up the pen/brush (define pen_mask matrix)

        We pre-calculate and store a boolean `.pen_mask` matrix for the requested brush size (and
        assumed circular shape). If you wanted, you could set other whacky shapes by replacing your
        own boolean matrix (True where the pen marks, False where it doesn't).

        Returns
        -------
        pen_mask :
            The same boolean 2D matrix this function saves to `self.pen_mask`.
        """
        # No sense re-inventing the "pixellated circle" wheel, so use PIL:
        mask_img = Image.new("1", (pen_size, pen_size))
        draw = ImageDraw.Draw(mask_img)
        draw.ellipse((0, 0, pen_size - 1, pen_size - 1), fill="white")
        self.pen_mask = np.array(mask_img)  # (pen_size, pen_size) boolean array
        return self.pen_mask

    def paint(self, x, y):
        """Mark the given location with the current pen"""
        # Truncate the current pen mask if required (if location is close to edge of image):
        x_floor = floor(x)
        y_floor = floor(y)

        pen_mask = self.pen_mask
        x_maskstart = floor(x - (pen_mask.shape[1] / 2))
        if x_maskstart < 0:
            pen_mask = pen_mask[:, -x_maskstart:]  # Truncate left of pen
            x_maskstart = 0
        x_pixelsafter = self.data.shape[1] - (x_maskstart + pen_mask.shape[1])
        if x_pixelsafter < 0:
            pen_mask = pen_mask[:, :x_pixelsafter]  # Truncate right of pen
            x_pixelsafter = 0

        y_maskstart = floor(y - (pen_mask.shape[0] / 2))
        if y_maskstart < 0:
            pen_mask = pen_mask[-y_maskstart:, :]  # Truncate top of pen
            y_maskstart = 0
        y_pixelsafter = self.data.shape[0] - (y_maskstart + pen_mask.shape[0])
        if y_pixelsafter < 0:
            pen_mask = pen_mask[:y_pixelsafter, :]  # Truncate bottom of pen
            y_pixelsafter = 0

        x_maskend = x_maskstart + pen_mask.shape[1]
        y_maskend = y_maskstart + pen_mask.shape[0]

        # Check which pixels will be actually updated to avoid drawing unnecessary canvas rects:
        new_fg_pixels_offset = np.argwhere(
            pen_mask
            & (
                self.data[
                    y_maskstart:(y_maskstart + pen_mask.shape[0]),
                    x_maskstart:(x_maskstart + pen_mask.shape[1]),
                    :,
                ]
                != np.expand_dims(self.col_fg.np_8bit, (0, 1))
            ).all(-1)
        )

        # Update the data buffer:
        full_mask = np.zeros_like(self.data)
        full_mask[y_maskstart:y_maskend, x_maskstart:x_maskend, :] = np.expand_dims(pen_mask, -1)
        self.data = np.where(full_mask, self.col_fg.np_8bit, self.data)

        # Draw the canvas updates:
        with hold_canvas(self.canvas):
            self.canvas.fill_style = self.col_fg.hexa
            self.canvas.fill_rects(
                new_fg_pixels_offset[:, 1] + x_maskstart,
                new_fg_pixels_offset[:, 0] + y_maskstart,
                1,
                1,
            )
            self.canvas.fill_rect(x_floor, y_floor, 1, 1)
