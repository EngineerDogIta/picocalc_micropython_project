# main.py - Basic ILI9488 Initialization and Screen Fill for Pico
# Fills the screen with Cyan color using RGB565 format.

import machine
import time
import ustruct # For packing color data

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

# --- Pin Initialization ---
# Initialize GPIO pins for controlling the display
spi_cs = machine.Pin(LCD_CS_PIN, machine.Pin.OUT, value=1) # CS inactive (high)
spi_dc = machine.Pin(LCD_DC_PIN, machine.Pin.OUT)
spi_rst = machine.Pin(LCD_RST_PIN, machine.Pin.OUT)
lcd_bl = machine.Pin(LCD_BL_PIN, machine.Pin.OUT)
print("GPIO pins initialized.")

# --- Backlight ON ---
# Turn on the display backlight
print(f"Turning Backlight ON (GP{LCD_BL_PIN})...")
lcd_bl.value(1)

# --- SPI Initialization ---
# Configure the SPI peripheral
spi = machine.SPI(SPI_BUS, baudrate=SPI_BAUDRATE, sck=machine.Pin(LCD_SCK_PIN), mosi=machine.Pin(LCD_MOSI_PIN), polarity=0, phase=0)
print(f"SPI(bus={SPI_BUS}, baudrate={SPI_BAUDRATE}, sck={LCD_SCK_PIN}, mosi={LCD_MOSI_PIN}) initialized.")

# --- Low-level SPI Communication Functions ---
def _wcmd(cmd_byte):
    """Send a command byte to the display controller."""
    spi_dc.value(0) # Command mode
    spi_cs.value(0) # Select chip
    spi.write(bytes([cmd_byte]))
    spi_cs.value(1) # Deselect chip

def _wdata(data_bytes):
    """Send a data byte or sequence of bytes to the display controller."""
    spi_dc.value(1) # Data mode
    spi_cs.value(0) # Select chip
    # Ensure data is bytes
    spi.write(data_bytes if isinstance(data_bytes, bytes) else bytes([data_bytes]))
    spi_cs.value(1) # Deselect chip

def _wcd(cmd_byte, data_bytes):
    """Send a command byte followed by data byte(s)."""
    _wcmd(cmd_byte)
    _wdata(data_bytes)

# --- Hardware Reset ---
# Reset the display controller
print("Performing hardware reset...")
spi_rst.value(0)
time.sleep(0.05) # 50ms reset low time
spi_rst.value(1)
time.sleep(0.15) # 150ms delay after reset

# --- ILI9488 Initialization Sequence ---
# Send initialization commands based on typical ILI9488 configuration
# Configured for 320x320 resolution, 16-bit RGB565 color, Portrait mode.
print("Sending ILI9488 Initialization Sequence...")

# Key Settings
_wcd(0x36, 0x40) # MADCTL: Memory Access Control - Portrait (MY=0,MX=1,MV=0), RGB color order
_wcd(0x3A, 0x55) # COLMOD: Pixel Format Set - 16 bits/pixel (RGB565)

# Interface & Display Control
_wcd(0xB0, 0x80) # Interface Mode Control - Use default settings
_wcd(0xB4, 0x00) # Display Inversion Control - Column Inversion (default)
_wcd(0xB6, bytes([0x80, 0x02, 0x3B])) # Display Function Control - Use common values
_wcd(0xB7, 0xC6) # Entry Mode Set - Use common values, deep standby OFF

# Power Controls
_wcd(0xC0, bytes([0x10, 0x10])) # Power Control 1 - Vreg voltage settings (common)
_wcd(0xC1, 0x41)               # Power Control 2 - VGH/VGL voltage settings (common)
_wcd(0xC5, bytes([0x00, 0x18])) # VCOM Control 1 - VCOM voltage settings (common)

# Gamma Settings
# Positive Gamma Correction
_wcd(0xE0, bytes([0x0F, 0x1F, 0x1C, 0x0C, 0x0F, 0x08, 0x48, 0x98, 0x37, 0x0A, 0x13, 0x04, 0x11, 0x0D, 0x00]))
# Negative Gamma Correction
_wcd(0xE1, bytes([0x0F, 0x32, 0x2E, 0x0B, 0x0D, 0x05, 0x47, 0x75, 0x37, 0x06, 0x10, 0x03, 0x24, 0x20, 0x00]))

# Tearing Effect Line OFF
_wcd(0x35, 0x00)

# Exit Sleep Mode
_wcmd(0x11)      # SLPOUT: Sleep Out
time.sleep(0.12) # 120ms delay required after SLPOUT

# Turn Display ON
_wcmd(0x29)      # DISPON: Display ON
time.sleep(0.02) # 20ms delay after DISPON

print("Initialization sequence sent.")

# --- Test: Fill Screen with Cyan (RGB565) ---

# Define Cyan in RGB565 format
# R=0 (00000), G=63 (111111), B=31 (11111)
# Packed: 00000 111111 11111 = 0x07FF
COLOR_CYAN_RGB565 = 0x07FF

# Pack the color into 2 bytes (Big Endian for SPI)
COLOR_TO_FILL_BYTES = ustruct.pack(">H", COLOR_CYAN_RGB565)

# Set drawing window to the full screen area
print("Setting drawing window to full screen (0,0 to 319,319)...")
_wcmd(0x2A) # CASET (Column Address Set)
_wdata(ustruct.pack(">HH", 0, LCD_WIDTH - 1)) # X start = 0, X end = 319

_wcmd(0x2B) # RASET (Row Address Set)
_wdata(ustruct.pack(">HH", 0, LCD_HEIGHT - 1)) # Y start = 0, Y end = 319

# Prepare for Memory Write command
print(f"Preparing to fill screen with Cyan (RGB565: {hex(COLOR_CYAN_RGB565)}, Bytes: {COLOR_TO_FILL_BYTES.hex()})...")
_wcmd(0x2C) # RAMWR (Memory Write)

# Start sending pixel data
print("Writing pixel data...")
spi_dc.value(1) # Data mode
spi_cs.value(0) # Chip select active

# Use a buffer for potentially faster SPI transfers
buffer_size_pixels = 128 # Number of pixels per buffer write
buffer_size_bytes = buffer_size_pixels * 2 # Bytes per buffer (2 bytes/pixel)
pixel_buffer = bytearray(buffer_size_bytes)
# Fill the buffer with the target color
for i in range(0, buffer_size_bytes, 2):
    pixel_buffer[i:i+2] = COLOR_TO_FILL_BYTES # Fill with 2-byte color

total_pixels = LCD_WIDTH * LCD_HEIGHT
pixels_sent = 0
# Loop sending the buffer until the screen is filled
while pixels_sent < total_pixels:
    # Calculate how many pixels to send in this chunk
    pixels_to_send = min(buffer_size_pixels, total_pixels - pixels_sent)
    bytes_to_send = pixels_to_send * 2
    # Send the appropriate portion of the buffer
    spi.write(pixel_buffer[:bytes_to_send])
    pixels_sent += pixels_to_send

# Deselect the chip after writing
spi_cs.value(1) # Chip select inactive
print("Screen fill complete.")

print("--- Script Finished ---")