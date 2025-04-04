# pico_project/graphics.py - Basic Graphics Drawing Functions

import ustruct
import font # Import the font definitions

# Pre-pack common colors if needed, or do it dynamically
# COLOR_BLACK_BYTES = ustruct.pack(">H", 0x0000)
# COLOR_WHITE_BYTES = ustruct.pack(">H", 0xFFFF)

def draw_char(display, char, x_pixel, y_pixel, fg_color_rgb565, bg_color_rgb565):
    """
    Draws a single 8x8 character on the display.

    Args:
        display: The initialized Display object (from ili9488.py).
        char: The character to draw (e.g., 'A').
        x_pixel: The top-left x-coordinate (in pixels) for the character.
        y_pixel: The top-left y-coordinate (in pixels) for the character.
        fg_color_rgb565: Foreground color in RGB565 format (e.g., 0xFFFF for white).
        bg_color_rgb565: Background color in RGB565 format (e.g., 0x0000 for black).
    """
    # Get the 8-byte bitmap for the character
    char_bytes = font.get_char_bytes(char)

    # Pack colors into 2-byte big-endian format
    fg_bytes = ustruct.pack(">H", fg_color_rgb565)
    bg_bytes = ustruct.pack(">H", bg_color_rgb565)

    # Create a buffer for the 8x8 pixel data (64 pixels * 2 bytes/pixel = 128 bytes)
    pixel_buffer = bytearray(font.FONT_WIDTH * font.FONT_HEIGHT * 2)
    buffer_idx = 0

    # Iterate through each row (byte) of the character bitmap
    for row_byte in char_bytes:
        # Iterate through each bit (pixel) in the row byte (MSB first)
        for col_bit in range(font.FONT_WIDTH -1, -1, -1):
            if (row_byte >> col_bit) & 1:
                # Bit is 1: Use foreground color
                pixel_buffer[buffer_idx : buffer_idx + 2] = fg_bytes
            else:
                # Bit is 0: Use background color
                pixel_buffer[buffer_idx : buffer_idx + 2] = bg_bytes
            buffer_idx += 2

    # Set the drawing window on the display
    display.set_window(x_pixel, y_pixel,
                       x_pixel + font.FONT_WIDTH - 1,
                       y_pixel + font.FONT_HEIGHT - 1)

    # Write the prepared pixel buffer to the display
    display.write_pixels(pixel_buffer)

# --- Optional Helper Functions (Can be added later) ---

def draw_string(display, text, x_pixel, y_pixel, fg_color_rgb565, bg_color_rgb565):
    current_x = x_pixel
    for char in text:
        # Need to import font if not already globally available in this scope
        draw_char(display, char, current_x, y_pixel, fg_color_rgb565, bg_color_rgb565)
        current_x += font.FONT_WIDTH # Assuming font is imported and FONT_WIDTH is accessible

def clear_screen(display, color_rgb565):
    display.fill_screen(color_rgb565) 