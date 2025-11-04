import pygame as py
from constants import UI_ROW_HEIGHT, UI_BAR_COLOR, COLOR_BLACK


class UIBar:
    """Manages a multi-row UI bar for displaying game information."""

    def __init__(self, width, font, num_rows=3):
        """Initialize UI bar with specified width and number of rows.

        Args:
            width: Width of the bar in pixels
            font: pygame.font.Font instance for rendering text
            num_rows: Number of rows in the bar (default: 3)
        """
        self.width = width
        self.font = font
        self.num_rows = num_rows
        self.height = UI_ROW_HEIGHT * num_rows
        self.row_contents = [None] * num_rows  # Store (text, alignment) tuples

    def set_row_content(self, row_index, text, alignment='left'):
        """Set content for a specific row.

        Args:
            row_index: Row number (0-based, must be < num_rows)
            text: Text to display
            alignment: 'left', 'center', or 'right'

        Raises:
            ValueError: If row_index is out of range
        """
        if row_index < 0 or row_index >= self.num_rows:
            raise ValueError(f"row_index must be 0-{self.num_rows-1}, got {row_index}")

        self.row_contents[row_index] = (text, alignment)

    def render(self):
        """Render the UI bar and return as a pygame surface.

        Returns:
            pygame.Surface with the rendered UI bar
        """
        surface = py.Surface((self.width, self.height))
        surface.fill(UI_BAR_COLOR)

        for row_index, content in enumerate(self.row_contents):
            if content is None:
                continue  # Skip empty rows

            text, alignment = content
            text_surface = self.font.render(text, True, COLOR_BLACK)

            # Calculate vertical position (center text in row)
            y_pos = row_index * UI_ROW_HEIGHT + (UI_ROW_HEIGHT - text_surface.get_height()) // 2

            # Calculate horizontal position based on alignment
            if alignment == 'left':
                x_pos = 10  # 10px left padding
            elif alignment == 'center':
                x_pos = (self.width - text_surface.get_width()) // 2
            elif alignment == 'right':
                x_pos = self.width - text_surface.get_width() - 10  # 10px right padding
            else:
                x_pos = 10  # Default to left

            surface.blit(text_surface, (x_pos, y_pos))

        return surface
