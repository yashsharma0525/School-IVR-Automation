# School-IVR-Automation
Raspberry Pi based IVR system using SIM800L GSM module. Features include auto call answering, audio playback, DTMF input handling, SMS replies, retry system, and call logging. Ideal for schools, helplines, and automated customer support.
#  Raspberry Pi 5 IVR System (SIM800L)

A smart **Interactive Voice Response (IVR) system** built on **Raspberry Pi 5** using the **SIM800L GSM module**.  
This project allows automated call handling, DTMF-based menu navigation, SMS replies, and Google Sheets logging — designed initially for **Krishna Public School**.

---

## ✨ Features
- 📞 **Auto Call Answering** using SIM800L (`ATA`).
- 🎶 **Plays pre-recorded audio files (MP3)** for IVR menu and options.
- 🔢 **DTMF Input Handling** (user presses 1,2,3…).
- 📑 **Call Logging** with timestamp in JSON
- 📩 **Auto SMS Replies** for admission, fees, and timings.
- 🔁 **Retry System** – max 3 attempts per hour with cooldown.
- ⏰ **Time-based Replies** (e.g., "School Closed" after 2 PM).
- 🗣 **Real-time staff conversation** (without call forwarding).
- 🔔 **Notification to staff** when someone selects “Talk to Staff”.

---

## 🛠 Hardware Requirements
- Raspberry Pi 4 / 5
- SIM800L GSM Module (with SIM card)
- USB Sound Card (if using mic/speaker)
- 5V Power Supply
- Audio files (MP3) for IVR messages

---

## 📂 Project Structure

ivr_project/
┣ audio/ # MP3 audio files
┃ ┣ welcome.mp3
┃ ┣ 5_main_menu.mp3
┃ ┣ 1_admission.mp3
┃ ┣ 2_fees.mp3
┃ ┣ 3_timing.mp3
┃ ┣ 4_talk_staff.mp3
┃ ┣ invalid.mp3
┣ ivr.py # Main IVR Python script
┣ requirements.txt # Python dependencies
┗ README.md # Documentation

## 📦 Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/YOUR_USERNAME/raspberrypi-ivr-system.git
   cd raspberrypi-ivr-system
   Install dependencies:

2. pip install -r requirements.txt


3. Connect SIM800L with Raspberry Pi (UART or USB-Serial).

4. Place your audio files inside the audio/ folder.

## Future Improvements

Multi-language IVR (Hindi + English).

Cloud-based call reports dashboard.

Integration with WhatsApp Business API.

Voice-to-Text for recording user messages.
