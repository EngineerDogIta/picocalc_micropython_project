# main.py - Refactored main application using Display, Graphics, and IRQ Keyboard

import time
from ili9488 import Display # Import the Display class
import graphics           # Import the graphics module
import font               # Import font dimensions
from kbd_irq import KeyboardIRQ  # Import the new IRQ-based keyboard driver

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

print("--- Initializing Display ---")
# Initialize the display driver
# The Display class constructor handles pin/SPI setup, reset, and init sequence.
display = Display(spi_bus=SPI_BUS,
                  cs_pin=LCD_CS_PIN, dc_pin=LCD_DC_PIN, rst_pin=LCD_RST_PIN,
                  bl_pin=LCD_BL_PIN, sck_pin=LCD_SCK_PIN, mosi_pin=LCD_MOSI_PIN,
                  width=LCD_WIDTH, height=LCD_HEIGHT, baudrate=SPI_BAUDRATE)

print("--- Initializing IRQ Keyboard ---")
# Initialize the IRQ-based keyboard driver
keyboard = KeyboardIRQ()

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

# Define printable characters for shell
printable_chars = '1234567890*#.+ '

# Keyboard callback function
def handle_key_press(key):
    """Handle key press events from the keyboard"""
    global line_buffer, cursor_col, cursor_row
    
    # --- Shell Input Handling --- 
    if key in printable_chars and cursor_col < TERM_COLS:
        # Draw the character on the display
        graphics.draw_char(display, key, 
                          cursor_col * font.FONT_WIDTH, 
                          cursor_row * font.FONT_HEIGHT, 
                          COLOR_WHITE, COLOR_BLACK)
        # Add character to buffer
        line_buffer += key
        # Advance cursor
        cursor_col += 1
    elif key == 'BSP': # Backspace
        if cursor_col > len(PROMPT): # Only allow backspace after the prompt
            # Move cursor back
            cursor_col -= 1
            # Draw a space to overwrite the character on screen
            graphics.draw_char(display, ' ', 
                              cursor_col * font.FONT_WIDTH, 
                              cursor_row * font.FONT_HEIGHT, 
                              COLOR_WHITE, COLOR_BLACK)
            # Remove character from buffer
            line_buffer = line_buffer[:-1]
    elif key == 'ENT':  # Enter
        # --- Process Command (Placeholder) ---
        print(f"\nCommand received: {line_buffer}") 
        # TODO: Implement actual command parsing/execution later
        
        # --- Clear Line and Advance Cursor ---
        line_buffer = "" # Clear the buffer for the next command
        # Advance to the next row, wrapping around if necessary
        cursor_row = (cursor_row + 1) % TERM_ROWS
        cursor_col = 0 # Reset column to the beginning of the line
        
        # --- Draw New Prompt ---
        graphics.draw_string(display, PROMPT, 
                            cursor_col * font.FONT_WIDTH, 
                            cursor_row * font.FONT_HEIGHT, 
                            COLOR_WHITE, COLOR_BLACK)
        cursor_col = len(PROMPT) # Update cursor position after drawing prompt

# Set the keyboard callback
keyboard.set_callback(handle_key_press)

# Main loop - just keep the program running
try:
    while True:
        # The keyboard driver handles key events via interrupts and callbacks
        # We just need to keep the program running
        time.sleep(0.1)
except KeyboardInterrupt:
    print("\nProgram terminated by user")