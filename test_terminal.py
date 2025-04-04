# test_terminal.py - Terminal Test Script
from display.ili9488 import Display
from shell.terminal import Terminal
import machine
import time

def test_terminal():
    # Initialize display
    spi_bus = 0
    cs_pin = 9
    dc_pin = 8
    rst_pin = 12
    bl_pin = 13
    sck_pin = 2
    mosi_pin = 3
    
    display = Display(spi_bus, cs_pin, dc_pin, rst_pin, bl_pin, sck_pin, mosi_pin)
    terminal = Terminal(display)
    
    # Test basic input
    print("Testing basic input...")
    test_string = "Hello, World!"
    for char in test_string:
        terminal.handle_char(char)
        time.sleep_ms(100)  # Slow down for visibility
        
    terminal.handle_char('\n')
    time.sleep_ms(500)
    
    # Test scrolling
    print("Testing scrolling...")
    for i in range(40):
        line = f"Line {i+1}: Testing scroll behavior"
        for char in line:
            terminal.handle_char(char)
            time.sleep_ms(50)
        terminal.handle_char('\n')
        time.sleep_ms(100)
        
    # Test scroll reset
    print("Testing scroll reset...")
    for i in range(10):
        line = f"After reset line {i+1}"
        for char in line:
            terminal.handle_char(char)
            time.sleep_ms(50)
        terminal.handle_char('\n')
        time.sleep_ms(100)
        
    print("Test complete!")

if __name__ == "__main__":
    test_terminal() 