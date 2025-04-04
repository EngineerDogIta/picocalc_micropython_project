# display/ili9488.py - Improved ILI9488 Display Driver
import machine
import time
import ustruct

class Display:
    """
    ILI9488 Display Driver with improved scroll handling
    """
    def __init__(self, spi_bus, cs_pin, dc_pin, rst_pin, bl_pin, sck_pin, mosi_pin,
                 width=320, height=320, baudrate=20_000_000):
        self.width = width
        self.height = height
        self._vsa_height = height  # Vertical Scroll Area height
        self._current_scroll_line = 0
        
        # Initialize GPIO pins
        self.cs = machine.Pin(cs_pin, machine.Pin.OUT, value=1)
        self.dc = machine.Pin(dc_pin, machine.Pin.OUT)
        self.rst = machine.Pin(rst_pin, machine.Pin.OUT)
        self.bl = machine.Pin(bl_pin, machine.Pin.OUT)
        self.sck = machine.Pin(sck_pin)
        self.mosi = machine.Pin(mosi_pin)
        
        # Initialize SPI
        self.spi = machine.SPI(spi_bus, baudrate=baudrate,
                              sck=self.sck, mosi=self.mosi,
                              polarity=0, phase=0)
        
        # Initialize display
        self.hardware_reset()
        self.init_display()
        self.backlight_on()
        
    def hardware_reset(self):
        """Hardware reset with proper timing"""
        self.rst.value(0)
        time.sleep_ms(50)
        self.rst.value(1)
        time.sleep_ms(150)
        
    def _wcmd(self, cmd_byte):
        """Send a command byte with proper timing"""
        self.dc.value(0)
        self.cs.value(0)
        self.spi.write(bytes([cmd_byte]))
        self.cs.value(1)
        time.sleep_us(1)  # Small delay after command
        
    def _wdata(self, data_bytes):
        """Send data bytes with proper timing"""
        self.dc.value(1)
        self.cs.value(0)
        # Check for bytes OR bytearray before attempting conversion
        if isinstance(data_bytes, (bytes, bytearray)):
            self.spi.write(data_bytes)
        else: # Assume it's a single byte value (int)
            self.spi.write(bytes([data_bytes]))
        self.cs.value(1)
        time.sleep_us(1)  # Small delay after data
        
    def _wcd(self, cmd_byte, data_bytes):
        """Send command and data with proper timing"""
        self._wcmd(cmd_byte)
        self._wdata(data_bytes)
        
    def init_display(self):
        """Initialize display with optimized settings"""
        # Memory Access Control
        self._wcd(0x36, 0x40)  # MADCTL: Portrait mode, RGB
        
        # Pixel Format Set
        self._wcd(0x3A, 0x55)  # 16-bit/pixel
        
        # Display Function Control
        self._wcd(0xB6, bytes([0x80, 0x02, 0x3B]))
        
        # Power Control
        self._wcd(0xC0, bytes([0x10, 0x10]))
        self._wcd(0xC1, 0x41)
        self._wcd(0xC5, bytes([0x00, 0x18]))
        
        # Exit sleep mode
        self._wcmd(0x11)
        time.sleep_ms(120)
        
        # Turn on display
        self._wcmd(0x29)
        time.sleep_ms(20)
        
    def define_scroll_area(self, tfa, vsa, bfa):
        """
        Define scroll area with validation
        tfa: Top Fixed Area
        vsa: Vertical Scroll Area
        bfa: Bottom Fixed Area
        """
        if tfa + vsa + bfa != self.height:
            raise ValueError("Sum of scroll areas must equal screen height")
            
        self._vsa_height = vsa
        data = ustruct.pack(">HHH", tfa, vsa, bfa)
        self._wcd(0x33, data)
        
    def set_scroll_start(self, line):
        """
        Set scroll start line.
        - Validates line number
        - Adds small delay after scroll command
        """
        if not 0 <= line < self._vsa_height:
            # Wrap line number if it exceeds scroll area height
            line = line % self._vsa_height

        data = ustruct.pack(">H", line)
        self._wcd(0x37, data)
        time.sleep_ms(1)  # Small delay after scroll command
        self._current_scroll_line = line
        
    def get_scroll_start(self):
        """Get current hardware scroll position"""
        return self._current_scroll_line
        
    def reset_scroll(self):
        """Reset scroll position to top (line 0)"""
        # Directly set scroll line to 0 without checking count
        data = ustruct.pack(">H", 0)
        self._wcd(0x37, data)
        time.sleep_ms(1) # Small delay after reset
        self._current_scroll_line = 0
        
    def backlight_on(self):
        """Turn on backlight"""
        self.bl.value(1)
        
    def backlight_off(self):
        """Turn off backlight"""
        self.bl.value(0)
        
    def set_window(self, x0, y0, x1, y1):
        """Set drawing window with bounds checking"""
        x0 = max(0, min(self.width - 1, x0))
        y0 = max(0, min(self.height - 1, y0))
        x1 = max(0, min(self.width - 1, x1))
        y1 = max(0, min(self.height - 1, y1))
        
        self._wcmd(0x2A)  # Column Address Set
        self._wdata(ustruct.pack(">HH", x0, x1))
        
        self._wcmd(0x2B)  # Row Address Set
        self._wdata(ustruct.pack(">HH", y0, y1))
        
    def write_pixels(self, pixel_data):
        """Write pixel data with proper command sequence"""
        self._wcmd(0x2C)  # Memory Write
        self._wdata(pixel_data)
        
    def fill_rect(self, x, y, w, h, color_rgb565):
        """Fill rectangle with optimized pixel writing"""
        self.set_window(x, y, x + w - 1, y + h - 1)
        color_bytes = ustruct.pack(">H", color_rgb565)
        
        # Prepare row buffer
        row_buffer = bytearray(w * 2)
        for i in range(0, w * 2, 2):
            row_buffer[i:i+2] = color_bytes
            
        # Write rows
        for _ in range(h):
            self.write_pixels(row_buffer)
            
    def fill_screen(self, color_rgb565):
        """Fill entire screen with color"""
        self.fill_rect(0, 0, self.width, self.height, color_rgb565) 