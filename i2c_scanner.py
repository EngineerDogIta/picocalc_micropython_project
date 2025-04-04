import machine
import time
import sys

def scan_i2c(bus_id, sda_pin, scl_pin):
    """Scan for I2C devices on the specified bus and pins"""
    try:
        i2c = machine.I2C(bus_id, sda=machine.Pin(sda_pin), scl=machine.Pin(scl_pin))
        devices = i2c.scan()
        return devices
    except Exception as e:
        print(f"Error scanning I2C{bus_id} (SDA={sda_pin}, SCL={scl_pin}): {e}")
        return []

def main():
    """Scan all common I2C configurations"""
    print("I2C Scanner for Raspberry Pi Pico")
    print("=================================")
    
    # Common configurations to try
    configs = [
        (0, 0, 1),  # I2C0: SDA=GP0, SCL=GP1
        (0, 4, 5),  # I2C0: SDA=GP4, SCL=GP5
        (1, 2, 3),  # I2C1: SDA=GP2, SCL=GP3
        (1, 6, 7),  # I2C1: SDA=GP6, SCL=GP7
        (0, 8, 9),  # I2C0: SDA=GP8, SCL=GP9
        (0, 12, 13),  # I2C0: SDA=GP12, SCL=GP13
        (1, 14, 15),  # I2C1: SDA=GP14, SCL=GP15
        (1, 26, 27)  # I2C1: SDA=GP26, SCL=GP27
    ]
    
    found_any = False
    
    # Try each configuration
    for i, (bus, sda, scl) in enumerate(configs):
        print(f"\nScanning I2C{bus}: SDA=GP{sda}, SCL=GP{scl}... ", end="")
        devices = scan_i2c(bus, sda, scl)
        
        if not devices:
            print("No devices found")
        else:
            found_any = True
            print(f"Found {len(devices)} device(s):")
            for addr in devices:
                print(f"  - Device at address: 0x{addr:02x} ({addr})")
                
    if not found_any:
        print("\nNo I2C devices found on any bus/pin configuration.")
        print("Check your connections and try again.")
    else:
        print("\nScan complete. Use these values in your I2C keyboard driver:")
        print("1. Use the correct bus_id, sda_pin, and scl_pin from above")
        print("2. Set KBD_I2C_ADDR to the detected address")

if __name__ == "__main__":
    main() 