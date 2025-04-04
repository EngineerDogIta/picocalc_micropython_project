# pico_project/graphics.py - Basic Graphics Drawing Functions

import ustruct
import font # Import the font definitions

# Screen and Font Dimensions (Pixel-based)
SCREEN_WIDTH_PX = 320 # Assuming ILI9488 is 320x320
SCREEN_HEIGHT_PX = 320
CHAR_WIDTH_PX = font.FONT_WIDTH
CHAR_HEIGHT_PX = font.FONT_HEIGHT
SCREEN_CHAR_WIDTH = SCREEN_WIDTH_PX // CHAR_WIDTH_PX # 40
SCREEN_CHAR_HEIGHT = SCREEN_HEIGHT_PX // CHAR_HEIGHT_PX # 40

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

def clear_rect(display, x_pixel, y_pixel, width_px, height_px, color_rgb565):
    """
    Fills a rectangular area of the display with a solid color.

    Args:
        display: The initialized Display object.
        x_pixel: The top-left x-coordinate (in pixels).
        y_pixel: The top-left y-coordinate (in pixels).
        width_px: The width of the rectangle (in pixels).
        height_px: The height of the rectangle (in pixels).
        color_rgb565: Fill color in RGB565 format.
    """
    if x_pixel < 0 or y_pixel < 0 or \
       x_pixel + width_px > SCREEN_WIDTH_PX or \
       y_pixel + height_px > SCREEN_HEIGHT_PX:
        # Optional: Add clipping or error handling here if needed
        # print("Warning: clear_rect coordinates out of bounds")
        # Adjust coordinates/dimensions if possible, or just return
        return # Simplest handling: do nothing if out of bounds

    # Set the window to the rectangle's dimensions
    display.set_window(x_pixel, y_pixel,
                       x_pixel + width_px - 1,
                       y_pixel + height_px - 1)

    # Prepare the color buffer for a single pixel
    color_bytes = ustruct.pack(">H", color_rgb565)

    # Calculate the total number of pixels
    num_pixels = width_px * height_px

    # Create a buffer for one row or a chunk at a time to avoid large allocations
    # Let's send pixel data pixel by pixel for simplicity here,
    # although buffering might be faster if memory allows.
    # Optimization: Create a buffer for the color data and write it repeatedly
    # For maximum memory efficiency on Pico, write pixel by pixel if needed.
    # display.write_pixels() likely expects a buffer, so let's prepare a small one.

    # Simple approach: Write color for each pixel (less efficient but simple)
    # This might be slow. A buffered approach is better.
    # Let's try writing the color bytes repeatedly using write_pixels.
    # write_pixels takes a buffer. We can send the same 2-byte color buffer many times.
    # However, the underlying driver might expect a buffer containing all pixel data.
    # Let's check ili9488.py or assume write_pixels can handle repeated small writes
    # if display._write exists or similar low-level function.
    # If write_pixels needs the full buffer:
    # chunk_size = 512 # bytes, adjust based on memory
    # full_buffer_size = num_pixels * 2
    # ... logic to fill and send chunks ...

    # Alternative: Use display.fill_rect if available, otherwise implement manually.
    # Assuming fill_rect is not standard, we implement via set_window + write_pixels.

    # Prepare a buffer for a single row might be a good compromise
    row_buffer_size = width_px * 2 # bytes per row
    if row_buffer_size > 0:
        row_buffer = bytearray(width_px * 2)
        for i in range(0, width_px * 2, 2):
            row_buffer[i:i+2] = color_bytes

        # Write the row buffer repeatedly for each row
        for _ in range(height_px):
            display.write_pixels(row_buffer)
    # else: handle zero width/height if necessary

# --- Removing scroll_up placeholder, scrolling handled in main.py via buffer ---
# def scroll_up(display, num_lines, bg_color_rgb565):
#     ...

# --- Optional Helper Functions (Can be added later) ---

def draw_string(display, text, x_pixel, y_pixel, fg_color_rgb565, bg_color_rgb565):
    current_x = x_pixel
    for char in text:
        # Need to import font if not already globally available in this scope
        draw_char(display, char, current_x, y_pixel, fg_color_rgb565, bg_color_rgb565)
        current_x += font.FONT_WIDTH # Assuming font is imported and FONT_WIDTH is accessible

def clear_screen(display, color_rgb565):
    display.fill_screen(color_rgb565) 