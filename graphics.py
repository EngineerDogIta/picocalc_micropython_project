# pico_project/graphics.py - Basic Graphics Drawing Functions

# Handle import differences between MicroPython and standard Python
try:
    import ustruct as struct
except ImportError:
    try:
        import struct
    except ImportError:
        # If neither is available, provide a fallback
        print("Warning: Neither ustruct nor struct modules available!")
        # Define a minimal struct implementation for RGB565 color packing
        class MinimalStruct:
            @staticmethod
            def pack(fmt, value):
                # Very basic implementation for RGB565 format only
                if fmt == ">H" and isinstance(value, int):
                    # Big-endian 16-bit unsigned
                    return bytes([(value >> 8) & 0xFF, value & 0xFF])
                raise ValueError("Unsupported format in minimal struct implementation")
        struct = MinimalStruct()

import font # Import the font definitions

# Screen and Font Dimensions (Pixel-based)
SCREEN_WIDTH_PX = 320 # Assuming ILI9488 is 320x320
SCREEN_HEIGHT_PX = 320
CHAR_WIDTH_PX = font.FONT_WIDTH
CHAR_HEIGHT_PX = font.FONT_HEIGHT
SCREEN_CHAR_WIDTH = SCREEN_WIDTH_PX // CHAR_WIDTH_PX # 40
SCREEN_CHAR_HEIGHT = SCREEN_HEIGHT_PX // CHAR_HEIGHT_PX # 40

# --- Performance Optimization Constants ---
# Larger buffer for batch operations
MAX_BATCH_PIXELS = 1024  # Adjust based on available memory
BATCH_ENABLED = True     # Can be toggled if needed

# Pre-pack common colors if needed, or do it dynamically
# COLOR_BLACK_BYTES = struct.pack(">H", 0x0000)
# COLOR_WHITE_BYTES = struct.pack(">H", 0xFFFF)

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
    fg_bytes = struct.pack(">H", fg_color_rgb565)
    bg_bytes = struct.pack(">H", bg_color_rgb565)

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

def draw_char_batch(display, chars, positions, fg_color_rgb565, bg_color_rgb565):
    """
    Batch draws multiple characters with a single window set and SPI transaction.
    
    Args:
        display: The initialized Display object
        chars: List of characters to draw
        positions: List of (x,y) tuples for character positions
        fg_color_rgb565: Foreground color
        bg_color_rgb565: Background color
    """
    if not chars:
        return
        
    # Find the bounding rectangle for all characters
    min_x = min(pos[0] for pos in positions)
    min_y = min(pos[1] for pos in positions)
    max_x = max(pos[0] + CHAR_WIDTH_PX - 1 for pos in positions)
    max_y = max(pos[1] + CHAR_HEIGHT_PX - 1 for pos in positions)
    
    # Calculate rectangle width and height
    width = max_x - min_x + 1
    height = max_y - min_y + 1
    
    # Create a buffer for the entire area
    buffer_size = width * height * 2
    
    # If buffer would be too large, fall back to individual drawing
    if buffer_size > MAX_BATCH_PIXELS * 2 or not BATCH_ENABLED:
        for char, pos in zip(chars, positions):
            draw_char(display, char, pos[0], pos[1], fg_color_rgb565, bg_color_rgb565)
        return
    
    # Create background buffer filled with background color
    bg_bytes = struct.pack(">H", bg_color_rgb565)
    fg_bytes = struct.pack(">H", fg_color_rgb565)
    
    # Fill entire area with background color first
    buffer = bytearray(buffer_size)
    for i in range(0, buffer_size, 2):
        buffer[i:i+2] = bg_bytes
    
    # Draw each character into the buffer
    for char, (x, y) in zip(chars, positions):
        char_bytes = font.get_char_bytes(char)
        rel_x = x - min_x
        rel_y = y - min_y
        
        for row_idx, row_byte in enumerate(char_bytes):
            for col_bit in range(CHAR_WIDTH_PX - 1, -1, -1):
                if (row_byte >> col_bit) & 1:
                    # Calculate position in buffer
                    buffer_x = rel_x + (CHAR_WIDTH_PX - 1 - col_bit)
                    buffer_y = rel_y + row_idx
                    buffer_pos = (buffer_y * width + buffer_x) * 2
                    buffer[buffer_pos:buffer_pos+2] = fg_bytes
    
    # Set the window for the entire area and send the buffer
    display.set_window(min_x, min_y, max_x, max_y)
    display.write_pixels(buffer)

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
    color_bytes = struct.pack(">H", color_rgb565)

    # Calculate the total number of pixels
    num_pixels = width_px * height_px

    # Optimize: Use maximum buffer size that fits in memory
    # This drastically reduces the number of SPI transactions
    pixels_per_chunk = min(num_pixels, MAX_BATCH_PIXELS)
    chunk_buffer = bytearray(pixels_per_chunk * 2)
    
    # Fill the buffer with the color
    for i in range(0, len(chunk_buffer), 2):
        chunk_buffer[i:i+2] = color_bytes
    
    # Send the buffer in chunks
    pixels_remaining = num_pixels
    while pixels_remaining > 0:
        chunk_size = min(pixels_remaining, pixels_per_chunk)
        # Only need to send the relevant portion of the buffer
        display.write_pixels(chunk_buffer[:chunk_size*2])
        pixels_remaining -= chunk_size

def draw_string(display, text, x_pixel, y_pixel, fg_color_rgb565, bg_color_rgb565):
    """
    Draws a string of text using optimized batch operations when possible.
    """
    if not text:
        return
        
    if BATCH_ENABLED:
        # Prepare character and position lists for batch operation
        chars = list(text)
        positions = [(x_pixel + i * CHAR_WIDTH_PX, y_pixel) for i in range(len(text))]
        draw_char_batch(display, chars, positions, fg_color_rgb565, bg_color_rgb565)
    else:
        # Fall back to character-by-character drawing
        current_x = x_pixel
        for char in text:
            draw_char(display, char, current_x, y_pixel, fg_color_rgb565, bg_color_rgb565)
            current_x += CHAR_WIDTH_PX

def clear_screen(display, color_rgb565):
    """
    Clears the entire screen with a color using optimal SPI transfers.
    """
    display.fill_screen(color_rgb565)

def optimized_scroll(display, buffer, start_row, num_rows, fg_color_rgb565, bg_color_rgb565):
    """
    Optimized scrolling that:
    1. Uses hardware scrolling when available
    2. Only redraws the newly exposed area (not the entire screen)
    3. Batches character drawing operations
    
    Args:
        display: The display object
        buffer: 2D character buffer (list of lists)
        start_row: Starting row to display
        num_rows: Number of rows to display
        fg_color_rgb565: Text color
        bg_color_rgb565: Background color
    """
    # First try hardware scrolling
    try:
        # If available in the display driver
        if hasattr(display, 'hardware_scroll'):
            scroll_lines = start_row * CHAR_HEIGHT_PX
            display.hardware_scroll(scroll_lines)
            # Only need to redraw the newly exposed line at the bottom
            bottom_row = min(start_row + num_rows - 1, len(buffer) - 1)
            
            # Batch draw the bottom line
            chars = buffer[bottom_row]
            positions = [(col * CHAR_WIDTH_PX, bottom_row * CHAR_HEIGHT_PX) 
                         for col in range(len(chars))]
            draw_char_batch(display, chars, positions, fg_color_rgb565, bg_color_rgb565)
            return True
    except Exception as e:
        # Fall back to software scrolling
        pass
        
    # Software scrolling with batch operations
    visible_rows = buffer[start_row:start_row + num_rows]
    
    # Batch all characters in the visible area
    all_chars = []
    all_positions = []
    
    for row_idx, row in enumerate(visible_rows):
        for col_idx, char in enumerate(row):
            all_chars.append(char)
            x = col_idx * CHAR_WIDTH_PX
            y = row_idx * CHAR_HEIGHT_PX
            all_positions.append((x, y))
            
    # Clear screen
    clear_screen(display, bg_color_rgb565)
    
    # Draw all characters in one batch operation
    draw_char_batch(display, all_chars, all_positions, fg_color_rgb565, bg_color_rgb565)
    return True

# Row-based display drawing (more efficient than character-by-character)
def draw_rows(display, buffer, start_row, num_rows, fg_color_rgb565, bg_color_rgb565):
    """
    Draws multiple rows from the buffer, optimizing by drawing entire rows at once.
    
    Much faster than character-by-character updates for scrolling operations.
    """
    for row_idx in range(num_rows):
        buffer_row = start_row + row_idx
        if buffer_row >= len(buffer):
            break
            
        # Draw an entire row in one batch operation
        y_pos = row_idx * CHAR_HEIGHT_PX
        draw_string(display, ''.join(buffer[buffer_row]), 0, y_pos, 
                   fg_color_rgb565, bg_color_rgb565)

# --- Removing scroll_up placeholder, scrolling handled in main.py via buffer ---
# def scroll_up(display, num_lines, bg_color_rgb565):
#     ...

# --- Optional Helper Functions (Can be added later) --- 