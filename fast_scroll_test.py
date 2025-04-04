# fast_scroll_test.py - Test optimized graphics with true hardware scrolling
import time
import graphics_fast as graphics # Use the new optimized graphics
import font     # For character dimensions
from ili9488 import Display # Import the Display class

# Display Configuration
LCD_CS_PIN = 13
LCD_DC_PIN = 14
LCD_RST_PIN = 15
LCD_SCK_PIN = 10
LCD_MOSI_PIN = 11
LCD_BL_PIN = 12
SPI_BUS = 1
SPI_BAUDRATE = 20_000_000  # 20MHz

# Screen and Font Dimensions
LCD_WIDTH = 320
LCD_HEIGHT = 320
CHAR_WIDTH_PX = font.FONT_WIDTH
CHAR_HEIGHT_PX = font.FONT_HEIGHT
SCREEN_CHAR_HEIGHT = LCD_HEIGHT // CHAR_HEIGHT_PX
SCREEN_CHAR_WIDTH = LCD_WIDTH // CHAR_WIDTH_PX

# Colors
COLOR_BLACK = 0x0000
COLOR_WHITE = 0xFFFF
COLOR_RED = 0xF800
COLOR_GREEN = 0x07E0
COLOR_BLUE = 0x001F

# Helper function to pad strings
def pad_string(text, width):
    """Pad a string with spaces to the given width (MicroPython compatible)"""
    return text + " " * (width - len(text))

def test_fast_scroll():
    """Tests drawing and scrolling with the optimized graphics implementation."""
    print("--- Initializing Display ---")
    # Use positional arguments instead of keyword arguments
    display = Display(SPI_BUS, LCD_CS_PIN, LCD_DC_PIN, LCD_RST_PIN, 
                     LCD_BL_PIN, LCD_SCK_PIN, LCD_MOSI_PIN,
                     LCD_WIDTH, LCD_HEIGHT, SPI_BAUDRATE)

    # Initialize the FastScreen directly - MicroPython style
    display._fast_screen = graphics.FastScreen(display)
    screen = display._fast_screen
    
    # --- 1. Initial Screen Fill --- 
    print(f"--- Filling screen with initial {SCREEN_CHAR_HEIGHT} lines ---")
    screen.clear_screen(COLOR_BLACK)
    
    # Create initial screen buffer
    screen_buffer = []
    for i in range(SCREEN_CHAR_HEIGHT):
        line_text = f"Line {i}"
        # Pad to fill screen width
        line_text = pad_string(line_text, SCREEN_CHAR_WIDTH)
        screen_buffer.append(list(line_text))
    
    # Draw initial screen content
    start_time = time.time()
    screen.update_screen_buffer(screen_buffer, 0, SCREEN_CHAR_HEIGHT, COLOR_WHITE, COLOR_BLACK)
    elapsed = (time.time() - start_time) * 1000
    print(f"Initial screen drawn in {elapsed:.2f}ms")
    
    time.sleep(2)

    # --- 2. Hardware Scrolling Test --- 
    num_new_lines = 20
    print(f"--- Testing Hardware Scrolling for {num_new_lines} lines ---")

    for i in range(num_new_lines):
        # Add a new line to the buffer
        new_line_num = SCREEN_CHAR_HEIGHT + i
        new_line_text = f"Line {new_line_num}"
        new_line_text = pad_string(new_line_text, SCREEN_CHAR_WIDTH)
        screen_buffer.append(list(new_line_text))
        
        print(f"  Scroll Step {i+1}")
        
        # Time the hardware scroll
        start_time = time.time()
        
        # Scroll up one line
        screen.scroll_up(1)
        
        # Update just the new line at the bottom
        first_visible_line = i + 1
        bottom_row = SCREEN_CHAR_HEIGHT - 1
        buffer_row = first_visible_line + bottom_row
        
        # Draw the new line
        screen.draw_row(screen_buffer[buffer_row], bottom_row, COLOR_WHITE, COLOR_BLACK)
        
        # Calculate and display render time
        elapsed = (time.time() - start_time) * 1000
        print(f"  Hardware scroll render time: {elapsed:.2f}ms")
        
        # Shorter pause to show the speed
        time.sleep(0.2)

    # --- 3. Text Color and Mixed Content Test ---
    print("--- Testing different colors and mixed content ---")
    
    # Clear screen and prepare for color test
    screen.clear_screen(COLOR_BLACK)
    time.sleep(1)
    
    # Draw text in different colors
    colors = [COLOR_RED, COLOR_GREEN, COLOR_BLUE, COLOR_WHITE]
    for i, color in enumerate(colors):
        row = i * 2
        text = f"Color text {i+1} (RGB565: 0x{color:04X})"
        text = pad_string(text, SCREEN_CHAR_WIDTH)
        screen.draw_text_at(text, 0, row, color, COLOR_BLACK)
        
    time.sleep(2)
    
    # --- 4. Speed Comparison ---
    print("--- Comparing speeds for different operations ---")
    
    # Test character-by-character drawing
    start_time = time.time()
    for col in range(SCREEN_CHAR_WIDTH):
        screen.draw_char_at('X', col, 10, COLOR_WHITE, COLOR_BLACK)
    char_by_char_time = (time.time() - start_time) * 1000
    print(f"Character-by-character: {char_by_char_time:.2f}ms")
    
    # Test batch text drawing
    text = "X" * SCREEN_CHAR_WIDTH
    start_time = time.time()
    screen.draw_text_at(text, 0, 12, COLOR_WHITE, COLOR_BLACK)
    batch_time = (time.time() - start_time) * 1000
    print(f"Batch text drawing: {batch_time:.2f}ms")
    
    # Calculate speed improvement
    if char_by_char_time > 0:
        speedup = char_by_char_time / batch_time
        print(f"Speed improvement: {speedup:.1f}x faster")
    
    time.sleep(2)
    
    # --- 5. Rapid Scrolling Test ---
    print("--- Testing rapid scrolling ---")
    
    # Clear and prepare for scrolling test
    screen.clear_screen(COLOR_BLACK)
    
    # Create new test lines
    screen_buffer = []
    for i in range(SCREEN_CHAR_HEIGHT + 30):  # Extra lines for scrolling
        line_text = f"Rapid scroll line {i}"
        line_text = pad_string(line_text, SCREEN_CHAR_WIDTH)
        screen_buffer.append(list(line_text))
    
    # Draw initial screen
    screen.update_screen_buffer(screen_buffer, 0, SCREEN_CHAR_HEIGHT, COLOR_WHITE, COLOR_BLACK)
    time.sleep(1)
    
    # Perform rapid scrolling
    start_time = time.time()
    for i in range(20):
        screen.scroll_up(1)
        bottom_row = SCREEN_CHAR_HEIGHT - 1
        buffer_row = i + 1 + bottom_row
        screen.draw_row(screen_buffer[buffer_row], bottom_row, COLOR_WHITE, COLOR_BLACK)
        time.sleep(0.05)  # Very short delay to show smooth scrolling
    
    total_time = (time.time() - start_time) * 1000
    print(f"Rapid scroll completed in {total_time:.2f}ms, avg {total_time/20:.2f}ms per frame")
    
    print("--- Test completed ---")

if __name__ == "__main__":
    try:
        test_fast_scroll()
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        print("Test script finished.") 