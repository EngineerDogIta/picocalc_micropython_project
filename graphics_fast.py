# pico_project/graphics_fast.py - Optimized Graphics with Hardware Scrolling
# This version prioritizes hardware scrolling and minimal redraws

# Handle import differences between MicroPython and standard Python
try:
    import ustruct as struct
except ImportError:
    import struct

import font # Import font definitions
import time # For performance tracking

# Screen and Font Dimensions
SCREEN_WIDTH_PX = 320
SCREEN_HEIGHT_PX = 320
CHAR_WIDTH_PX = font.FONT_WIDTH
CHAR_HEIGHT_PX = font.FONT_HEIGHT
SCREEN_CHAR_WIDTH = SCREEN_WIDTH_PX // CHAR_WIDTH_PX
SCREEN_CHAR_HEIGHT = SCREEN_HEIGHT_PX // CHAR_HEIGHT_PX

# Performance optimization constants
MAX_BATCH_PIXELS = 512  # Smaller buffer for faster transfers
DEBUG_TIMING = True     # Set to True to output timing information

# Helper functions for color conversion
def rgb565_to_bytes(color):
    """Convert RGB565 color to byte sequence for SPI"""
    return struct.pack(">H", color)

# Screen management class - handles hardware scrolling and efficient updates
class FastScreen:
    def __init__(self, display):
        self.display = display
        self.width = SCREEN_WIDTH_PX
        self.height = SCREEN_HEIGHT_PX
        self.scroll_offset = 0
        
        # Initialize hardware scroll
        self.display.define_scroll_area(0, self.height, 0)
        
        # Track which lines need updates (dirty rectangles)
        self.dirty_rows = set()
        
        # Optimization: Pre-pack common colors
        self.black_bytes = rgb565_to_bytes(0x0000)
        self.white_bytes = rgb565_to_bytes(0xFFFF)
        
        # Create character drawing buffers
        self._init_char_cache()
    
    def _init_char_cache(self):
        """Pre-generate character bitmaps for faster drawing"""
        self.char_cache = {}
        # We'll lazily create and cache character bitmaps as they're used
    
    def get_char_bitmap(self, char, fg_color, bg_color):
        """Get or create a character bitmap with the specified colors"""
        cache_key = (char, fg_color, bg_color)
        
        if cache_key in self.char_cache:
            return self.char_cache[cache_key]
            
        # Create a new character bitmap
        char_bytes = font.get_char_bytes(char)
        fg_bytes = rgb565_to_bytes(fg_color)
        bg_bytes = rgb565_to_bytes(bg_color)
        
        # Create buffer for the character
        bitmap = bytearray(CHAR_WIDTH_PX * CHAR_HEIGHT_PX * 2)
        
        # Fill the bitmap
        idx = 0
        for row_byte in char_bytes:
            for col_bit in range(CHAR_WIDTH_PX - 1, -1, -1):
                if (row_byte >> col_bit) & 1:
                    bitmap[idx:idx+2] = fg_bytes
                else:
                    bitmap[idx:idx+2] = bg_bytes
                idx += 2
        
        # Cache and return
        self.char_cache[cache_key] = bitmap
        return bitmap
    
    def hardware_scroll(self, rows):
        """Scroll the display by the specified number of rows (text lines)"""
        pixels_to_scroll = rows * CHAR_HEIGHT_PX
        
        # Calculate new scroll offset
        new_offset = (self.scroll_offset + pixels_to_scroll) % self.height
        
        # Set hardware scroll register
        self.display.set_scroll_start(new_offset)
        self.scroll_offset = new_offset
    
    def scroll_up(self, num_rows=1):
        """Scroll display up by num_rows lines, only redrawing new lines"""
        if num_rows <= 0:
            return
            
        # Perform hardware scroll
        self.hardware_scroll(num_rows)
        
        # Mark the newly exposed bottom rows as dirty
        for i in range(SCREEN_CHAR_HEIGHT - num_rows, SCREEN_CHAR_HEIGHT):
            self.dirty_rows.add(i)
    
    def clear_row(self, row, color=0x0000):
        """Efficiently clear a single row"""
        y = (row * CHAR_HEIGHT_PX) % self.height
        self.display.set_window(0, y, self.width - 1, y + CHAR_HEIGHT_PX - 1)
        
        # Use a smaller buffer for the clear operation
        row_bytes = self.width * CHAR_HEIGHT_PX * 2
        clear_buffer_size = min(row_bytes, MAX_BATCH_PIXELS * 2)
        clear_buffer = bytearray(clear_buffer_size)
        
        # Fill buffer with color
        color_bytes = rgb565_to_bytes(color)
        for i in range(0, clear_buffer_size, 2):
            clear_buffer[i:i+2] = color_bytes
        
        # Send the clear buffer in chunks
        remaining = row_bytes
        while remaining > 0:
            chunk = min(remaining, clear_buffer_size)
            self.display.write_pixels(clear_buffer[:chunk])
            remaining -= chunk
    
    def draw_char_at(self, char, col, row, fg_color=0xFFFF, bg_color=0x0000):
        """Draw a character at the specified text position"""
        # Get physical coordinates
        x = col * CHAR_WIDTH_PX
        y = (row * CHAR_HEIGHT_PX) % self.height
        
        # Get character bitmap
        bitmap = self.get_char_bitmap(char, fg_color, bg_color)
        
        # Draw to display
        self.display.set_window(x, y, x + CHAR_WIDTH_PX - 1, y + CHAR_HEIGHT_PX - 1)
        self.display.write_pixels(bitmap)
    
    def draw_text_at(self, text, col, row, fg_color=0xFFFF, bg_color=0x0000):
        """Draw text at the specified text position"""
        if not text:
            return
            
        # Get physical coordinates
        start_x = col * CHAR_WIDTH_PX
        y = (row * CHAR_HEIGHT_PX) % self.height
        end_x = start_x + (len(text) * CHAR_WIDTH_PX) - 1
        
        # Check if we should use individual character drawing or batch
        if len(text) <= 4:  # For very short strings, draw chars individually
            for i, char in enumerate(text):
                x = start_x + (i * CHAR_WIDTH_PX)
                self.draw_char_at(char, col + i, row, fg_color, bg_color)
            return
        
        # Batch drawing for longer text
        # Set window for the entire text
        self.display.set_window(start_x, y, end_x, y + CHAR_HEIGHT_PX - 1)
        
        # Create buffer for the entire text area
        buffer_size = len(text) * CHAR_WIDTH_PX * CHAR_HEIGHT_PX * 2
        
        # If buffer is too large, fall back to individual chars
        if buffer_size > MAX_BATCH_PIXELS * 2:
            for i, char in enumerate(text):
                self.draw_char_at(char, col + i, row, fg_color, bg_color)
            return
            
        # Create and fill the buffer for the entire text
        buffer = bytearray(buffer_size)
        buf_idx = 0
        
        for char in text:
            char_bitmap = self.get_char_bitmap(char, fg_color, bg_color)
            buffer[buf_idx:buf_idx + len(char_bitmap)] = char_bitmap
            buf_idx += len(char_bitmap)
        
        # Send the buffer to the display
        self.display.write_pixels(buffer)
        
        # Mark row as clean
        if row in self.dirty_rows:
            self.dirty_rows.remove(row)
    
    def draw_row(self, row_data, row, fg_color=0xFFFF, bg_color=0x0000):
        """Draw a complete row of text"""
        if not row_data:
            return
            
        # Convert row_data to string if it's a list
        if isinstance(row_data, (list, tuple)):
            row_data = ''.join(row_data)
            
        # Truncate if too long
        if len(row_data) > SCREEN_CHAR_WIDTH:
            row_data = row_data[:SCREEN_CHAR_WIDTH]
            
        # First clear the row
        self.clear_row(row, bg_color)
        
        # Then draw the text
        self.draw_text_at(row_data, 0, row, fg_color, bg_color)
    
    def update_screen_buffer(self, buffer, start_row, num_rows, fg_color=0xFFFF, bg_color=0x0000):
        """Update screen from a text buffer with minimal redraws"""
        if DEBUG_TIMING:
            start_time = time.time()
            
        # Only update rows that need to be updated
        update_count = 0
        
        for i in range(min(num_rows, SCREEN_CHAR_HEIGHT)):
            buffer_row = start_row + i
            screen_row = i
            
            # Skip if this row isn't dirty and we haven't scrolled
            if screen_row not in self.dirty_rows and self.scroll_offset == 0:
                continue
                
            # Only update if we have data for this row
            if buffer_row < len(buffer):
                self.draw_row(buffer[buffer_row], screen_row, fg_color, bg_color)
                update_count += 1
                
                # Row is now clean
                if screen_row in self.dirty_rows:
                    self.dirty_rows.remove(screen_row)
        
        if DEBUG_TIMING:
            elapsed = (time.time() - start_time) * 1000
            print(f"Updated {update_count} rows in {elapsed:.2f}ms")
    
    def clear_screen(self, color=0x0000):
        """Clear the entire screen and reset scroll state"""
        # Use the display's native fill_screen
        if DEBUG_TIMING:
            start_time = time.time()
            
        self.display.fill_screen(color)
        
        # Reset scroll state
        self.display.set_scroll_start(0)
        self.scroll_offset = 0
        
        # All rows are clean after a full clear
        self.dirty_rows.clear()
        
        if DEBUG_TIMING:
            elapsed = (time.time() - start_time) * 1000
            print(f"Screen cleared in {elapsed:.2f}ms")

# Compatibility with existing graphics.py API - MicroPython style
def draw_string(display, text, x_pixel, y_pixel, fg_color_rgb565, bg_color_rgb565):
    """Draw text at pixel coordinates (compatibility function)"""
    # Use direct attribute access - MicroPython style
    if not hasattr(display, "_fast_screen"):
        display._fast_screen = FastScreen(display)
    
    screen = display._fast_screen
    
    # Convert pixel coordinates to text coordinates
    col = x_pixel // CHAR_WIDTH_PX
    row = y_pixel // CHAR_HEIGHT_PX
    
    # Draw the text
    screen.draw_text_at(text, col, row, fg_color_rgb565, bg_color_rgb565)

def draw_rows(display, buffer, start_row, num_rows, fg_color_rgb565, bg_color_rgb565):
    """Draw multiple rows from a buffer (compatibility function)"""
    # Use direct attribute access - MicroPython style
    if not hasattr(display, "_fast_screen"):
        display._fast_screen = FastScreen(display)
    
    screen = display._fast_screen
    
    # Update the screen
    screen.update_screen_buffer(buffer, start_row, num_rows, fg_color_rgb565, bg_color_rgb565)

def optimized_scroll(display, buffer, start_row, num_rows, fg_color_rgb565, bg_color_rgb565):
    """Scroll the display and update with new content (compatibility function)"""
    # Use direct attribute access - MicroPython style
    if not hasattr(display, "_fast_screen"):
        display._fast_screen = FastScreen(display)
    
    screen = display._fast_screen
    
    # Store last start row directly on the display object
    if not hasattr(display, "_last_start_row"):
        display._last_start_row = 0
    
    # Calculate how many rows to scroll
    rows_to_scroll = start_row - display._last_start_row
    display._last_start_row = start_row
    
    if rows_to_scroll > 0:
        # Scroll the display
        screen.scroll_up(rows_to_scroll)
        
    # Update the screen content
    screen.update_screen_buffer(buffer, start_row, num_rows, fg_color_rgb565, bg_color_rgb565)
    
    return True

def clear_screen(display, color_rgb565):
    """Clear the entire screen (compatibility function)"""
    # Use direct attribute access - MicroPython style
    if not hasattr(display, "_fast_screen"):
        display._fast_screen = FastScreen(display)
    
    screen = display._fast_screen
    
    # Clear the screen
    screen.clear_screen(color_rgb565)

def draw_char(display, char, x_pixel, y_pixel, fg_color_rgb565, bg_color_rgb565):
    """Draw a single character at pixel coordinates (compatibility function)"""
    # Use direct attribute access - MicroPython style
    if not hasattr(display, "_fast_screen"):
        display._fast_screen = FastScreen(display)
    
    screen = display._fast_screen
    
    # Convert pixel coordinates to text coordinates
    col = x_pixel // CHAR_WIDTH_PX
    row = y_pixel // CHAR_HEIGHT_PX
    
    # Draw the character
    screen.draw_char_at(char, col, row, fg_color_rgb565, bg_color_rgb565)

def clear_rect(display, x_pixel, y_pixel, width_px, height_px, color_rgb565):
    """Clear a rectangular area (compatibility function)"""
    # Use direct attribute access - MicroPython style
    if not hasattr(display, "_fast_screen"):
        display._fast_screen = FastScreen(display)
    
    screen = display._fast_screen
    
    # Convert to row coordinates
    start_row = y_pixel // CHAR_HEIGHT_PX
    end_row = (y_pixel + height_px - 1) // CHAR_HEIGHT_PX
    
    # Clear each row
    for row in range(start_row, end_row + 1):
        if 0 <= row < SCREEN_CHAR_HEIGHT:
            screen.clear_row(row, color_rgb565)
            screen.dirty_rows.add(row) 