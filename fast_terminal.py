# fast_terminal.py - Optimized Terminal Management using graphics_fast.py
from display.ili9488 import Display
from shell.buffer import ScreenBuffer
import time
import graphics_fast as graphics

# Helper function to pad strings (replacement for ljust)
def pad_string(text, width):
    """Pad a string with spaces to the given width (MicroPython compatible)"""
    return text + " " * (width - len(text))

class FastTerminal:
    """
    Optimized terminal implementation that uses hardware scrolling and
    minimal redraw operations for maximum performance.
    """
    def __init__(self, display, width=320, height=320, line_height=16):
        self.display = display
        self.buffer = ScreenBuffer(width, height, line_height)
        self.width = width
        self.height = height
        self.line_height = line_height
        self.visible_lines = height // line_height
        
        # Calculate character dimensions
        self.char_width = graphics.CHAR_WIDTH_PX
        self.chars_per_line = width // self.char_width
        
        # Initialize FastScreen for optimized drawing - MicroPython style
        # Create directly rather than using get_screen_for_display
        if not hasattr(self.display, "_fast_screen"):
            self.display._fast_screen = graphics.FastScreen(self.display)
        self.screen = self.display._fast_screen
        
        # Keep track of the lines for optimized drawing
        self.text_buffer = []
        for _ in range(self.visible_lines):
            self.text_buffer.append([" " for _ in range(self.chars_per_line)])

        # Define colors
        self.fg_color = 0xFFFF  # White
        self.bg_color = 0x0000  # Black
        
        # Initialize display
        self.screen.clear_screen(self.bg_color)
        
        # Debug info
        print(f"FastTerminal initialized with {self.visible_lines} visible lines, {self.chars_per_line} chars per line")

    def handle_char(self, char):
        """Handle character input"""
        start_time = time.time()
        
        if char == '\n':
            self._handle_new_line()
        elif char == '\b':
            self.buffer.backspace()
            self._redraw_current_line()
        else:
            self.buffer.add_char(char)
            self._redraw_current_line()
        
        # Performance tracking
        if graphics.DEBUG_TIMING:
            elapsed = (time.time() - start_time) * 1000
            print(f"Character handled in {elapsed:.2f}ms")

    def _handle_new_line(self):
        """Handle new line using hardware scrolling for maximum performance."""
        start_time = time.time()
        
        # Add the completed line to the buffer
        self.buffer.new_line()

        # Update the text buffer with visible lines
        current_scroll = self.buffer.get_scroll_position()
        visible_lines = self.buffer.get_visible_lines()
        
        for i, line in enumerate(visible_lines):
            if i < len(self.text_buffer):
                # Convert string to character list
                line_chars = list(pad_string(line, self.chars_per_line))
                self.text_buffer[i] = line_chars
        
        # Check if buffer needs scrolling
        line_count = self.buffer.get_line_count()
        if line_count > self.visible_lines:
            # Increment logical scroll position
            new_logical_scroll = self.buffer.get_scroll_position() + 1
            self.buffer.update_scroll_position(new_logical_scroll)
            
            # Use hardware scrolling
            self.screen.scroll_up(1)  # Scroll one line
            
            # Only draw the new line at the bottom
            bottom_line_idx = self.visible_lines - 1
            bottom_line = pad_string(visible_lines[-1], self.chars_per_line)
            
            # Draw just the new bottom line
            self.screen.draw_row(bottom_line, bottom_line_idx, self.fg_color, self.bg_color)
            
            print(f">>> Hardware Scrolling (Scroll Pos: {new_logical_scroll}) <<<")
        else:
            # No scroll needed, just redraw
            print(">>> No Scroll Needed <<<")
            self._redraw_screen()
        
        # Performance tracking
        if graphics.DEBUG_TIMING:
            elapsed = (time.time() - start_time) * 1000
            print(f"New line handled in {elapsed:.2f}ms")

    def _redraw_current_line(self):
        """Redraw the current input line at its correct position."""
        current_line_text = self.buffer.get_current_line()
        
        # Determine the row index for the current line
        if self.buffer.get_line_count() > self.visible_lines:
            visible_line_index = self.visible_lines - 1  # Bottom line
        else:
            visible_line_index = self.buffer.get_line_count()
            
        # Update the text buffer
        if visible_line_index < len(self.text_buffer):
            line_chars = list(pad_string(current_line_text, self.chars_per_line))
            self.text_buffer[visible_line_index] = line_chars
            
        # Draw just this one line
        self.screen.draw_row(current_line_text, visible_line_index, 
                            self.fg_color, self.bg_color)
        
        # Debugging info
        y_pos = visible_line_index * self.line_height
        print(f"--- Redrawing Current Line at y={y_pos} (Visible Index: {visible_line_index}) --- Text: '{current_line_text}'")

    def _redraw_screen(self):
        """Redraw visible screen content with minimal operations."""
        print("--- Redrawing Screen (Optimized) ---")
        
        # Get the lines that should be visible
        visible_lines_data = self.buffer.get_visible_lines()
        
        # Update our text buffer with current visible lines
        for i, line_text in enumerate(visible_lines_data):
            if i < len(self.text_buffer):
                line_chars = list(pad_string(line_text, self.chars_per_line))
                self.text_buffer[i] = line_chars
        
        # Update the screen with our buffer
        self.screen.update_screen_buffer(self.text_buffer, 0, self.visible_lines, 
                                        self.fg_color, self.bg_color)

    def clear(self):
        """Clear the terminal and buffer."""
        self.buffer.clear()
        self.screen.clear_screen(self.bg_color)
        
        # Reset text buffer
        for i in range(len(self.text_buffer)):
            self.text_buffer[i] = [" " for _ in range(self.chars_per_line)] 