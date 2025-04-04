# main.py - Refactored main application using Display, Graphics, and PicoCalc Keyboard

import time
from ili9488 import Display # Import the Display class
import graphics           # Import the graphics module
import font               # Import font definitions/dimensions
import keyboard          # Import the new PicoCalc keyboard driver

# Import constants from graphics
from graphics import SCREEN_CHAR_WIDTH, SCREEN_CHAR_HEIGHT, CHAR_WIDTH_PX, CHAR_HEIGHT_PX, clear_rect

# --- Display Configuration ---
LCD_CS_PIN = 13   # Chip Select
LCD_DC_PIN = 14   # Data/Command
LCD_RST_PIN = 15  # Reset
LCD_SCK_PIN = 10  # SPI Clock
LCD_MOSI_PIN = 11 # SPI Data Out
LCD_BL_PIN = 12   # Backlight Control (Active High)

LCD_WIDTH = 320  # Display width in pixels
LCD_HEIGHT = 320 # Display height in pixels (Square display)

SPI_BUS = 1 # Use SPI1 (matches schematic pins GP10, GP11)
SPI_BAUDRATE = 20_000_000 # SPI clock frequency

# --- Color Definitions (RGB565) ---
COLOR_BLACK = 0x0000
COLOR_WHITE = 0xFFFF
COLOR_RED   = 0xF800
COLOR_GREEN = 0x07E0
COLOR_BLUE  = 0x001F
COLOR_CYAN  = 0x07FF
COLOR_MAGENTA = 0xF81F
COLOR_YELLOW = 0xFFE0

# --- Debug Configuration ---
DEBUG_MODE = False  # Set to False for normal operation, True for debugging

print("--- Initializing Display ---")
# Initialize the display driver
# The Display class constructor handles pin/SPI setup, reset, and init sequence.
display = Display(spi_bus=SPI_BUS,
                  cs_pin=LCD_CS_PIN, dc_pin=LCD_DC_PIN, rst_pin=LCD_RST_PIN,
                  bl_pin=LCD_BL_PIN, sck_pin=LCD_SCK_PIN, mosi_pin=LCD_MOSI_PIN,
                  width=LCD_WIDTH, height=LCD_HEIGHT, baudrate=SPI_BAUDRATE)

print("--- Initializing PicoCalc Keyboard ---")
# Initialize the keyboard driver with default I2C settings (I2C1, SDA=GP6, SCL=GP7)
# Rename the instance to avoid conflict with the module name
kbd = keyboard.init()  # This uses the default settings from keyboard.py

print("--- Initializing Shell ---")

# --- Shell Configuration & State ---
# Screen buffer: List of lists (rows of characters)
screen_buffer = [[' ' for _ in range(SCREEN_CHAR_WIDTH)] for _ in range(SCREEN_CHAR_HEIGHT)]
cursor_col = 0
cursor_row = 0
PROMPT = "> " # Define the prompt string
# line_buffer and current_prompt_row are no longer needed

def redraw_screen(display, buffer, c_col, c_row):
    """Redraws the entire screen from the buffer, placing cursor.
    NOTE: Full redraw can be slow, optimizations are possible.
    """
    for r in range(SCREEN_CHAR_HEIGHT):
        for c in range(SCREEN_CHAR_WIDTH):
            char = buffer[r][c]
            fg = COLOR_WHITE
            bg = COLOR_BLACK
            # Invert colors for cursor position
            if r == c_row and c == c_col:
                fg = COLOR_BLACK
                bg = COLOR_WHITE
            
            graphics.draw_char(display, char, 
                               c * CHAR_WIDTH_PX, 
                               r * CHAR_HEIGHT_PX, 
                               fg, bg)

# Clear the physical screen initially
graphics.clear_screen(display, COLOR_BLACK)

# Initialize buffer (already done with spaces)
# Draw the initial prompt into the buffer
for i, char in enumerate(PROMPT):
    if i < SCREEN_CHAR_WIDTH:
        screen_buffer[cursor_row][i] = char
cursor_col = len(PROMPT) # Update cursor position after prompt

# Initial screen draw from buffer
redraw_screen(display, screen_buffer, cursor_col, cursor_row)

print(f"Terminal Size: {SCREEN_CHAR_WIDTH}x{SCREEN_CHAR_HEIGHT}")
print("Shell initialized. Waiting for input...")

# Define the valid Enter key codes (CR/LF is all we need now with corrected key handling)
ENTER_KEY_CODES = [13]  # CR only since we standardized on CR in keyboard.py
# Arrow key codes from keyboard reverse engineering
ARROW_UP = 0xB5
ARROW_DOWN = 0xB6
ARROW_LEFT = 0xB4 # Define if needed later
ARROW_RIGHT = 0xB7 # Define if needed later
BACKSPACE_KEYS = [8, 133] # ASCII BS and DEL

def handle_key(key_code):
    """Handle a key code from the keyboard using screen buffer"""
    global cursor_col, cursor_row # screen_buffer is global implicitly
    redraw_needed = False

    # --- Debug --- 
    if DEBUG_MODE:
        key_name = "Unknown"
        if 32 <= key_code <= 126: key_name = f"'{chr(key_code)}'"
        elif key_code in BACKSPACE_KEYS: key_name = "Backspace"
        elif key_code in ENTER_KEY_CODES: key_name = "Enter"
        elif key_code == ARROW_UP: key_name = "Up Arrow"
        elif key_code == ARROW_DOWN: key_name = "Down Arrow"
        status = kbd.last_raw_status if kbd else None
        status_str = f"0x{status:04X}" if status is not None else "None"
        print(f"DEBUG: Key: 0x{key_code:02X}, Name: {key_name}, Raw: {status_str}, Cursor: ({cursor_col},{cursor_row})")

    # --- Printable Characters --- 
    if 32 <= key_code <= 126:
        char = chr(key_code)
        screen_buffer[cursor_row][cursor_col] = char
        cursor_col += 1
        # Handle line wrap
        if cursor_col >= SCREEN_CHAR_WIDTH:
            cursor_col = 0
            cursor_row += 1
            # Handle screen scroll
            if cursor_row >= SCREEN_CHAR_HEIGHT:
                # Scroll buffer content up
                screen_buffer.pop(0) # Remove top line
                screen_buffer.append([' ' for _ in range(SCREEN_CHAR_WIDTH)]) # Add blank line at bottom
                cursor_row = SCREEN_CHAR_HEIGHT - 1 # Keep cursor on last line
        redraw_needed = True

    # --- Backspace --- 
    elif key_code in BACKSPACE_KEYS:
        original_cursor_col = cursor_col
        original_cursor_row = cursor_row
        
        # Decide where the cursor *should* move back to
        if cursor_col > 0:
            cursor_col -= 1
        elif cursor_row > 0:
            # Move to end of previous line
            cursor_row -= 1
            cursor_col = SCREEN_CHAR_WIDTH - 1
            # Skip back over any trailing spaces on the previous line (optional refinement)
            while cursor_col > 0 and screen_buffer[cursor_row][cursor_col] == ' ':
                 cursor_col -= 1
            # If we landed on a space, move one more so backspace clears it
            # Or handle case where entire previous line was spaces - land at col 0
            if screen_buffer[cursor_row][cursor_col] == ' ' and cursor_col < SCREEN_CHAR_WIDTH - 1:
                 pass # Landed on the last non-space char or col 0
            elif cursor_col < SCREEN_CHAR_WIDTH - 1:
                cursor_col += 1 # If last char wasn't space, cursor goes after it
        
        # Check if the target position is part of the prompt on the first line
        is_prompt_area = (cursor_row == 0 and cursor_col < len(PROMPT))

        # Only erase if we actually moved and it's not the prompt area
        if (cursor_col != original_cursor_col or cursor_row != original_cursor_row) and not is_prompt_area:
            screen_buffer[cursor_row][cursor_col] = ' ' # Erase character in buffer
            redraw_needed = True
        else: # Didn't move or tried to delete prompt, revert cursor position
            cursor_col = original_cursor_col
            cursor_row = original_cursor_row
            
    # --- Enter --- 
    elif key_code in ENTER_KEY_CODES:
        # Extract command from current line (excluding prompt if on row 0)
        start_col = len(PROMPT) if cursor_row == 0 else 0
        # Command needs to be extracted *before* scrolling
        # Find current line based on cursor_row before potential modification
        command = "".join(screen_buffer[cursor_row][start_col:]).rstrip()
        print(f"\nCommand: {command}") # Process the command here

        # Scroll buffer content up
        screen_buffer.pop(0)
        screen_buffer.append([' ' for _ in range(SCREEN_CHAR_WIDTH)])
        # Always place cursor at start of new bottom line after Enter
        cursor_row = SCREEN_CHAR_HEIGHT - 1 
        cursor_col = 0
        
        # Draw prompt on the new line in the buffer
        for i, char in enumerate(PROMPT):
            if i < SCREEN_CHAR_WIDTH:
                screen_buffer[cursor_row][i] = char
        cursor_col = len(PROMPT) # Position cursor after prompt
        redraw_needed = True
        
    # --- Arrow Up --- 
    elif key_code == ARROW_UP:
        if cursor_row > 0:
            cursor_row -= 1
            # Optional: Adjust cursor_col if new line is shorter?
            # current_line_len = len("".join(screen_buffer[cursor_row]).rstrip())
            # if cursor_col >= current_line_len:
            #     cursor_col = current_line_len
            redraw_needed = True
            
    # --- Arrow Down --- 
    elif key_code == ARROW_DOWN:
        if cursor_row < SCREEN_CHAR_HEIGHT - 1:
            cursor_row += 1
            # Optional: Adjust cursor_col if new line is shorter?
            # current_line_len = len("".join(screen_buffer[cursor_row]).rstrip())
            # if cursor_col >= current_line_len:
            #     cursor_col = current_line_len
            redraw_needed = True

    # Redraw the screen if anything changed
    if redraw_needed:
        redraw_screen(display, screen_buffer, cursor_col, cursor_row)

# Main loop
try:
    if DEBUG_MODE:
        print("Keyboard debugging mode: ON")
    
    while True:
        # Scan the keyboard (this updates the internal buffer)
        if kbd:
            kbd.scan_keyboard()
            
            # Check if there's a key available
            if kbd.has_key():
                key = kbd.get_key()
                if key is not None:
                    handle_key(key)
        
        # Small delay to prevent busy-waiting
        time.sleep(0.01)  # 10ms delay
        
except KeyboardInterrupt:
    print("\nProgram terminated by user")