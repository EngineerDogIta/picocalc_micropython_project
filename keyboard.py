"""
PicoCalc Keyboard Interface

This module provides an interface for communicating with the STM32F103-based
keyboard controller on the PicoCalc.

Based on analysis of the official firmware, the keyboard controller uses a
6x6 matrix connected directly to the STM32, which then communicates with the
Raspberry Pi Pico.

This implementation focuses on establishing the correct communication channel
with the STM32 controller.
"""
import machine
import time

# Possible communication pins between Pico and STM32
# Default SPI0 pins seem to be working based on initial test
COMMUNICATION_PINS = {
    'spi': {'sck': 2, 'mosi': 3, 'miso': 4, 'cs': 5},  # SPI0 default pins
    # Other modes removed for focused testing
}

# Keycodes and modifiers (Placeholders)
KEY_ENTER = 0x0D # Example
KEY_BACKSPACE = 0x08 # Example
KEY_ESCAPE = 0x1B # Example
KEY_TAB = 0x09 # Example

# Buffers for SPI communication
spi_write_buf = bytearray(1)
spi_read_buf = bytearray(1)

class KeyboardController:
    """Interface for communicating with the STM32 keyboard controller (SPI Focus)"""
    
    def __init__(self, mode='spi'): # Defaulting to SPI for now
        """Initialize the keyboard controller interface (SPI only)"""
        self.mode = mode
        self.interface = None
        self.cs = None # Store SPI CS pin if used
        self.last_key_byte = None
        self.key_buffer = []
        
        # Initialize the interface based on the selected mode
        try:
            if mode == 'spi':
                self._init_spi()
            else:
                # Only SPI is supported in this focused version
                raise ValueError(f"Invalid mode: {mode}. Only 'spi' is supported.")
            
            print(f"Keyboard controller initialized in {self.mode} mode")
            
            # Test communication immediately after init
            if not self._test_communication():
                 print("Warning: Initial communication test failed.")
                 
        except Exception as e:
            print(f"Error during keyboard controller initialization: {e}")
            self.mode = 'failed' # Set mode to failed on error
            raise # Re-raise the exception so caller knows init failed
    
    def _init_spi(self):
        """Initialize SPI communication with the STM32"""
        sck_pin_num = COMMUNICATION_PINS['spi']['sck']
        mosi_pin_num = COMMUNICATION_PINS['spi']['mosi']
        miso_pin_num = COMMUNICATION_PINS['spi']['miso']
        cs_pin_num = COMMUNICATION_PINS['spi']['cs']
        
        self.cs = machine.Pin(cs_pin_num, machine.Pin.OUT)
        self.cs.value(1)  # Deselect by default
        
        self.interface = machine.SPI(0,
                                    baudrate=1000000,
                                    polarity=0,
                                    phase=0,
                                    sck=machine.Pin(sck_pin_num),
                                    mosi=machine.Pin(mosi_pin_num),
                                    miso=machine.Pin(miso_pin_num))
        self.mode = 'spi' # Set mode explicitly
    
    def _test_communication(self):
        """Test SPI communication using write_readinto"""
        if not (self.mode == 'spi' and isinstance(self.interface, machine.SPI) and self.cs is not None):
             print("Test communication skipped: SPI not initialized correctly")
             return False
             
        try:
            # Prepare buffer to write (e.g., sending 0x00)
            spi_write_buf[0] = 0x00 
            # Prepare buffer to read into
            spi_read_buf[0] = 0xFF # Clear read buffer
            
            self.cs.value(0) # Select
            time.sleep(0.001)
            # Write one byte while reading one byte
            self.interface.write_readinto(spi_write_buf, spi_read_buf)
            time.sleep(0.001)
            self.cs.value(1) # Deselect
            
            # Basic test: Did we receive *something* (even 0xFF is okay here)?
            # We just want to know if the transaction completed without error.
            # print(f"DEBUG: Test read byte: 0x{spi_read_buf[0]:02X}") # Optional debug
            return True # Assume success if no exception
        except Exception as e_spi:
            print(f"SPI communication test failed: {e_spi}")
            # Ensure CS is released on error
            if self.cs is not None:
                 self.cs.value(1)
            return False
            
    def get_key_byte(self):
        """Get a single raw key byte using SPI write_readinto"""
        if not (self.mode == 'spi' and isinstance(self.interface, machine.SPI) and self.cs is not None):
            return None
            
        key_byte = None
        try:
            if self.key_buffer:
                return self.key_buffer.pop(0)
                
            # --- Perform SPI transaction --- 
            # Prepare buffer to write (send 0x00 as poll/dummy byte)
            spi_write_buf[0] = 0x00 
            # Prepare buffer to read into
            spi_read_buf[0] = 0xFF # Default to idle

            self.cs.value(0) # Select
            time.sleep(0.001)
            # Simultaneously write poll_cmd and read response into read_buf
            self.interface.write_readinto(spi_write_buf, spi_read_buf)
            time.sleep(0.001)
            self.cs.value(1) # Deselect
            
            received_byte = spi_read_buf[0]
            # print(f"DEBUG: SPI read byte: 0x{received_byte:02X}") # Optional debug
            
            # Treat 0xFF and 0x00 as "no key" / idle
            if received_byte != 0xFF and received_byte != 0x00: 
                key_byte = received_byte
                
        except Exception as e_spi_read:
             print(f"Error reading SPI: {e_spi_read}")
             # Ensure CS is released on error
             if self.cs is not None:
                 self.cs.value(1)
             key_byte = None # Set to None on error
            
        # --- Store and return --- 
        if key_byte is not None:
            self.last_key_byte = key_byte
            return key_byte
        else:
            return None # Explicitly return None if no key byte found
    
    def scan_keyboard(self):
        """Scan the keyboard for keypresses and update the key buffer"""
        key_byte = self.get_key_byte()
        if key_byte is not None:
            self.key_buffer.append(key_byte)
    
    def has_key(self):
        """Check if a key is available in the buffer
        
        Returns:
            bool: True if a key is available, False otherwise
        """
        if not self.key_buffer:
            # Scan for a new key if buffer is empty
            self.scan_keyboard()
        return len(self.key_buffer) > 0

    def get_key(self):
        """Get the next available key byte from the buffer.
           Scans if the buffer is empty.
        
        Returns:
            int or None: Key byte or None if buffer is empty after scanning.
        """
        if not self.key_buffer:
            self.scan_keyboard() # Fill buffer if empty
            
        if self.key_buffer:
            return self.key_buffer.pop(0)
        else:
            return None
            
    def test(self):
        """Run a simple test loop to check keyboard functionality"""
        print(f"Keyboard test started (mode: {self.mode})")
        print("Press keys on the keyboard (Ctrl+C to exit)...")
        print("Will print raw byte codes detected (excluding 0xFF and 0x00).")
        
        try:
            while True:
                key_byte = self.get_key() # Use the buffered get_key
                if key_byte is not None:
                    # Print the raw byte value in hex format
                    print(f"Key byte pressed: 0x{key_byte:02X}")
                # Add a small delay to prevent busy-looping and reduce noise
                time.sleep(0.05) 
        except KeyboardInterrupt:
            print("\nTest stopped by user")
        except Exception as e:
             print(f"\nError during test loop: {e}")

# Default keyboard instance
_keyboard_instance: KeyboardController | None = None

def init(mode='spi', force_reinit=False): # Forcing SPI mode here
    """Initialize the keyboard controller (singleton pattern)
    
    Args:
        mode (str): Communication mode to use (forced to 'spi')
        force_reinit (bool): If True, force reinitialization even if already initialized.
    
    Returns:
        KeyboardController or None: The initialized keyboard controller or None on failure
    """
    global _keyboard_instance
    # Force SPI mode for this focused test
    mode = 'spi' 
    
    if _keyboard_instance is None or force_reinit:
        print(f"Initializing keyboard (Mode: {mode}, Force: {force_reinit})...")
        try:
            _keyboard_instance = KeyboardController(mode)
            if _keyboard_instance.mode == 'failed':
                 print("Keyboard initialization failed (mode set to 'failed').")
                 _keyboard_instance = None
        except Exception as e:
            print(f"Keyboard initialization failed with exception: {e}")
            _keyboard_instance = None # Ensure it's None on failure
            
    return _keyboard_instance

def get_key():
    """Get the next key byte from the keyboard buffer
    
    Returns:
        int or None: The key byte pressed, or None if no key is pressed/error
    """
    global _keyboard_instance
    if _keyboard_instance is None:
        if init() is None:
             return None
             
    if _keyboard_instance is None:
        print("Error: Keyboard object not available after init attempt.")
        return None
        
    try:
        return _keyboard_instance.get_key()
    except Exception as e:
        print(f"Error during get_key: {e}")
        return None

def has_key():
    """Check if a key is available
    
    Returns:
        bool: True if a key is available, False otherwise
    """
    global _keyboard_instance
    if _keyboard_instance is None:
        if init() is None:
            return False
            
    if _keyboard_instance is None:
        print("Error: Keyboard object not available after init attempt.")
        return False
        
    try:
        return _keyboard_instance.has_key()
    except Exception as e:
        print(f"Error during has_key: {e}")
        return False

def test():
    """Run a keyboard test (forces SPI mode)"""
    global _keyboard_instance
    # Always try to initialize before testing, forcing SPI
    instance = init(mode='spi') 
    if instance:
        try:
            instance.test()
        except Exception as e:
             print(f"Error during test: {e}")
    else:
        print("Cannot run test: Keyboard initialization failed.")

if __name__ == "__main__":
    # Run test in SPI mode
    test() 