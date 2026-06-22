# SDRAngel_Llama3



📡 Cognitive Spectrum Patrol: AI-Driven SDR Scanner
An intelligent, cognitive Software Defined Radio (SDR) scanner that automates spectrum surveillance across 11 major frequency bands. By combining the hardware versatility of SDRangel with the local decision-making capabilities of Ollama (Llama 3), this tool autonomously detects signal spikes, dynamically switches demodulators, and decodes live transmissions—including tactical text over POCSAG, ADS-B aviation telemetry, and traditional voice.

🚀 Features
11-Band Autonomous Matrix: Seamlessly cycles through HF, Commercial FM, Civil Aviation, NOAA Weather Satellites, Maritime VHF, Emergency Services, ISM/Remotes, PMR446, POCSAG Paging, and ADS-B.

Cognitive Demodulation: Uses a local LLM (Llama 3) to process contextual spectrum data (frequency, power, band signature) and dynamically inject the perfect decoder module.

SDRangel Hardware Abstraction: Interface layer that automatically identifies hardware reporting features (rssi vs channelPowerDB) and dynamically applies hardware amplification (ampOn, lnaGain, vgaGain).

Silent POCSAG Interception: Smart routing automatically mutes the audio channel and routes raw text straight to the log console when paging networks are detected.

📋 Prerequisites & Setup
Before running the cognitive scanner, ensure you have your hardware connected and the following software running locally.

1. SDRangel Configuration
Download and run SDRangel.

Ensure your SDR hardware (e.g., RTL-SDR, HackRF, LimeSDR) is plugged in and recognized on Device Index 0.

Enable the built-in REST API Server. By default, it runs on http://127.0.0.1:8091.

2. Ollama Setup
Install Ollama.

Download the Llama 3 model by running the following command in your terminal: ollama run llama3

Keep the Ollama service running in the background (http://127.0.0.1:11434).

3. Python Dependencies
Clone this repository and install the required dependencies: pip install requests

🎛️ Configuration & Tuning
You can fine-tune the detection logic inside the script directly:

SEUIL_DETECTION = -82.5: Adjust this value (in dB) depending on your local noise floor. A higher threshold prevents false positives from static noise.

Dwell Time: The script pauses for 0.8 seconds after changing frequencies to let the hardware stabilize before assessing power, and locks onto an intercepted signal for 15 seconds before resuming patrol.

💻 Usage
Run the scanner directly from your terminal: python scanner.py

Expected Output Console Feed:
Balayage : [Radio FM Commerciale] -> 100.3 MHz...

Spectre : -84.2 dB (Seuil d'interception : -82.5 dB)

RAS. Poursuite de la patrouille spectrale...

Balayage : [Radiomessagerie POCSAG Pagers] -> 466.05 MHz...

Spectre : -72.1 dB (Seuil d'interception : -82.5 dB)

SIGNAL REPERÉ sur 466.05 MHz !

Llama 3 ordonne le mode -> [POCSAG]

Canal POCSAG intercepté. Regarde la fenêtre du décodeur dans SDRangel pour voir les messages s'afficher !

🛑 Stopping the Scanner
To safely stop the spectral patrol, press Ctrl + C in your terminal window. The script will intercept the command and terminate cleanly with the message: "Surveillance coupée."

📜 License & Legal Disclaimer
This tool is created for educational, research, and radio-experimentation purposes only. Monitoring certain radio frequencies without proper licensing or authorization may be restricted or illegal depending on your local jurisdiction. Always comply with local telecommunication regulations (FCC, ANFR, etc.).
