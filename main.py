import speech_recognition as sr
import serial
import google.generativeai as genai
import json  # Use JSON for safe parsing

# Configure Google Gemini API
genai.configure(api_key="ENTER_YOUR_API")
model = genai.GenerativeModel("gemini-1.5-flash")

# Initialize position variables
current_x = 0
current_y = 0

# Function to recognize voice and convert it to text
def voice_to_text():
    recognizer = sr.Recognizer()
    
    with sr.Microphone() as source:
        print("Listening... Speak now:")
        recognizer.adjust_for_ambient_noise(source)  # Reduce background noise
        try:
            audio = recognizer.listen(source, timeout=10)  # Listen for speech
            text = recognizer.recognize_google(audio)  # Convert speech to text
            print("You said:", text)
            return text
        except sr.UnknownValueError:
            print("Could not understand the audio.")
        except sr.RequestError:
            print("Error connecting to the recognition service.")
        except sr.WaitTimeoutError:
            print("No speech detected.")
        return None

# Function to convert command to G-code using Gemini API
def get_gcode_from_api(command, x, y):
    if not command:
        return None
    
    prompt = (
        f"You are a G-code generator for a motor car use F100. Convert the following command into G-code, "
        f"considering the car's current position X={x}, Y={y}. "
        f"The car moves as follows: 'left' → Increment X, 'right' → Increment Y, "
        f"'forward' → Increment both X and Y, 'backward' → Decrement both X and Y. "
        f"'left back' → Decrement X, 'right back' → Decrement Y. "
        f"Each unit corresponds to 1 cm movement. "
        f"always Return three in this format in comma seprated dont give brakets: \"G-code\", new X position, new Y position "
        f"Do not return any extra text. "
        f"For example, if the command is {{move forward 10cm and right 10}}, return: "
        f'"G0 X10 Y10 F100", 10, 10 '
        f"Now process this command: \"{command}\""
    )

    response = model.generate_content(prompt)

    
    return response.text.strip() if response.text else None

# Main function for handling voice input and sending G-code via serial
def main():
    global current_x, current_y

    # Open serial port (Update port as needed)
    ser = serial.Serial(port='COM5', baudrate=115200, timeout=1)

    try:
        while True:
            print("\nSay a command for the motor car...")
            command = voice_to_text()
            if not command:
                continue  # Skip if no valid input

            # Get G-code from API
            result = get_gcode_from_api(command, current_x, current_y)
            
            print(type(result))
            print(result)
        

            gcode, new_x, new_y = result.split(',')  # Extract values from API response
            print("Generated G-code:\n", gcode.strip())  
            print(gcode,"'",new_x,"'",new_y)

            # Send G-code to serial port
            for line in gcode.split("\n"):
                ser.write(line.strip().encode() + b'\n')  # Ensure no leading spaces

                # Read response from serial
                response = ser.readline().decode().strip()
                if response:
                    print("Received from device:", response)

            # Update position
            current_x, current_y = new_x, new_y
            print(f"Updated Position: X={current_x}, Y={current_y}")

    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        ser.close()

if __name__ == "__main__":
    main()
