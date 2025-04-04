# main.py - Refactored main application using Display, Graphics, and PicoCalc Keyboard

import time
from ili9488 import Display # Import the Display class
import graphics           # Import the graphics module
import font               # Import font dimensions
import keyboard          # Import the new PicoCalc keyboard driver

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
TERM_COLS = display.width // font.FONT_WIDTH
TERM_ROWS = display.height // font.FONT_HEIGHT
line_buffer = ""
cursor_col = 0
cursor_row = 0
PROMPT = "> " # Define the prompt string

# Clear the screen initially
graphics.clear_screen(display, COLOR_BLACK)

# Draw the initial prompt
graphics.draw_string(display, PROMPT, 
                     cursor_col * font.FONT_WIDTH, 
                     cursor_row * font.FONT_HEIGHT, 
                     COLOR_WHITE, COLOR_BLACK)
cursor_col = len(PROMPT) # Update cursor position after drawing prompt

print(f"Terminal Size: {TERM_COLS}x{TERM_ROWS}")
print("Shell initialized. Waiting for input...")

# Define the valid Enter key codes (CR/LF is all we need now with corrected key handling)
ENTER_KEY_CODES = [13]  # CR only since we standardized on CR in keyboard.py

def handle_key(key_code):
    """Handle a key code from the keyboard"""
    global line_buffer, cursor_col, cursor_row
    
    # Debug output for all key presses if DEBUG_MODE is on
    if DEBUG_MODE:
        key_name = "Unknown"
        if 32 <= key_code <= 126:
            key_name = f"'{chr(key_code)}'"
        elif key_code == 8 or key_code == 133:
            key_name = "Backspace"
        elif key_code in ENTER_KEY_CODES:
            key_name = "Enter"
        
        status = kbd.last_raw_status if kbd else None
        status_str = f"0x{status:04X}" if status is not None else "None"
        print(f"DEBUG: Key detected - Code: 0x{key_code:02X} ({key_code}) Name: {key_name} Raw Status: {status_str}")
    
    # Convert key code to character if it's a printable ASCII code
    if 32 <= key_code <= 126:  # Printable ASCII range
        if cursor_col < TERM_COLS:
            char = chr(key_code)
            # Draw the character on the display
            graphics.draw_char(display, char, 
                              cursor_col * font.FONT_WIDTH, 
                              cursor_row * font.FONT_HEIGHT, 
                              COLOR_WHITE, COLOR_BLACK)
            # Add character to buffer
            line_buffer += char
            # Advance cursor
            cursor_col += 1
            # Print the character (simple output mode)
            if not DEBUG_MODE:
                print(f"Key: '{char}'", end=" ")
            
    elif key_code == 133 or key_code == 8:  # Backspace (DEL=133 or ASCII backspace=8)
        if cursor_col > len(PROMPT):  # Only allow backspace after the prompt
            # Move cursor back
            cursor_col -= 1
            # Draw a space to overwrite the character on screen
            graphics.draw_char(display, ' ', 
                              cursor_col * font.FONT_WIDTH, 
                              cursor_row * font.FONT_HEIGHT, 
                              COLOR_WHITE, COLOR_BLACK)
            # Remove character from buffer
            line_buffer = line_buffer[:-1]
            if not DEBUG_MODE:
                print("Backspace", end=" ")
            
    elif key_code in ENTER_KEY_CODES:  # Enter (standardized on CR=13)
        # Process the command 
        print(f"\nCommand: {line_buffer}")
        
        # Clear line and advance cursor
        line_buffer = ""  # Clear the buffer
        cursor_row = (cursor_row + 1) % TERM_ROWS  # Wrap around if needed
        cursor_col = 0  # Reset to start of line
        
        # Draw new prompt
        graphics.draw_string(display, PROMPT, 
                            cursor_col * font.FONT_WIDTH, 
                            cursor_row * font.FONT_HEIGHT, 
                            COLOR_WHITE, COLOR_BLACK)
        cursor_col = len(PROMPT)
        if not DEBUG_MODE:
            print("Enter pressed")

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