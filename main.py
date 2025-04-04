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

print("--- Setting up Scroll Area ---")
try:
    display.define_scroll_area(0, LCD_HEIGHT, 0) # Top Fixed, Scroll Area, Bottom Fixed
    display.set_scroll_start(0)
    print("Hardware scroll area defined.")
except Exception as e:
    print(f"Error setting up scroll area: {e}")

print("--- Initializing PicoCalc Keyboard ---")
# Initialize the keyboard driver with default I2C settings (I2C1, SDA=GP6, SCL=GP7)
# Rename the instance to avoid conflict with the module name
kbd = keyboard.init()  # This uses the default settings from keyboard.py

print("--- Initializing Shell ---")

# --- Shell Configuration & State ---
screen_buffer = [[' ' for _ in range(SCREEN_CHAR_WIDTH)] for _ in range(SCREEN_CHAR_HEIGHT)]
cursor_col = 0
cursor_row = 0
PROMPT = "> " # Define the prompt string
# line_buffer and current_prompt_row are no longer needed

# --- NEW: Optimized Character Drawing ---
def update_char_display(display, buffer, col, row, current_cursor_col, current_cursor_row):
    """Draws the character at buffer[row][col] to the display,
       inverting colors if it's the cursor position."""
    # Basic bounds check
    if not (0 <= row < SCREEN_CHAR_HEIGHT and 0 <= col < SCREEN_CHAR_WIDTH):
        return 
        
    char = buffer[row][col]
    is_cursor = (row == current_cursor_row and col == current_cursor_col)
    fg = COLOR_BLACK if is_cursor else COLOR_WHITE
    bg = COLOR_WHITE if is_cursor else COLOR_BLACK
    
    graphics.draw_char(display, char, 
                       col * CHAR_WIDTH_PX, 
                       row * CHAR_HEIGHT_PX, 
                       fg, bg)

# --- Modified Redraw Screen ---
def redraw_screen(display, buffer, c_col, c_row):
    """Redraws the entire screen from the buffer, placing cursor.
    NOTE: Full redraw can be slow, optimizations are possible. -> Now uses optimized draw
    """
    # graphics.clear_screen(display, COLOR_BLACK) # Optional: uncomment if flashing is acceptable
    for r in range(SCREEN_CHAR_HEIGHT):
        for c in range(SCREEN_CHAR_WIDTH):
            # Use the new function to draw each character
            update_char_display(display, buffer, c, r, c_col, c_row)

# Clear the physical screen initially
graphics.clear_screen(display, COLOR_BLACK)

# Initialize buffer (already done with spaces)
# Draw the initial prompt into the buffer
for i, char in enumerate(PROMPT):
    if i < SCREEN_CHAR_WIDTH:
        screen_buffer[cursor_row][i] = char
cursor_col = len(PROMPT) # Update cursor position after prompt

# Initial screen draw from buffer
redraw_screen(display, screen_buffer, cursor_col, cursor_row) # Use modified redraw

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

# --- Modified Handle Key ---
def handle_key(key_code):
    """Handle a key code from the keyboard using screen buffer"""
    global cursor_col, cursor_row # screen_buffer is global implicitly
    old_cursor_col, old_cursor_row = cursor_col, cursor_row
    # REMOVED: needs_full_redraw = False (now handled differently)
    needs_partial_update = False # Flag for general partial updates

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
        # Only process if cursor is within bounds (before potential wrap/scroll)
        if 0 <= cursor_row < SCREEN_CHAR_HEIGHT and 0 <= cursor_col < SCREEN_CHAR_WIDTH:
            screen_buffer[cursor_row][cursor_col] = char # Update buffer *before* moving cursor
            cursor_col += 1
            needs_partial_update = True # Update character and potentially old cursor pos
            # Handle line wrap
            if cursor_col >= SCREEN_CHAR_WIDTH:
                cursor_col = 0
                cursor_row += 1
                # Handle screen scroll (This should ideally not trigger here anymore for Enter)
                if cursor_row >= SCREEN_CHAR_HEIGHT:
                    # If Enter caused scroll, it's handled below.
                    # If typing caused scroll (auto-wrap scroll):
                    # Perform scroll similar to Enter, but without command processing/prompt.
                    # 1. Update Software Buffer
                    screen_buffer.pop(0)
                    screen_buffer.append([' ' for _ in range(SCREEN_CHAR_WIDTH)])
                    
                    # 2. Set Cursor Position (already wrapped, just fix row)
                    cursor_row = SCREEN_CHAR_HEIGHT - 1
                    # cursor_col is already 0 from wrap

                    # 3. Perform Hardware Scroll
                    current_scroll_start = display.get_scroll_start()
                    next_scroll_start = (current_scroll_start + CHAR_HEIGHT_PX) % LCD_HEIGHT
                    display.set_scroll_start(next_scroll_start)

                    # 4. DIAGNOSTIC: Use full redraw instead of partial
                    redraw_screen(display, screen_buffer, cursor_col, cursor_row)
                    
                    # No need for further partial update, we redrew the whole screen
                    needs_partial_update = False 
                    
    # --- Backspace --- 
    elif key_code in BACKSPACE_KEYS:
        # Determine if we *can* backspace (not in prompt area on first line)
        can_move_back = (cursor_col > len(PROMPT) or cursor_row > 0)

        if can_move_back:
            # Redraw old cursor position first before moving it
            update_char_display(display, screen_buffer, old_cursor_col, old_cursor_row, -1, -1) 
            
            if cursor_col > 0:
                # Move cursor back
                cursor_col -= 1
                # Erase character in buffer at the new cursor position
                screen_buffer[cursor_row][cursor_col] = ' ' 
                # Redraw the erased character position (now blank)
                update_char_display(display, screen_buffer, cursor_col, cursor_row, -1, -1)
            elif cursor_row > 0:
                # Move cursor to end of previous line (don't erase)
                cursor_row -= 1
                # Find the effective end of the previous line (last non-space char)
                effective_end_col = SCREEN_CHAR_WIDTH - 1
                while effective_end_col >= 0 and screen_buffer[cursor_row][effective_end_col] == ' ':
                    effective_end_col -= 1
                cursor_col = effective_end_col + 1 # Place cursor after last char or at 0
                # Prevent moving cursor into prompt on line 0 if it was empty/all spaces
                if cursor_row == 0 and cursor_col < len(PROMPT):
                     cursor_col = len(PROMPT)
            
            # Redraw the new cursor position
            update_char_display(display, screen_buffer, cursor_col, cursor_row, cursor_col, cursor_row)
            needs_partial_update = False # Handled manually above
            
    # --- Enter --- 
    elif key_code in ENTER_KEY_CODES:
        # Extract command from the line where Enter was pressed (using old_cursor_row)
        start_col = len(PROMPT) if old_cursor_row == 0 else 0
        command = "".join(screen_buffer[old_cursor_row][start_col:]).rstrip() 
        print(f"\nCommand: {command}") # Process the command here

        # Redraw the old cursor position normally before moving
        update_char_display(display, screen_buffer, old_cursor_col, old_cursor_row, -1, -1)

        # Calculate next row and check if scrolling is needed
        next_prompt_row = old_cursor_row + 1
        
        # --- SCROLLING LOGIC --- 
        if next_prompt_row < SCREEN_CHAR_HEIGHT:
            # --- NO SCROLL --- 
            cursor_row = next_prompt_row
            cursor_col = 0
            # Write prompt to software buffer
            for i, char in enumerate(PROMPT):
                if i < SCREEN_CHAR_WIDTH:
                    screen_buffer[cursor_row][i] = char
            cursor_col = len(PROMPT)
            # Draw the new prompt characters normally
            for i, char in enumerate(PROMPT):
                 draw_col = 0 + i
                 if draw_col < SCREEN_CHAR_WIDTH:
                     update_char_display(display, screen_buffer, draw_col, cursor_row, -1, -1)
            # Draw the new cursor
            update_char_display(display, screen_buffer, cursor_col, cursor_row, cursor_col, cursor_row)
            needs_partial_update = False # Handled here

        else:
            # --- HARDWARE SCROLL REQUIRED --- 
            # 1. Update Software Buffer (Keep this)
            screen_buffer.pop(0)
            screen_buffer.append([' ' for _ in range(SCREEN_CHAR_WIDTH)]) # Add new blank line at bottom
            
            # 2. Set Cursor Position (Keep this - cursor now on the new last line)
            cursor_row = SCREEN_CHAR_HEIGHT - 1
            cursor_col = 0
            
            # 3. Write Prompt to software buffer (Keep this - updates the *new* last line)
            for i, char in enumerate(PROMPT):
                if i < SCREEN_CHAR_WIDTH:
                    screen_buffer[cursor_row][i] = char
            cursor_col = len(PROMPT) # Position cursor after prompt on the new last line
            
            # --- Perform Hardware Scroll ---
            # Get current scroll start line (from display driver)
            current_scroll_start = display.get_scroll_start() 
            # Calculate next scroll line (wrapping around total height)
            # Scroll UP by one character height
            next_scroll_start = (current_scroll_start + CHAR_HEIGHT_PX) % LCD_HEIGHT 
            display.set_scroll_start(next_scroll_start)
            
            # --- DIAGNOSTIC: Use full redraw instead of partial ---
            redraw_screen(display, screen_buffer, cursor_col, cursor_row)
            
            # We have manually updated the screen, no further partial update needed
            needs_partial_update = False 
            # REMOVED: needs_full_redraw = True 

    # --- Arrow Up --- 
    elif key_code == ARROW_UP:
        if cursor_row > 0:
            update_char_display(display, screen_buffer, old_cursor_col, old_cursor_row, -1, -1) # Undraw old cursor
            cursor_row -= 1
            # Prevent moving into prompt
            if cursor_row == 0 and cursor_col < len(PROMPT):
                cursor_col = len(PROMPT)
            update_char_display(display, screen_buffer, cursor_col, cursor_row, cursor_col, cursor_row) # Draw new cursor
            needs_partial_update = False # Handled manually

    # --- Arrow Down --- 
    elif key_code == ARROW_DOWN:
        if cursor_row < SCREEN_CHAR_HEIGHT - 1:
            update_char_display(display, screen_buffer, old_cursor_col, old_cursor_row, -1, -1) # Undraw old cursor
            cursor_row += 1
            # Prevent moving into prompt (shouldn't happen when moving down, but safe)
            if cursor_row == 0 and cursor_col < len(PROMPT):
                cursor_col = len(PROMPT)
            update_char_display(display, screen_buffer, cursor_col, cursor_row, cursor_col, cursor_row) # Draw new cursor
            needs_partial_update = False # Handled manually

    # --- Simplified Update Display ---
    # Only needs to handle the case where a printable char was added
    # All other cases now handle their own drawing updates.
    if needs_partial_update:
        # 1. Redraw the old cursor position without inversion 
        update_char_display(display, screen_buffer, old_cursor_col, old_cursor_row, -1, -1) 
        # 2. Redraw the character that was just typed (at old cursor pos)
        update_char_display(display, screen_buffer, old_cursor_col, old_cursor_row, -1, -1) # Draw char normally
        # 3. Redraw the new cursor position with inversion
        update_char_display(display, screen_buffer, cursor_col, cursor_row, cursor_col, cursor_row) 

    # REMOVED Final update block for needs_full_redraw

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
        time.sleep(0.02)  # 20ms delay (Increased slightly)
        
except KeyboardInterrupt:
    print("\nProgram terminated by user")