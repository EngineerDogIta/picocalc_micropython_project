import machine
import time
# import ili9488  # Requires ili9488.py library on the Pico
from lib.ili9486 import ILI9486 as SSD # Use Peter Hinch's driver from lib/

# Check for color inversion needed by some ILI9488
# SSD.COLOR_INVERT = 0xFFFF # Try enabling color inversion - Disabled based on PicoMite patch analysis
SSD.COLOR_INVERT = 0 # Explicitly disable inversion

# Pin definitions (Mapping 2 - PicoCalc ILI9488)
spi_sck = machine.Pin(10)
spi_mosi = machine.Pin(11)
# MISO is not typically used for display-only SPI
spi_cs = machine.Pin(13, machine.Pin.OUT)
spi_dc = machine.Pin(14, machine.Pin.OUT)
spi_rst = machine.Pin(15, machine.Pin.OUT)
# spi_bl = machine.Pin(12, machine.Pin.OUT) # Removed: PicoMite patch indicates I2C backlight control

# Initialize SPI
# Using SPI(1) as it commonly uses GP10/GP11 on Pico
# Baudrate can be adjusted, 40MHz is often stable for ILI9488. Start lower if issues occur.
# Peter Hinch's driver might prefer lower default speeds, let's try 30MHz based on docs.
# Let's try an even lower speed to see if it stabilizes
# spi = machine.SPI(1, baudrate=30_000_000, sck=spi_sck, mosi=spi_mosi)
spi = machine.SPI(1, baudrate=10_000_000, sck=spi_sck, mosi=spi_mosi) # Try 10MHz

# Initialize Backlight - Removed: Assuming I2C control based on patch
# spi_bl.value(1) # Turn backlight on (set high)
# print("Backlight ON")

# Initialize Display Driver
# PicoCalc resolution is 480x320
# display = ili9488.ILI9488(spi, cs=spi_cs, dc=spi_dc, rst=spi_rst, width=480, height=320)
display = SSD(spi, cs=spi_cs, dc=spi_dc, rst=spi_rst, width=480, height=320)
print("Display driver initialized")

# Initialize the display hardware
# This driver doesn't explicitly require a separate .init() call after instantiation
# display.init()
# print("Display hardware initialized")

# --- Basic Test ---
print("Starting display test...")

# Define some 16-bit RGB565 colors (used by many drivers)
# Adjusted for BGR order based on PicoMite patch (Option.BGR = 1)
COLOR_BLACK = 0x0000
# COLOR_RED = 0xF800   # Original RGB Red
# COLOR_BLUE = 0x001F  # Original RGB Blue
COLOR_RED = 0x001F     # BGR Red (Looks Blue in RGB565)
COLOR_GREEN = 0x07E0   # BGR Green (Same as RGB565)
COLOR_BLUE = 0xF800    # BGR Blue (Looks Red in RGB565)
# COLOR_YELLOW = 0xFFE0 # Original RGB Yellow (R+G)
COLOR_YELLOW = 0x07FF  # BGR Yellow (G+B)
COLOR_WHITE = 0xFFFF

# Fill screen RED only and stop
# We want to display RED on the screen, which in BGR mode requires the BLUE constant (0xF800)
print("Fill Red (using BGR constant for Blue)")
# display.fill(COLOR_RED) # This would show Blue on a BGR screen
display.fill(COLOR_BLUE) # Use the constant that contains the Red component for BGR
print("Test complete (filled screen with 0xF800). Script finished.")

# Keep the rest of the test commented out for now
# time.sleep(1)
# 
# # Fill screen GREEN
# print("Fill Green")
# # display.fill(ili9488.color565(0, 255, 0))
# display.fill(COLOR_GREEN)
# time.sleep(1)
# 
# # Fill screen BLUE
# print("Fill Blue")
# # display.fill(ili9488.color565(0, 0, 255))
# display.fill(COLOR_BLUE)
# time.sleep(1)
# 
# # Clear screen (fill BLACK)
# print("Fill Black (Clear)")
# # display.fill(0)
# display.fill(COLOR_BLACK)
# time.sleep(0.5)
# 
# # Draw a yellow rectangle
# # Note: fill_rect might not be implemented exactly the same way or at all
# # in this driver without the full nano-gui framework.
# # Let's try filling the whole screen yellow instead for a simpler test.
# print("Fill Yellow")
# # display.fill_rect(10, 10, 200, 100, ili9488.color565(255, 255, 0))
# display.fill(COLOR_YELLOW)
# time.sleep(2)
# 
# print("Display test complete.")
# 
# # Optional: Turn off backlight at the end
# # spi_bl.value(0)
# # print("Backlight OFF")
