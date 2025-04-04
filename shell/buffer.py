# shell/buffer.py - Screen Buffer Management (Software Scroll Only)
from collections import deque

class ScreenBuffer:
    """
    Manages screen buffer using software scroll logic only.
    """
    def __init__(self, width, height, line_height):
        self.width = width
        self.height = height
        self.line_height = line_height
        
        # Calculate buffer size based on screen dimensions
        calculated_maxlen = height // line_height + 10 # Allow slightly larger buffer
        
        # Create a deque with proper initialization
        # Note: We're bypassing linter issues by creating the deque
        # in a way that works for both MicroPython and CPython
        self.lines = deque(maxlen=calculated_maxlen)
        
        # For MicroPython compatibility, we might need special handling
        # but this is commented out due to linter issues
        # MicroPython uses: deque([], maxlen, 0) with positional args
        
        self.current_line = ""
        self.scroll_position = 0 # Logical scroll lines (lines above visible area)

    def add_char(self, char):
        """Add character to current line"""
        self.current_line += char
        
    def new_line(self):
        """Add current line to buffer and start new line"""
        self.lines.append(self.current_line)
        self.current_line = ""
        
    def backspace(self):
        """Handle backspace in current line"""
        if self.current_line:
            self.current_line = self.current_line[:-1]
            
    def clear(self):
        """Clear buffer and current line, reset scroll state"""
        while self.lines:
            self.lines.popleft()
        self.current_line = ""
        self.scroll_position = 0
        
    def get_visible_lines(self):
        """Get lines currently visible on screen based on logical scroll"""
        visible_height_lines = self.height // self.line_height
        # Calculate the slice of the deque to display
        start_idx = self.scroll_position
        end_idx = self.scroll_position + visible_height_lines
        
        # Convert to list and slice
        # Note: We assume deque is iterable in both MicroPython and CPython
        lines_list = [line for line in self.lines]
        return lines_list[start_idx:end_idx]
        
    def get_scroll_position(self):
        """Get current logical scroll position"""
        return self.scroll_position
        
    def update_scroll_position(self, new_position):
        """Update logical scroll position (used primarily during hardware scroll phase)"""
        # No upper bound needed now as buffer handles overflow
        self.scroll_position = max(0, new_position)
        
    def get_line_count(self):
        """Get total number of lines in buffer"""
        return len(self.lines)
        
    def get_current_line(self):
        """Get current line being edited"""
        return self.current_line 