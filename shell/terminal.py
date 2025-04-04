# shell/terminal.py - Terminal Management
from display.ili9488 import Display
from shell.buffer import ScreenBuffer
import time
import graphics

# Helper function to pad strings (replacement for ljust)
def pad_string(text, width):
    """Pad a string with spaces to the given width (MicroPython compatible)"""
    return text + " " * (width - len(text))

# Placeholder for graphics drawing - replace with actual implementation
class Graphics:
    def __init__(self, display):
        self.display = display
        self.line_height = 16  # Should get from config/font
        self.width = 320       # Should get from config

    def draw_text(self, text, x, y, color=0xFFFF, background=0x0000):
        # Use the optimized graphics drawing functions
        graphics.draw_string(self.display, text, x, y, color, background)

class Terminal:
    """
    Manages terminal display, switching from hardware to software scroll at a threshold.
    """
    def __init__(self, display, width=320, height=320, line_height=16):
        self.display = display
        self.buffer = ScreenBuffer(width, height, line_height)
        self.width = width
        self.height = height
        self.line_height = line_height
        self.visible_lines = height // line_height
        self.graphics = Graphics(display)
        
        # Keep track of the lines for optimized drawing
        self.text_buffer = []
        self.char_width = graphics.CHAR_WIDTH_PX
        self.chars_per_line = width // self.char_width
        
        for _ in range(self.visible_lines):
            self.text_buffer.append([" " for _ in range(self.chars_per_line)])

        # Initialize display
        self.display.define_scroll_area(0, height, 0)
        self.display.fill_screen(0x0000)

    def handle_char(self, char):
        """Handle character input"""
        if char == '\n':
            self._handle_new_line()
        elif char == '\b':
            self.buffer.backspace()
            self._redraw_current_line()
        else:
            self.buffer.add_char(char)
            self._redraw_current_line()

    def _handle_new_line(self):
        """Handle new line using optimized scrolling."""
        # Add the completed line to the buffer
        self.buffer.new_line()

        # Add the line to our text buffer for optimized drawing
        current_scroll = self.buffer.get_scroll_position()
        visible_lines = self.buffer.get_visible_lines()
        
        # Update the text buffer with visible lines
        for i, line in enumerate(visible_lines):
            if i < len(self.text_buffer):
                # Convert string to list of characters for the buffer
                # Using our pad_string function instead of ljust
                line_chars = list(pad_string(line, self.chars_per_line))
                self.text_buffer[i] = line_chars
        
        # Check if buffer needs scrolling
        line_count = self.buffer.get_line_count()
        if line_count > self.visible_lines:
            # Increment logical scroll position
            new_logical_scroll = self.buffer.get_scroll_position() + 1
            self.buffer.update_scroll_position(new_logical_scroll)
            print(f">>> Software Scrolling (Scroll Pos: {new_logical_scroll}) <<< ")
            
            # Use the optimized scroll method for better performance
            graphics.optimized_scroll(
                self.display, 
                self.text_buffer,
                0,  # Start from top of visible area
                self.visible_lines, 
                0xFFFF,  # White text
                0x0000   # Black background
            )
        else:
            # No scroll needed, just redraw screen
            print(">>> No Scroll Needed <<< ")
            self._redraw_screen()

    def _redraw_current_line(self):
        """Redraw the current input line at its correct position using optimized methods."""
        current_line_text = self.buffer.get_current_line()
        
        # Convert to list of characters for the text buffer
        # Using our pad_string function instead of ljust
        current_line_chars = list(pad_string(current_line_text, self.chars_per_line))
        
        # Determine the row index for the current line
        if self.buffer.get_line_count() > self.visible_lines:
            visible_line_index = self.visible_lines - 1  # Bottom line
        else:
            visible_line_index = self.buffer.get_line_count()
            
        # Update the text buffer
        if visible_line_index < len(self.text_buffer):
            self.text_buffer[visible_line_index] = current_line_chars
            
        # Calculate physical Y position
        y_pos = min(max(0, visible_line_index), self.visible_lines - 1) * self.line_height

        print(f"--- Redrawing Current Line at y={y_pos} (Visible Index: {visible_line_index}) --- Text: '{current_line_text}'")
        
        # Use optimized string drawing for the current line
        graphics.draw_string(
            self.display,
            current_line_text,
            0, y_pos,
            0xFFFF,  # White text
            0x0000   # Black background
        )

    def _redraw_screen(self):
        """Redraw entire visible screen content from buffer using optimized batch operations."""
        print("--- Redrawing Full Screen (Optimized) --- ")
        
        # Get the lines that should be visible based on current scroll position
        visible_lines_data = self.buffer.get_visible_lines()
        
        # Update our text buffer with the current visible lines
        for i, line_text in enumerate(visible_lines_data):
            if i < len(self.text_buffer):
                # Using our pad_string function instead of ljust
                line_chars = list(pad_string(line_text, self.chars_per_line))
                self.text_buffer[i] = line_chars
                
        # Use the optimized row drawing method for better performance
        graphics.draw_rows(
            self.display,
            self.text_buffer,
            0,  # Start from top of visible area
            self.visible_lines,
            0xFFFF,  # White text
            0x0000   # Black background
        )
        
        # Redraw the current input line
        self._redraw_current_line() 