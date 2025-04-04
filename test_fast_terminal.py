# test_fast_terminal.py - Test script for the optimized FastTerminal
from display.ili9488 import Display
from fast_terminal import FastTerminal

def test_fast_terminal():
    # Initialize display with the same pins as in test_terminal.py
    spi_bus = 0
    cs_pin = 9
    dc_pin = 8
    rst_pin = 12
    bl_pin = 13
    sck_pin = 2
    mosi_pin = 3
    width = 320
    height = 320
    baudrate = 20_000_000  # 20MHz - add baudrate for MicroPython
    
    print("--- Initializing Display ---")
    # MicroPython style: use positional args, including baudrate
    display = Display(spi_bus, cs_pin, dc_pin, rst_pin, bl_pin, sck_pin, mosi_pin, width, height, baudrate)
    
    print("--- Initializing FastTerminal ---")
    terminal = FastTerminal(display)
    
    # Test basic input with timing
    print("Testing basic input...")
    test_string = "Hello, World!"
    
    # time_ms the basic input
    start_time_ms = time_ms.time_ms()
    for char in test_string:
        terminal.handle_char(char)
        time_ms.sleep(0.05)  # Slowed down for visibility
        
    terminal.handle_char('\n')
    elapsed = (time_ms.time_ms() - start_time_ms) * 1000
    print(f"Basic input completed in {elapsed:.2f}ms")
    time_ms.sleep(0.5)
    
    # Test scrolling with timing
    print("Testing optimized scrolling...")
    total_lines = 40
    scroll_start_time_ms = time_ms.time_ms()
    
    for i in range(total_lines):
        line = f"Line {i+1}: Testing optimized hardware scroll"
        line_start = time_ms.time_ms()
        
        for char in line:
            terminal.handle_char(char)
            time_ms.sleep(0.01)  # Faster typing for demonstration
            
        terminal.handle_char('\n')
        
        line_elapsed = (time_ms.time_ms() - line_start) * 1000
        print(f"Line {i+1} completed in {line_elapsed:.2f}ms")
        time_ms.sleep(0.1)  # Brief pause between lines
    
    scroll_elapsed = (time_ms.time_ms() - scroll_start_time_ms) * 1000
    print(f"Scroll test completed in {scroll_elapsed:.2f}ms")
    print(f"Average time_ms per line: {scroll_elapsed / total_lines:.2f}ms")
    
    # Test rapid scrolling (no char-by-char input)
    print("Testing rapid scrolling...")
    
    # Clear terminal
    terminal.clear()
    time_ms.sleep(1)
    
    # Add some content first
    for i in range(5):
        line = f"Initial line {i+1}"
        for char in line:
            terminal.handle_char(char)
        terminal.handle_char('\n')
    
    # Now do rapid scrolling
    rapid_start_time_ms = time_ms.time_ms()
    rapid_lines = 20
    
    for i in range(rapid_lines):
        line = f"Rapid scroll line {i+1}"
        for char in line:
            terminal.handle_char(char)
        terminal.handle_char('\n')
        # No delay between lines for maximum speed test
    
    rapid_elapsed = (time_ms.time_ms() - rapid_start_time_ms) * 1000
    print(f"Rapid scroll test: {rapid_lines} lines in {rapid_elapsed:.2f}ms")
    print(f"Average time_ms per rapid line: {rapid_elapsed / rapid_lines:.2f}ms")
    
    print("Test complete!")

if __name__ == "__main__":
    try:
        test_fast_terminal()
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        print("Test script finished.") 