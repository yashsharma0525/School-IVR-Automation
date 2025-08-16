# === IMPORTS ===
import serial, time, os, subprocess, json
from datetime import datetime, timedelta
from threading import Thread, Event
from gpiozero import Button

# === CONFIGURATION ===
SERIAL_PORT      = "/dev/serial0"              # Serial port for SIM800L
BAUDRATE         = 9600                        # Baudrate for serial communication
AUDIO_FOLDER     = "/home/yash/ivr_project/audio"  # Folder containing MP3 files
CALL_LOG_FILE    = "call_logs.txt"             # To log call history
RETRY_LOG_FILE   = "retry_logs.txt"            # To manage retry limits
MAX_ATTEMPTS     = 300                         # Max retry attempts per hour
BLOCK_DURATION   = timedelta(hours=1)          # Retry block period
STAFF_NUMBER     = "919219220759"              # Number to notify for Option 4
ANSWER_BUTTON_PIN = 17                         # Button to answer staff call
CUT_BUTTON_PIN    = 27                         # Button to manually cut call

# === GLOBAL VARIABLES ===
call_active = False
stop_event = Event()
answer_button = Button(ANSWER_BUTTON_PIN)
cut_button = Button(CUT_BUTTON_PIN)

# === AUDIO PLAYBACK ===
def play_audio(filename):
    """Play audio synchronously using VLC."""
    path = os.path.join(AUDIO_FOLDER, filename)
    subprocess.run(["cvlc", "--aout=alsa", "--alsa-audio-device=hw:0,0", "--play-and-exit", path])

def play_audio_async(filename):
    """Play audio in background thread."""
    Thread(target=play_audio, args=(filename,), daemon=True).start()

# === SMS FUNCTION ===
def send_sms(number, message):
    """Send SMS to given number."""
    ser.write(b'AT+CMGF=1\r'); time.sleep(0.5)
    ser.write(f'AT+CMGS="{number}"\r'.encode()); time.sleep(0.5)
    ser.write((message + "\x1A").encode()); time.sleep(3)

# === RETRY & LOGGING ===
def is_blocked(phone):
    """Check if the number has exceeded call attempts."""
    if not os.path.exists(RETRY_LOG_FILE):
        return False
    with open(RETRY_LOG_FILE) as f:
        data = json.load(f)
    now = datetime.now()
    recent = [datetime.fromisoformat(t) for t in data.get(phone, []) if now - datetime.fromisoformat(t) < BLOCK_DURATION]
    if len(recent) >= MAX_ATTEMPTS:
        return True
    data[phone] = [t.isoformat() for t in recent]
    with open(RETRY_LOG_FILE, "w") as f:
        json.dump(data, f)
    return False

def log_attempt(phone):
    """Log the phone's attempt."""
    data = {}
    if os.path.exists(RETRY_LOG_FILE):
        with open(RETRY_LOG_FILE) as f:
            data = json.load(f)
    data.setdefault(phone, []).append(datetime.now().isoformat())
    with open(RETRY_LOG_FILE, "w") as f:
        json.dump(data, f)

def log_call(phone, option):
    """Log the option selected by user."""
    with open(CALL_LOG_FILE, "a") as f:
        f.write(json.dumps({
            "phone": phone,
            "option": option,
            "time": datetime.now().isoformat()
        }) + "\n")

# === DTMF INPUT HANDLING ===
def handle_dtmf(digit, phone):
    """Handle user input (DTMF tone)."""
    if digit == '1':
        play_audio_async("1_admission.mp3")
        send_sms(phone, "Admission info: Visit our site or school.")
    elif digit == '2':
        play_audio_async("2_fees.mp3")
        send_sms(phone, "Fees: ₹2500/month. Pay online or office.")
    elif digit == '3':
        play_audio_async("3_timing.mp3")
        send_sms(phone, "Timing: Mon–Sat 8AM–2PM, Sunday closed.")
    elif digit == '4':
        play_audio_async("4_talk_staff.mp3")
        send_sms(STAFF_NUMBER, f"IVR Alert: call from {phone}")
        simulate_staff_call()
    elif digit == '0':
        play_audio_async("5_main_menu.mp3")  # Go back to main menu
        return
    else:
        play_audio_async("invalid.mp3")      # Invalid option
    log_call(phone, digit)

def simulate_staff_call():
    """Initiate a simulated staff call after option 4."""
    print("Simulating staff call…")
    ser.write(f'ATD{STAFF_NUMBER};\r'.encode())
    time.sleep(3)

    print("Waiting for staff to press answer button…")
    if answer_button.wait_for_press(timeout=10):
        print("Staff answered using button")
        ser.write(b'ATA\r')
    else:
        print("No answer from staff")
        ser.write(b'ATH\r')
        play_audio_async("staff_busy.mp3")  # Make sure this file exists

def dtmf_listener(phone):
    """Listen for DTMF tones from user during call."""
    global call_active
    recent_digits = set()
    while call_active and not stop_event.is_set():
        if ser.in_waiting:
            try:
                line = ser.readline().decode(errors='ignore').strip()
                if "+DTMF:" in line:
                    parts = line.split(":")
                    if len(parts) == 2:
                        digit = parts[1].strip()[0]
                        if digit and digit not in recent_digits:
                            print("User pressed:", digit)
                            recent_digits.add(digit)
                            handle_dtmf(digit, phone)
                            time.sleep(1)
            except Exception as e:
                print("DTMF error:", e)
    print("DTMF listener stopped.")

# === MANUAL CUT BUTTON HANDLER ===
def cut_call_monitor():
    """Monitor manual cut button."""
    global call_active, stop_event
    if cut_button.wait_for_press(timeout=60):
        print("Call manually disconnected.")
        call_active = False
        stop_event.set()
        ser.write(b'ATH\r')
        play_audio_async("staff_busy.mp3")

# === CALL HANDLER ===
def handle_call(phone):
    """Main function to handle the incoming call."""
    global call_active, stop_event

    if is_blocked(phone):
        print("Number blocked due to too many calls.")
        ser.write(b'ATH\r')
        return

    log_attempt(phone)
    ser.write(b'AT+DDET=1\r')  # Enable DTMF
    call_active = True
    stop_event.clear()

    # Start background threads
    Thread(target=dtmf_listener, args=(phone,), daemon=True).start()
    Thread(target=cut_call_monitor, daemon=True).start()

    # Play welcome and menu
    play_audio("welcome.mp3")
    play_audio("5_main_menu.mp3")

    # Wait until timeout or cut
    timeout = 60
    start = time.time()
    while time.time() - start < timeout and call_active:
        time.sleep(0.5)

    call_active = False
    stop_event.set()
    ser.write(b'ATH\r')
    print("Call ended.")

# === MAIN LOOP ===
def listen_for_calls():
    """Main loop to wait for incoming calls."""
    global ser, call_active
    ser = serial.Serial(SERIAL_PORT, BAUDRATE, timeout=1)
    ser.flushInput()
    ser.write(b'AT+CLIP=1\r'); time.sleep(0.5)  # Enable caller ID
    ser.write(b'AT+DDET=1\r'); time.sleep(0.5)  # Enable DTMF
    print("📞 IVR System Ready. Waiting for calls...")

    while True:
        if call_active:
            time.sleep(0.1)
            continue
        if ser.in_waiting:
            line = ser.readline().decode(errors='ignore').strip()
            if "RING" in line:
                print("Incoming call...")
            elif "+CLIP:" in line:
                try:
                    phone = line.split('"')[1]
                    print("Call from:", phone)
                    ser.write(b'ATA\r')  # Auto answer
                    time.sleep(2)
                    Thread(target=handle_call, args=(phone,), daemon=True).start()
                except IndexError:
                    print("⚠️ Couldn't extract phone number.")

# === START SCRIPT ===
try:
    listen_for_calls()
except KeyboardInterrupt:
    print("📴 IVR system stopped manually.")
