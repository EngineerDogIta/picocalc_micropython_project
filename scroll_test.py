# scroll_test.py - Test Basic Drawing and Software Scrolling
import time
import graphics # Assuming graphics.py contains necessary drawing functions
import font     # For character dimensions
from ili9488 import Display # Import the Display class

# Display Configuration (Ensure these match your hardware setup)
LCD_CS_PIN = 13
LCD_DC_PIN = 14
LCD_RST_PIN = 15
LCD_SCK_PIN = 10
LCD_MOSI_PIN = 11
LCD_BL_PIN = 12
SPI_BUS = 1 # Or 0, depending on your wiring
SPI_BAUDRATE = 20_000_000  # Start conservative

# Screen and Font Dimensions
LCD_WIDTH = 320
LCD_HEIGHT = 320
CHAR_WIDTH_PX = font.FONT_WIDTH
CHAR_HEIGHT_PX = font.FONT_HEIGHT
SCREEN_CHAR_HEIGHT = LCD_HEIGHT // CHAR_HEIGHT_PX # Number of text lines visible
SCREEN_CHAR_WIDTH = LCD_WIDTH // CHAR_WIDTH_PX # Number of characters per line

# Colors
COLOR_BLACK = 0x0000
COLOR_WHITE = 0xFFFF
COLOR_RED = 0xF800

# Helper function to pad strings (replacement for ljust)
def pad_string(text, width):
    """Pad a string with spaces to the given width (MicroPython compatible)"""
    return text + " " * (width - len(text))

def test_software_scroll():
    """Tests drawing lines and simulates scrolling using full redraws."""
    print("--- Initializing Display ---")
    display = Display(spi_bus=SPI_BUS,
                     cs_pin=LCD_CS_PIN, dc_pin=LCD_DC_PIN, rst_pin=LCD_RST_PIN,
                     bl_pin=LCD_BL_PIN, sck_pin=LCD_SCK_PIN, mosi_pin=LCD_MOSI_PIN,
                     width=LCD_WIDTH, height=LCD_HEIGHT,
                     baudrate=SPI_BAUDRATE)

    # --- 1. Initial Screen Fill --- 
    print(f"--- Filling screen with initial {SCREEN_CHAR_HEIGHT} lines ---")
    graphics.clear_screen(display, COLOR_BLACK)
    
    # Create initial screen buffer
    screen_buffer = []
    for i in range(SCREEN_CHAR_HEIGHT):
        line_text = f"Line {i}"
        # Pad to fill screen width (using our compatible function)
        line_text = pad_string(line_text, SCREEN_CHAR_WIDTH)
        screen_buffer.append(list(line_text))
    
    # Draw entire screen in one operation using new batch method
    graphics.draw_rows(display, screen_buffer, 0, SCREEN_CHAR_HEIGHT, COLOR_WHITE, COLOR_BLACK)

    print("Initial screen drawn. Pausing for 3 seconds...")
    time.sleep(3)

    # --- 2. Simulate Adding New Lines with Optimized Scroll --- 
    num_new_lines = 20
    print(f"--- Simulating addition of {num_new_lines} new lines using Optimized Scroll ---")

    for i in range(num_new_lines):
        # Add a new line to the buffer
        new_line_num = SCREEN_CHAR_HEIGHT + i
        new_line_text = f"Line {new_line_num}"
        new_line_text = pad_string(new_line_text, SCREEN_CHAR_WIDTH)
        screen_buffer.append(list(new_line_text))
        
        # Calculate visible range (scrolled)
        first_visible_line = i + 1
        
        print(f"  Scroll Step {i+1}: Showing lines {first_visible_line} to {first_visible_line + SCREEN_CHAR_HEIGHT - 1}")
        
        # Use optimized scroll method
        start_time = time.time()
        graphics.optimized_scroll(display, screen_buffer, first_visible_line, 
                                 SCREEN_CHAR_HEIGHT, COLOR_WHITE, COLOR_BLACK)
        end_time = time.time()
        
        # Calculate and display render time
        render_time_ms = (end_time - start_time) * 1000
        print(f"  Render time: {render_time_ms:.2f}ms")
        
        # Pause to observe
        time.sleep(0.3) # Shorter pause to demonstrate speed improvement

    print("--- Optimized scroll test completed. ---")
    
    # Compare with old method
    print("--- Now comparing with traditional method for reference ---")
    time.sleep(1)
    
    # Revert to initial state
    screen_buffer = screen_buffer[:SCREEN_CHAR_HEIGHT]
    graphics.clear_screen(display, COLOR_BLACK)
    graphics.draw_rows(display, screen_buffer, 0, SCREEN_CHAR_HEIGHT, COLOR_WHITE, COLOR_BLACK)
    time.sleep(1)
    
    # Execute traditional full redraw scrolling (similar to original implementation)
    for i in range(5):  # Only test a few lines to save time
        # Add a new line to the buffer
        new_line_num = SCREEN_CHAR_HEIGHT + i
        new_line_text = f"Traditional Line {new_line_num}"
        new_line_text = pad_string(new_line_text, SCREEN_CHAR_WIDTH)
        screen_buffer.append(list(new_line_text))
        
        # Calculate the range of line numbers to display
        first_visible_line = i + 1
        
        print(f"  Traditional Scroll Step {i+1}")
        
        # Time the traditional redraw method
        start_time = time.time()
        
        # Perform full redraw (traditional method)
        graphics.clear_screen(display, COLOR_BLACK)
        for screen_row in range(SCREEN_CHAR_HEIGHT):
            line_num_to_draw = first_visible_line + screen_row
            if line_num_to_draw < len(screen_buffer):
                line_text = ''.join(screen_buffer[line_num_to_draw])
                y_pos = screen_row * CHAR_HEIGHT_PX
                graphics.draw_string(display, line_text, 0, y_pos, COLOR_WHITE, COLOR_BLACK)
        
        end_time = time.time()
        
        # Calculate and display render time
        render_time_ms = (end_time - start_time) * 1000
        print(f"  Traditional render time: {render_time_ms:.2f}ms")
        
        # Pause to observe
        time.sleep(0.5)
    
    print("--- Comparison completed. ---")
    time.sleep(3)

if __name__ == "__main__":
    try:
        test_software_scroll()
    except Exception as e:
        print(f"An error occurred: {e}")
        # Optional: Add cleanup code here if needed
    finally:
        print("Test script finished.")
        # Consider adding display.deinit() or backlight_off() if needed
        pass 