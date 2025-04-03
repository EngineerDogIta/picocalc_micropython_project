# main.py - Testing ILI9488 initialization based on PicoMite patch

import machine
import time
import ustruct # For packing color data

# --- Configuration ---
LCD_CS_PIN = 13   # Schematic Pin
LCD_DC_PIN = 14   # Schematic Pin
LCD_RST_PIN = 15  # Schematic Pin
LCD_SCK_PIN = 10  # Schematic Pin
LCD_MOSI_PIN = 11 # Schematic Pin
LCD_BL_PIN = 12   # Schematic Pin (Backlight)

LCD_WIDTH = 320  # Schematic Resolution
LCD_HEIGHT = 320 # Schematic Resolution

SPI_BUS = 0 # SPI0 uses GP10/11 as default on Pico if not specified otherwise
SPI_BAUDRATE = 20_000_000 # Keeping reduced speed

# --- I2C Backlight Control (PicoCalc specific - AW9523B) --- REMOVED
# I2C_BUS_ID = 0
# I2C_SDA_PIN = 8
# I2C_SCL_PIN = 9
# AW9523B_ADDR = 0x38
# AW_REG_OUTPUT_P1 = 0x03 # Output Port 1 (Not needed for LED mode setup?)
# AW_REG_CONF_P1 = 0x13   # Configure Port 1 (Direction: 0=OUT, 1=IN)
# AW_REG_LED_MODE_P1 = 0x11 # LED Mode Select Port 1 (0=LED, 1=GPIO)
# AW_REG_DIM_P1_4 = 0x25  # Dimmer for P1.4 (Backlight control pin)

# print(f"Initializing I2C{I2C_BUS_ID} (SDA={I2C_SDA_PIN}, SCL={I2C_SCL_PIN})...")
# try:
#     i2c = machine.I2C(I2C_BUS_ID, sda=machine.Pin(I2C_SDA_PIN), scl=machine.Pin(I2C_SCL_PIN))
#     print("I2C Initialized.")
#     print(f"Configuring AW9523B (addr {hex(AW9523B_ADDR)}) for backlight...")
#     val_conf = 0xEF
#     i2c.writeto_mem(AW9523B_ADDR, AW_REG_CONF_P1, bytes([val_conf]))
#     print(f"  - Wrote {hex(val_conf)} to REG {hex(AW_REG_CONF_P1)} (Configure P1.4 as OUT)")
#     val_dim = 0xFF
#     i2c.writeto_mem(AW9523B_ADDR, AW_REG_DIM_P1_4, bytes([val_dim]))
#     print(f"  - Wrote {hex(val_dim)} to REG {hex(AW_REG_DIM_P1_4)} (Set P1.4 Brightness Max)")
#     print("Backlight configuration sent.")
# except Exception as e:
#     print(f"ERROR during I2C setup/backlight control: {e}")

# --- Pin Initialization ---
spi_cs = machine.Pin(LCD_CS_PIN, machine.Pin.OUT, value=1) # Initialize CS high (inactive)
spi_dc = machine.Pin(LCD_DC_PIN, machine.Pin.OUT)
spi_rst = machine.Pin(LCD_RST_PIN, machine.Pin.OUT)
# SPI pins sck and mosi are configured directly in the SPI constructor
# Backlight Pin
lcd_bl = machine.Pin(LCD_BL_PIN, machine.Pin.OUT)

print("Pins initialized (using schematic values)")

# --- Backlight ON --- (Using direct GPIO control)
print(f"Turning Backlight ON (GP{LCD_BL_PIN})")
lcd_bl.value(1)

# --- SPI Initialization ---
# Standard SPI pins for Pico SPI0 are SCK=18, MOSI=19, MISO=16
# Standard SPI pins for Pico SPI1 are SCK=10, MOSI=11, MISO=8 - SCHEMATIC USES SPI1 PINS!
# Let's use SPI1 based on SCK=10, MOSI=11 from schematic
SPI_BUS = 1
spi = machine.SPI(SPI_BUS, baudrate=SPI_BAUDRATE, sck=machine.Pin(LCD_SCK_PIN), mosi=machine.Pin(LCD_MOSI_PIN), polarity=0, phase=0)
print(f"SPI(bus={SPI_BUS}, baudrate={SPI_BAUDRATE}, sck={LCD_SCK_PIN}, mosi={LCD_MOSI_PIN}) initialized")

# --- Low-level SPI Send Functions ---
def _wcmd(cmd_byte):
    """Send a command byte."""
    spi_dc.value(0)
    spi_cs.value(0)
    spi.write(bytes([cmd_byte]))
    spi_cs.value(1)

def _wdata(data_bytes):
    """Send a data byte or bytes."""
    spi_dc.value(1)
    spi_cs.value(0)
    spi.write(data_bytes if isinstance(data_bytes, bytes) else bytes([data_bytes]))
    spi_cs.value(1)

def _wcd(cmd_byte, data_bytes):
    """Send command then data."""
    _wcmd(cmd_byte)
    _wdata(data_bytes)

# --- Hardware Reset ---
print("Hardware Reset...")
spi_rst.value(0)
time.sleep(0.05) # 50ms
spi_rst.value(1)
time.sleep(0.15) # 150ms delay after reset

# --- PicoMite Patch Initialization Sequence ---
# Based on commands observed in patch diffs and ILI9488 datasheets
print("Sending Simplified ILI9488 Init Sequence (16-bit RGB565, Portrait 320x320, MADCTL=0x40)...")

# Commands from patch (translated to Python bytes)
# _wcd(0xF0, 0xC3) # Command Set Control (?) - Enable Extension Command 2 - REMOVED
# _wcd(0xF0, 0x96) # Command Set Control (?) - Enable Extension Command 3 - REMOVED

# Key Settings - MODIFIED for Portrait RGB
_wcd(0x36, 0x40) # MADCTL: Portrait (MY=0,MX=1,MV=0), RGB=0
_wcd(0x3A, 0x55) # Pixel Format: 16-bit/pixel (RGB565)

# Other commands found in typical ILI9488 init, potentially relevant from patch context
_wcd(0xB0, 0x80) # Interface Mode Control
_wcd(0xB4, 0x00) # Display Inversion Control: Column Inversion (Seems default)
_wcd(0xB6, bytes([0x80, 0x02, 0x3B])) # Display Function Control: Default Clock Div, Scan Cycle=VSYNC, etc. (Using common values)
_wcd(0xB7, 0xC6) # Entry Mode Set: Deep standby OFF, ?? - Kept for now

# Power Controls (Using generic common values now)
_wcd(0xC0, bytes([0x10, 0x10])) # Power Control 1 (Vreg1out, Vreg2out) - Common value
_wcd(0xC1, 0x41)               # Power Control 2 (VGH, VGL) - Common value
_wcd(0xC5, bytes([0x00, 0x18])) # VCOM Control 1 (VCOMH, VCOM L) - Common value

# Gamma Settings (Using common defaults now)
# Positive Gamma Correction
_wcd(0xE0, bytes([0x0F, 0x1F, 0x1C, 0x0C, 0x0F, 0x08, 0x48, 0x98, 0x37, 0x0A, 0x13, 0x04, 0x11, 0x0D, 0x00]))
# Negative Gamma Correction
_wcd(0xE1, bytes([0x0F, 0x32, 0x2E, 0x0B, 0x0D, 0x05, 0x47, 0x75, 0x37, 0x06, 0x10, 0x03, 0x24, 0x20, 0x00]))

# Undocumented/Magic from patch - REMOVED
# _wcd(0xE8, bytes([0x40, 0x8A, 0x00, 0x00, 0x29, 0x19, 0xAA, 0x33])) # Timing control?
# _wcd(0xB9, bytes([0x02, 0xE0])) # Unknown/Magic - Maybe panel specific settings

# Exit Command Set Control? - REMOVED
# _wcd(0xF0, 0x3C) # Command Set Control (?) - Disable Extension Command 3
# _wcd(0xF0, 0x69) # Command Set Control (?) - Disable Extension Command 2

_wcd(0x35, 0x00) # Tearing Effect Line OFF - Kept

_wcmd(0x11)      # Sleep Out (SLPOUT)
time.sleep(0.12) # 120ms delay required

_wcmd(0x29)      # Display ON (DISPON)
time.sleep(0.02) # 20ms delay

# _wcmd(0x21)      # Display Inversion ON (INVON) - REMOVED for standard 16-bit test

print("Initialization sequence sent.")

# --- Test: Fill Screen with Red (RGB565) ---

# Define Red in RGB565 format
# R=31 (11111), G=0 (000000), B=0 (00000)
# Packed: 11111 000000 00000 = 0xF800
COLOR_RED_RGB565 = 0xF800
COLOR_BLACK_RGB565 = 0x0000
COLOR_WHITE_RGB565 = 0xFFFF
COLOR_BLUE_RGB565 = 0x001F # R=0, G=0, B=31 (00000 000000 11111)

# Pack the color into 2 bytes (Big Endian for SPI)
COLOR_TO_FILL_BYTES = ustruct.pack(">H", COLOR_RED_RGB565)
# COLOR_TO_FILL_BYTES = ustruct.pack(">H", COLOR_BLACK_RGB565)
# COLOR_TO_FILL_BYTES = ustruct.pack(">H", COLOR_WHITE_RGB565)
# COLOR_TO_FILL_BYTES = ustruct.pack(">H", COLOR_BLUE_RGB565)

# Define Black (0,0,0) -> inverted = (0xFF, 0xFF, 0xFF) - REMOVED
# INV_COLOR_BLACK_BYTES = bytes([0xFF, 0xFF, 0xFF])
# Define White (0x3F,0x3F,0x3F) -> inverted = (0xC0, 0xC0, 0xC0) - REMOVED
# INV_COLOR_WHITE_BYTES = bytes([0xC0, 0xC0, 0xC0])

# Set drawing window to full screen
print("Setting drawing window...")
_wcmd(0x2A) # CASET (Column Address Set)
_wdata(ustruct.pack(">HH", 0, LCD_WIDTH - 1)) # 0 to 319 (Square)

_wcmd(0x2B) # RASET (Row Address Set)
_wdata(ustruct.pack(">HH", 0, LCD_HEIGHT - 1)) # 0 to 319 (Square)

# Prepare to write pixel data
pixel_bytes_to_fill = COLOR_TO_FILL_BYTES # Use the 2-byte packed color

print(f"Preparing to fill with RGB565 color: {pixel_bytes_to_fill.hex()}")
_wcmd(0x2C) # RAMWR (Memory Write)

# Write pixel data for the whole screen
print("Writing pixel data (this might take a while)...")
spi_dc.value(1) # Data mode
spi_cs.value(0) # Chip select active

# Create a buffer for faster transfer
# Buffer size should be multiple of 2 for 16-bit color
# Let's use a buffer representing a few pixels, e.g., 128 pixels * 2 bytes/pixel
buffer_size_pixels = 128
buffer_size_bytes = buffer_size_pixels * 2
line_buffer = bytearray(buffer_size_bytes)
for i in range(0, buffer_size_bytes, 2):
    line_buffer[i:i+2] = pixel_bytes_to_fill # Fill with 2-byte color

total_pixels = LCD_WIDTH * LCD_HEIGHT
pixels_sent = 0
while pixels_sent < total_pixels:
    pixels_to_send = min(buffer_size_pixels, total_pixels - pixels_sent)
    bytes_to_send = pixels_to_send * 2 # Use 2 bytes per pixel
    spi.write(line_buffer[:bytes_to_send])
    pixels_sent += pixels_to_send
    # Optional progress print
    # if pixels_sent % (LCD_WIDTH * 10) == 0:
    #     print(f"  {pixels_sent}/{total_pixels} pixels written...")


spi_cs.value(1) # Chip select inactive
print("Fill attempt complete.")

print("\n--- Script Finished ---")