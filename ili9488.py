# pico_project/ili9488.py - ILI9488 Driver for MicroPython
import machine
import time
import ustruct

class Display:
    """
    ILI9488 Display Driver for Raspberry Pi Pico.

    Handles SPI communication, initialization, and basic drawing commands.
    """
    def __init__(self, spi_bus, cs_pin, dc_pin, rst_pin, bl_pin, sck_pin, mosi_pin,
                 width=320, height=320, baudrate=20_000_000):
        self.width = width
        self.height = height
        # Internal state for scrolling
        self._vsa_height = height # Assume full screen scroll initially
        self._current_scroll_line = 0

        self.spi_bus_id = spi_bus
        self.baudrate = baudrate

        # Initialize GPIO pins
        self.cs = machine.Pin(cs_pin, machine.Pin.OUT, value=1) # CS inactive (high)
        self.dc = machine.Pin(dc_pin, machine.Pin.OUT)
        self.rst = machine.Pin(rst_pin, machine.Pin.OUT)
        self.bl = machine.Pin(bl_pin, machine.Pin.OUT)
        self.bl_pin_num = bl_pin # Store the pin number
        self.sck = machine.Pin(sck_pin)
        self.mosi = machine.Pin(mosi_pin)
        print(f"Display pins initialized: CS={cs_pin}, DC={dc_pin}, RST={rst_pin}, BL={bl_pin}")

        # Initialize SPI
        self.spi = machine.SPI(self.spi_bus_id, baudrate=self.baudrate,
                               sck=self.sck, mosi=self.mosi,
                               polarity=0, phase=0)
        print(f"SPI(bus={self.spi_bus_id}, baudrate={self.baudrate}, sck={sck_pin}, mosi={mosi_pin}) initialized.")

        # Perform hardware reset and initialization
        self._hwreset()
        self.init_display()
        self.backlight_on()

    def _wcmd(self, cmd_byte):
        """Send a command byte."""
        self.dc.value(0) # Command mode
        self.cs.value(0) # Select chip
        self.spi.write(bytes([cmd_byte]))
        self.cs.value(1) # Deselect chip

    def _wdata(self, data_bytes):
        """Send a data byte or sequence of bytes."""
        self.dc.value(1) # Data mode
        self.cs.value(0) # Select chip
        self.spi.write(data_bytes if isinstance(data_bytes, bytes) else bytes([data_bytes]))
        self.cs.value(1) # Deselect chip

    def _wcd(self, cmd_byte, data_bytes):
        """Send a command byte followed by data byte(s)."""
        self._wcmd(cmd_byte)
        self._wdata(data_bytes)

    def _hwreset(self):
        """Perform hardware reset."""
        print("Performing hardware reset...")
        self.rst.value(0)
        time.sleep(0.05) # 50ms reset low time
        self.rst.value(1)
        time.sleep(0.15) # 150ms delay after reset

    def init_display(self):
        """Send the initialization sequence to the ILI9488 controller."""
        print("Sending ILI9488 Initialization Sequence...")
        # Key Settings
        self._wcd(0x36, 0x40) # MADCTL: Memory Access Control - Portrait (MY=0,MX=1,MV=0), RGB
        self._wcd(0x3A, 0x55) # COLMOD: Pixel Format Set - 16 bits/pixel (RGB565)

        # Interface & Display Control
        self._wcd(0xB0, 0x80) # Interface Mode Control
        self._wcd(0xB4, 0x00) # Display Inversion Control
        self._wcd(0xB6, bytes([0x80, 0x02, 0x3B])) # Display Function Control
        self._wcd(0xB7, 0xC6) # Entry Mode Set

        # Power Controls
        self._wcd(0xC0, bytes([0x10, 0x10])) # Power Control 1
        self._wcd(0xC1, 0x41)               # Power Control 2
        self._wcd(0xC5, bytes([0x00, 0x18])) # VCOM Control 1

        # Gamma Settings
        self._wcd(0xE0, bytes([0x0F, 0x1F, 0x1C, 0x0C, 0x0F, 0x08, 0x48, 0x98, 0x37, 0x0A, 0x13, 0x04, 0x11, 0x0D, 0x00])) # PGAMCTRL
        self._wcd(0xE1, bytes([0x0F, 0x32, 0x2E, 0x0B, 0x0D, 0x05, 0x47, 0x75, 0x37, 0x06, 0x10, 0x03, 0x24, 0x20, 0x00])) # NGAMCTRL

        # Tearing Effect Line OFF
        self._wcd(0x35, 0x00)

        # Exit Sleep Mode
        self._wcmd(0x11)      # SLPOUT: Sleep Out
        time.sleep(0.12) # 120ms delay required after SLPOUT

        # Turn Display ON
        self._wcmd(0x29)      # DISPON: Display ON
        time.sleep(0.02) # 20ms delay after DISPON

        # Default scroll setup (can be overridden later)
        # self.define_scroll_area(0, self.height, 0) # Let main.py call this
        # self.set_scroll_start(0)

        print("Initialization sequence sent.")

    def backlight_on(self):
        """Turn the backlight on."""
        print(f"Turning Backlight ON (Pin {self.bl_pin_num})...")
        self.bl.value(1)

    def backlight_off(self):
        """Turn the backlight off."""
        print(f"Turning Backlight OFF (Pin {self.bl_pin_num})...")
        self.bl.value(0)

    def set_window(self, x0, y0, x1, y1):
        """Set the drawing window area."""
        # Ensure coordinates are within bounds
        x0 = max(0, min(self.width - 1, x0))
        y0 = max(0, min(self.height - 1, y0))
        x1 = max(0, min(self.width - 1, x1))
        y1 = max(0, min(self.height - 1, y1))

        self._wcmd(0x2A) # CASET (Column Address Set)
        self._wdata(ustruct.pack(">HH", x0, x1))

        self._wcmd(0x2B) # RASET (Row Address Set)
        self._wdata(ustruct.pack(">HH", y0, y1))

    def write_pixels(self, pixel_data):
        """
        Write raw pixel data (bytes) to the display RAM.
        Assumes set_window() has been called previously.
        Sends the RAMWR command before writing data.
        """
        self._wcmd(0x2C) # RAMWR (Memory Write)
        self.dc.value(1) # Data mode
        self.cs.value(0) # Chip select active
        self.spi.write(pixel_data)
        self.cs.value(1) # Chip select inactive

    def fill_rect(self, x, y, w, h, color_rgb565):
        """Fill a rectangular area with a specified color."""
        self.set_window(x, y, x + w - 1, y + h - 1)
        color_bytes = ustruct.pack(">H", color_rgb565)
        num_pixels = w * h
        bytes_per_pixel = 2

        # Prepare RAMWR command
        self._wcmd(0x2C)
        self.dc.value(1) # Data mode
        self.cs.value(0) # Chip select active

        # Use a buffer for potentially faster SPI transfers
        buffer_size_pixels = 128 # Number of pixels per buffer write
        buffer_size_bytes = buffer_size_pixels * bytes_per_pixel
        pixel_buffer = bytearray(buffer_size_bytes)
        # Fill the buffer with the target color
        for i in range(0, buffer_size_bytes, bytes_per_pixel):
            pixel_buffer[i:i+bytes_per_pixel] = color_bytes

        pixels_sent = 0
        while pixels_sent < num_pixels:
            pixels_to_send = min(buffer_size_pixels, num_pixels - pixels_sent)
            bytes_to_send = pixels_to_send * bytes_per_pixel
            # Send the appropriate portion of the buffer
            self.spi.write(pixel_buffer[:bytes_to_send])
            pixels_sent += pixels_to_send

        self.cs.value(1) # Chip select inactive

    def fill_screen(self, color_rgb565):
        """Fill the entire screen with a specified color."""
        print(f"Filling screen with color {hex(color_rgb565)}...")
        self.fill_rect(0, 0, self.width, self.height, color_rgb565)
        print("Screen fill complete.")

    # --- Hardware Scrolling Methods ---
    def define_scroll_area(self, tfa, vsa, bfa):
        """ Defines the Vertical Scrolling Area (TFA+VSA+BFA = screen height)
            tfa: Top Fixed Area lines
            vsa: Vertical Scroll Area lines
            bfa: Bottom Fixed Area lines
        """
        if tfa + vsa + bfa != self.height:
            raise ValueError("Sum of scroll areas must equal screen height")
        print(f"Defining scroll area: TFA={tfa}, VSA={vsa}, BFA={bfa}")
        self._vsa_height = vsa
        data = ustruct.pack(">HHH", tfa, vsa, bfa)
        self._wcd(0x33, data)

    def set_scroll_start(self, line):
        """ Sets the start line for vertical scrolling (VSCSAD) """
        if self._vsa_height <= 0:
            print("Warning: Scroll area not defined or VSA is zero.")
            return
        line = line % self._vsa_height # Wrap around the scroll area
        self._current_scroll_line = line
        # print(f"Setting scroll start line to: {line}") # Debug print
        data = ustruct.pack(">H", line)
        self._wcd(0x37, data)

    def get_scroll_start(self):
        """ Returns the internally tracked current scroll line """
        return self._current_scroll_line 