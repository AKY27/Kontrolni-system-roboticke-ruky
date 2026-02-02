import serial

class roboruka:
    def __init__(self, port):
        tty = serial.Serial(port=port, baudrate=115200, timeout=1)
        if not tty.writable():
            raise Exception("Could not open serial port")
        self.tty = tty
        self.angles = [0, -90, 0, 0, 0, 0]

    def __map(self, x, in_min, in_max, out_min, out_max):
        return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min
        
    def send_command(self, command):
        self.tty.write(command.encode('utf-8'))
    
    def get_angles(self):
        return self.angles.copy()

    def set_angles(self, angles):
        if len(angles) != 6:
            raise ValueError("Angles list must have exactly 6 elements")
        elif any(not isinstance(angle, (int, float)) for angle in angles):
            raise ValueError("All angles must be numbers")
        elif any(angle < -90 or angle > 90 for angle in angles):
            raise ValueError("Angles must be between -90 and 90 degrees")
        self.angles = angles.copy()
        for i, val in zip(range(6), angles):
            mapped_val = int(self.__map(val, -90, 90, 0, 1024))
            command = f"S{i+1}:{mapped_val:04}\n"
            self.send_command(command)

    def close(self):
        self.send_command("stop\n")
        self.tty.close()


if __name__ == "__main__":
    ## start webserver - to be implemented
    pass
    
    
    
        
