"""
PicoCalc Keyboard Interface (MicroPython)

This module provides an interface for communicating with the PicoCalc's
custom I2C keyboard controller (Address 0x1F) using MicroPython's
`machine.I2C` module.
"""
import time
import machine

# PicoCalc Keyboard Specifics
PICOCALC_I2C_ADDR = 0x1F
PICOCALC_CMD_READ_STATUS = 0x09

# MMBasic Internal Key Codes (Derived from standard MMBasic & I2C.c switch)
ESC = 0x1B      # 27
BreakKey = 0x03 # 3 (Ctrl+C)
UP = 128
RIGHT = 129
DOWN = 130
LEFT = 131
INSERT = 132
DEL = 133       # Note: DEL not in the I2C.c switch, but standard MMBasic
HOME = 134
END = 135
PUP = 136       # Page Up
PDOWN = 137     # Page Down
F1 = 138
F2 = 139
F3 = 140
F4 = 141
F5 = 142
F6 = 143
F7 = 144
F8 = 145
F9 = 146
F10 = 147
F11 = 148      # Note: F11 not in the I2C.c switch
F12 = 149      # Note: F12 not in the I2C.c switch

# Command buffer for writing
_CMD_BUF = bytearray([PICOCALC_CMD_READ_STATUS])

class PicoCalcKeyboard:
    """
    Handles communication with the PicoCalc's I2C keyboard (address 0x1F)
    using MicroPython's machine.I2C.
    Implements the two-stage read protocol based on C firmware analysis.
    """
    def __init__(self, i2c_id=1, sda_pin=6, scl_pin=7, freq=100000, address=PICOCALC_I2C_ADDR):
        """
        Initialize the I2C connection to the keyboard.

        Args:
            i2c_id (int): The I2C bus ID (0 or 1). Defaults to 1.
            sda_pin (int): The GPIO pin number for SDA. Defaults to 6.
            scl_pin (int): The GPIO pin number for SCL. Defaults to 7.
            freq (int): The I2C frequency (default 100kHz).
            address (int): The I2C address of the keyboard.
        """
        self.i2c_id = i2c_id
        self.address = address
        self.bus = None
        self.ctrl_held = False
        self.key_buffer = [] # Simple list buffer
        self.last_raw_status = None # For debugging

        try:
            # Explicitly define pins with pull-ups using passed pin numbers
            self.sda = machine.Pin(sda_pin, machine.Pin.IN, machine.Pin.PULL_UP)
            self.scl = machine.Pin(scl_pin, machine.Pin.IN, machine.Pin.PULL_UP)
            # Initialize with explicit frequency using passed arguments
            self.bus = machine.I2C(i2c_id, sda=self.sda, scl=self.scl, freq=freq)
            print(f"PicoCalc Keyboard: Initialized machine.I2C({i2c_id}, sda=Pin({sda_pin}, PULL_UP), scl=Pin({scl_pin}, PULL_UP), freq={freq}) for address 0x{self.address:02X}")

            # Optional: Scan to check if device is present?
            devices = self.bus.scan()
            print("Found I2C devices:", [hex(d) for d in devices]) # Print found devices
            if self.address not in devices:
                print(f"Warning: Device 0x{self.address:02X} not found on I2C bus {self.i2c_id}")

        except Exception as e:
            print(f"Error initializing machine.I2C on bus {self.i2c_id}: {e}")
            self.bus = None
            raise # Re-raise the exception

    # No explicit close needed for machine.I2C in this context

    def _write_command(self):
        """
        Sends the command byte (0x09) to initiate status read.
        (Corresponds to CheckI2CKeyboard(..., 0) in C)

        Returns:
            bool: True on success, False on failure.
        """
        if not self.bus:
            return False
        try:
            # Send the single command byte
            self.bus.writeto(self.address, _CMD_BUF)
            # print(f"DEBUG: Wrote command 0x{PICOCALC_CMD_READ_STATUS:02X} to 0x{self.address:02X}") # Debug
            return True
        except OSError as e:
            # Common errors: ENODEV (19) if device NACKs or isn't there
            # print(f"Error writing command to I2C address 0x{self.address:02X}: {e}") # Debug/Verbose Info
            if e.args[0] == 19: # ENODEV / NACK
                 pass # Don't spam console if device just isn't there
            else:
                 print(f"Error writing I2C command: {e}")
            return False
        # except Exception as e: # Catch other potential errors if needed
        #     print(f"Unexpected error writing I2C command: {e}")
        #     return False

    def _read_status(self):
        """
        Reads the 2-byte status word from the keyboard.
        (Corresponds to CheckI2CKeyboard(..., 1) in C)

        Returns:
            int or None: The 16-bit status word, or None on failure.
            The format is (raw_key_code << 8) | event_type.
            Returns 0 if the device returns 0 (no event).
        """
        if not self.bus:
            return None
        try:
            # Read 2 bytes directly from the device
            data = self.bus.readfrom(self.address, 2)
            # print(f"DEBUG: Raw read from 0x{self.address:02X}: {data}") # Debug

            if len(data) == 2:
                # C code implies MSB is key code, LSB is status/type (0x01 for key press)
                # Combine bytes: data[0] is MSB, data[1] is LSB
                status_word = (data[0] << 8) | data[1]
                return status_word
            else:
                # Should not happen with readfrom unless error
                print(f"Error reading status: Expected 2 bytes, got {len(data)}")
                return None

        except OSError as e:
            # print(f"Error reading status from I2C address 0x{self.address:02X}: {e}") # Debug/Verbose info
            if e.args[0] == 19: # ENODEV / NACK
                 pass # Don't spam console
            else:
                 print(f"Error reading I2C status: {e}")
            return None
        # except Exception as e:
        #     print(f"Unexpected error reading I2C status: {e}")
        #     return None

    def _translate_raw_code(self, raw_code):
        """
        Translates the raw key code (high byte of status) into an internal code.
        This needs to replicate the C code's switch statement.

        Args:
            raw_code (int): The 8-bit raw key code.

        Returns:
            int: The translated key code (e.g., ASCII or special constant).
                 Returns the raw_code itself if no translation exists.
        """
        # This map translates the 8-bit raw key identifier from the I2C keyboard
        # (high byte of the status word) into MMBasic internal key codes.
        # Derived from the switch statement in CheckI2CKeyboard in I2C.c
        c_intermediate_map = {
            0xb1: ESC,    # Raw code -> MMBasic ESC (27)
            0x81: F1,     # Raw code -> MMBasic F1 (138)
            0x82: F2,     # Raw code -> MMBasic F2 (139)
            0x83: F3,     # Raw code -> MMBasic F3 (140)
            0x84: F4,     # Raw code -> MMBasic F4 (141)
            0x85: F5,     # Raw code -> MMBasic F5 (142)
            0x86: F6,     # Raw code -> MMBasic F6 (143)
            0x87: F7,     # Raw code -> MMBasic F7 (144)
            0x88: F8,     # Raw code -> MMBasic F8 (145)
            0x89: F9,     # Raw code -> MMBasic F9 (146)
            0x90: F10,    # Raw code -> MMBasic F10 (147)
            0xb5: UP,     # Raw code -> MMBasic UP (128)
            0xb6: DOWN,   # Raw code -> MMBasic DOWN (130)
            0xb7: RIGHT,  # Raw code -> MMBasic RIGHT (129)
            0xb4: LEFT,   # Raw code -> MMBasic LEFT (131)
            0xd0: BreakKey,# Raw code -> MMBasic BreakKey (3)
            0xd1: INSERT, # Raw code -> MMBasic INSERT (132)
            0xd2: HOME,   # Raw code -> MMBasic HOME (134)
            0xd5: END,    # Raw code -> MMBasic END (135)
            0xd6: PUP,    # Raw code -> MMBasic PUP (136)
            0xd7: PDOWN,  # Raw code -> MMBasic PDOWN (137)
            # Raw ASCII codes (like 'a', '1', etc.) are passed through by default
        }

        # The C code's default case passes the raw code through if not matched.
        # .get(raw_code, raw_code) achieves the same here.
        return c_intermediate_map.get(raw_code, raw_code)

    def _decode_and_buffer(self, status):
        """
        Decodes the 16-bit status word and buffers valid keypresses.
        Updates the `ctrl_held` state.

        Args:
            status (int): The 16-bit status word (or None).
        """
        if status is None: # Communication error
            return
        if status == 0: # No key event
             return

        self.last_raw_status = status # Store for debugging

        # Check for PicoCalc specific Ctrl codes first
        if status == 0xA502: # PicoCalc Ctrl pressed
            self.ctrl_held = True
            # print("DEBUG: Ctrl Pressed (0xA502)")
            return
        elif status == 0xA503: # PicoCalc Ctrl released
            self.ctrl_held = False
            # print("DEBUG: Ctrl Released (0xA503)")
            return
        # Check for alternate Ctrl codes (non-PicoCalc build?)
        elif status == 0x7E02: # Standard Ctrl pressed
            self.ctrl_held = True
            # print("DEBUG: Ctrl Pressed (0x7E02)")
            return
        elif status == 0x7E03: # Standard Ctrl released
            self.ctrl_held = False
            # print("DEBUG: Ctrl Released (0x7E03)")
            return

        # Check if it's a key press event (HIGH BYTE == 1)
        event_type = status >> 8 # Use HIGH byte for event type
        
        if event_type == 1: # Key PRESS event
            raw_key_code = status & 0xFF # Use LOW byte for raw key code
            # print(f"DEBUG: Key Press Event: Raw Code=0x{raw_key_code:02X}")

            # Translate raw code to intermediate code
            c = self._translate_raw_code(raw_key_code)
            # print(f"DEBUG: Translated Code=0x{c:02X} ({chr(c) if 32<=c<=126 else '.'})")

            # Apply Ctrl modifier ONLY to lowercase letters
            if self.ctrl_held and isinstance(c, int) and ord('a') <= c <= ord('z'):
                final_code = c - ord('a') + 1
                # print(f"DEBUG: Applied Ctrl: 0x{final_code:02X}")
            else:
                final_code = c

            # Handle Break Key (Ctrl+C -> ASCII 3)
            if final_code == BreakKey:
                # How to signal MMAbort in Python? Raise an exception? Set a flag?
                # For now, just buffer it like any other key.
                # Or maybe have a specific callback or flag. Let's buffer it.
                # MMAbort = True # Can't set global like this easily
                print("Break key (Ctrl+C) detected!")
                # C code clears buffer, maybe do that here?
                self.key_buffer.clear() # Clear buffer on break

            # Buffer the final key code
            if final_code is not None:
                self.key_buffer.append(final_code)
                # print(f"DEBUG: Buffered key: 0x{final_code:02X}")
        elif event_type == 2: # Key REPEAT event?
            # Optional: Handle repeat like a press? Or ignore?
            # For now, let's buffer repeats too, like presses
            raw_key_code = status & 0xFF # Use LOW byte for raw key code
            c = self._translate_raw_code(raw_key_code)
            if self.ctrl_held and isinstance(c, int) and ord('a') <= c <= ord('z'):
                final_code = c - ord('a') + 1
            else:
                final_code = c
            if final_code is not None:
                 self.key_buffer.append(final_code)
            # print(f"DEBUG: Key Repeat Event: Raw Code=0x{raw_key_code:02X}, Buffered as 0x{final_code:02X}")
            pass 
        elif event_type == 3: # Key RELEASE event
            # print(f"DEBUG: Key Release Event: Raw Code=0x{status & 0xFF:02X}")
            # We generally don't buffer key releases, but could add logic here if needed.
            pass
        # else: # Other event types? LSB != 1 and not Ctrl code
            # print(f"DEBUG: Unknown event type: Status=0x{status:04X}")

    def scan_keyboard(self):
        """
        Performs the two-stage poll (write command, read status)
        and processes the result. Should be called periodically.
        """
        if not self.bus:
            # print("Warning: scan_keyboard called but I2C bus not initialized.")
            return

        # Stage 1: Write command
        if not self._write_command():
            # Failed to write command, maybe device disconnected?
            # print("DEBUG: Failed to write command in scan_keyboard") # Debug
            time.sleep(0.01) # Small delay before next attempt
            return # Skip reading status if write failed

        # Short delay between write and read? Needed by some I2C devices.
        time.sleep_ms(1) # 1 millisecond delay

        # Stage 2: Read status
        status = self._read_status()

        # --- DEBUG: Print raw status --- 
        if status is not None: 
            # print(f"DEBUG: Received Status = 0x{status:04X}")
            pass
        else:
            print("DEBUG: Received Status = None")
        # --- END DEBUG ---

        # Stage 3: Decode and buffer
        if status is not None:
            self._decode_and_buffer(status)
        # else:
            # print("DEBUG: Failed to read status in scan_keyboard") # Debug

    def has_key(self):
        """
        Check if a key code is available in the buffer.

        Returns:
            bool: True if a key is available, False otherwise.
        """
        return len(self.key_buffer) > 0

    def get_key(self):
        """
        Get the next available key code from the buffer.

        Returns:
            int or None: Key code (ASCII or special value) or None if buffer is empty.
        """
        if self.key_buffer:
            return self.key_buffer.pop(0)
        else:
            return None

    def test(self):
        """
        Run a simple test loop to check keyboard functionality.
        Scans periodically and prints detected keys.
        """
        if not self.bus:
            print("Cannot run test: I2C bus not initialized.")
            return

        print(f"PicoCalc Keyboard Test (Bus: {self.i2c_id}, Addr: 0x{self.address:02X})")
        print("Polling keyboard... Press keys (Ctrl+C on *this* terminal to exit test).")
        print("Outputs: Raw Status | Decoded Key (Hex) | Ctrl Held?")

        try:
            while True:
                self.scan_keyboard() # Poll the keyboard

                key = self.get_key() # Check buffer
                if key is not None:
                     char_repr = chr(key) if 32 <= key <= 126 else '.'
                     print(f"Status: 0x{self.last_raw_status:04X} -> Key: 0x{key:02X} ('{char_repr}') Ctrl: {self.ctrl_held}")

                # Prevent busy-looping, C firmware implies periodic checks
                time.sleep(0.02) # Poll roughly 50 times/sec

        except KeyboardInterrupt:
            print("Test stopped by user.")
        except Exception as e:
            print(f"Error during test loop: {e}")
        finally:
            # Ensure the bus is closed if the test created the instance
            # self.close() # Let the caller manage closing
            pass

# --- Optional: Module-level functions for singleton-like access ---

_keyboard_instance: PicoCalcKeyboard | None = None

def init(i2c_id=1, sda_pin=6, scl_pin=7, freq=100000, force_reinit=False):
    """Initialize the global keyboard instance."""
    global _keyboard_instance
    if _keyboard_instance is None or force_reinit:
        # No explicit close needed for machine.I2C
        _keyboard_instance = None # Clear previous instance if forcing reinit
        try:
            _keyboard_instance = PicoCalcKeyboard(i2c_id=i2c_id, sda_pin=sda_pin, scl_pin=scl_pin, freq=freq)
        except Exception as e:
            print(f"Failed to initialize PicoCalcKeyboard: {e}")
            _keyboard_instance = None
    return _keyboard_instance

def get_key_module():
    """Get a key using the global instance, requires periodic scanning elsewhere."""
    if _keyboard_instance:
        return _keyboard_instance.get_key()
    return None

def has_key_module():
     """Check for key using the global instance, requires periodic scanning elsewhere."""
     if _keyboard_instance:
         return _keyboard_instance.has_key()
     return False

def scan_keyboard_module():
     """Scan using the global instance."""
     if _keyboard_instance:
         _keyboard_instance.scan_keyboard()

def test_module(i2c_id=1, sda_pin=6, scl_pin=7, freq=100000):
     """Run test using a temporary instance."""
     kbd = None
     try:
         kbd = PicoCalcKeyboard(i2c_id=i2c_id, sda_pin=sda_pin, scl_pin=scl_pin, freq=freq)
         kbd.test()
     except Exception as e:
         print(f"Failed to run test: {e}")
     # No finally block needed to close kbd

# Example Usage (if run directly)
if __name__ == "__main__":
    print("Running PicoCalc Keyboard Test (MicroPython)...")
    # Use the new default settings based on schematic analysis
    # I2C_BUS_ID = 1
    # SDA_PIN = 6
    # SCL_PIN = 7
    # I2C_FREQ = 400000 # Changed back to 100000

    print(f"Attempting to use default I2C settings (I2C1, SDA: GP6, SCL: GP7, Freq: 100kHz)") # Updated frequency in print
    print("Ensure the keyboard is connected and powered.")

    # Use the module-level test function, which now uses the correct defaults
    test_module()

    # --- Alternative direct instantiation (also uses new defaults) ---
    # keyboard = None
    # try:
    #     keyboard = PicoCalcKeyboard(i2c_id=I2C_BUS_ID, sda_pin=SDA_PIN, scl_pin=SCL_PIN, freq=I2C_FREQ)
    #     keyboard.test()
    # except Exception as e:
    #     print(f"Error: {e}")
    # No finally needed 