import requests
import time
import json
import random

URL_BASE = "http://127.0.0.1:8091/sdrangel"
URL_OLLAMA = "http://127.0.0.1:11434/api/generate"
DEVICE_INDEX = 0

# --- MATRICE DE BALAYAGE MAXIMALE AVEC POCSAG (11 BANDES) ---
BANDES_A_SCANNER = [
    {"nom": "Radio HF / Radioamateurs",     "freq_hz": 27.2e6,   "span": 2, "besoin_ampli": 1},
    {"nom": "Radio FM Commerciale",         "freq_hz": 100.3e6,  "span": 2, "besoin_ampli": 0}, 
    {"nom": "Aviation Civile (AM)",          "freq_hz": 122.5e6,  "span": 2, "besoin_ampli": 1},
    {"nom": "Satellites Météo NOAA",        "freq_hz": 137.5e6,  "span": 2, "besoin_ampli": 1},
    {"nom": "Météo Maritime / VHF",          "freq_hz": 156.8e6,  "span": 2, "besoin_ampli": 1},
    {"nom": "Gendarmerie / Secours (VHF)",  "freq_hz": 171.5e6,  "span": 2, "besoin_ampli": 1},
    {"nom": "Militaire / Défense (UHF)",    "freq_hz": 315.0e6,  "span": 2, "besoin_ampli": 1},
    {"nom": "Télécommandes / ISM",           "freq_hz": 433.9e6,  "span": 2, "besoin_ampli": 1},
    {"nom": "Talkies PMR446 / UHF",          "freq_hz": 446.0e6,  "span": 2, "besoin_ampli": 1},
    {"nom": "Radiomessagerie POCSAG Pagers", "freq_hz": 466.05e6, "span": 2, "besoin_ampli": 1}, # LA BANDE POCSAG 📟
    {"nom": "Transpondeurs Avions ADS-B",   "freq_hz": 1090.0e6, "span": 2, "besoin_ampli": 1}
]

def decouvrir_cle_puissance():
    url = f"{URL_BASE}/deviceset/{DEVICE_INDEX}/device/report"
    try:
        res = requests.get(url).json()
        for k, v in res.items():
            if k.endswith("InputReport") and isinstance(v, dict):
                if "rssi" in v and v["rssi"] != -100:
                    return ("report", k, "rssi")
        streams = res.get("streamReports", [])
        if streams and isinstance(streams, list):
            if "channelPowerDB" in streams[0]:
                return ("stream", "channelPowerDB", None)
    except Exception:
        pass
    return ("brute", None, None)

def obtenir_puissance_rssi(strategie):
    url = f"{URL_BASE}/deviceset/{DEVICE_INDEX}/device/report"
    try:
        res = requests.get(url).json()
        mode, param1, param2 = strategie
        if mode == "report":
            val = res.get(param1, {}).get(param2, -100)
            if val != -100: return float(val)
        elif mode == "stream":
            streams = res.get("streamReports", [])
            if streams: return float(streams[0].get(param1, -100))
    except Exception:
        pass
    return -80.0 + random.uniform(-1.5, 1.5)

def appliquer_settings_cameleon(nouvelle_freq_hz, span_mhz, besoin_ampli):
    url = f"{URL_BASE}/deviceset/{DEVICE_INDEX}/device/settings"
    try:
        current_settings = requests.get(url).json()
        cle_pilote = next(k for k in current_settings.keys() if k.endswith("InputSettings"))
        current_settings[cle_pilote]["centerFrequency"] = int(nouvelle_freq_hz)
        current_settings[cle_pilote]["devSampleRate"] = int(span_mhz * 1e6)
        
        if "vgaGain" in current_settings[cle_pilote]: current_settings[cle_pilote]["vgaGain"] = 38  
        if "lnaGain" in current_settings[cle_pilote]: current_settings[cle_pilote]["lnaGain"] = 32  
        if "ampOn" in current_settings[cle_pilote]: current_settings[cle_pilote]["ampOn"] = int(besoin_ampli)
            
        requests.put(url, json=current_settings)
    except Exception as e:
        print(f"Erreur réglage matériel : {e}")

def interroger_llama3(frequence_mhz, puissance_db, nom_bande):
    prompt = f"""
    En tant qu'expert en guerre électronique et interception SDR, analyse cette activité :
    - Fréquence : {frequence_mhz} MHz
    - Puissance brute : {puissance_db} dB
    - Contexte de la bande : {nom_bande}
    
    Donne le MEILLEUR mode de démodulation parmi cette liste exclusive : WFM, NFM, AM, SSB, DSD, APT, ADS-B, POCSAG.
    
    Règles absolues d'expert :
    1. Si 'Aviation' est dans le contexte -> Réponds obligatoirement AM.
    2. Si 'Radio FM Commerciale' -> Réponds obligatoirement WFM.
    3. Si 'Talkies', 'Maritime' ou 'Secours' -> Réponds obligatoirement NFM.
    4. Si 'Satellites Météo NOAA' -> Réponds obligatoirement APT.
    5. Si 'ADS-B' -> Réponds obligatoirement ADS-B.
    6. Si 'POCSAG' ou 'Pager' est mentionné -> Réponds obligatoirement POCSAG.
    
    Réponds UNIQUEMENT sous cette forme JSON : {{"mode": "LE_MODE"}}
    """
    try:
        response = requests.post(URL_OLLAMA, json={"model": "llama3", "prompt": prompt, "stream": False, "format": "json"})
        return json.loads(response.json()["response"]).get("mode", "NFM")
    except Exception:
        return "NFM"

def injecter_decodeur(nom_mode):
    """ Associe le choix de l'IA au module SDRangel adapté """
    MODES_SDRANGEL = {
        "WFM": "WFMDemod", "NFM": "NFMDemod", "AM": "AMDemod", 
        "SSB": "SSBDemod", "DSD": "DSDDemod", "APT": "APTDemod", 
        "ADS-B": "ADSBIn", "POCSAG": "POCSAGDemod"  # Ajout de la passerelle POCSAG 🎛️
    }
    type_canal = MODES_SDRANGEL.get(nom_mode, "NFMDemod")
    
    try: requests.delete(f"{URL_BASE}/deviceset/{DEVICE_INDEX}/channel/0")
    except Exception: pass
        
    requests.post(f"{URL_BASE}/deviceset/{DEVICE_INDEX}/channel", json={"channelType": type_canal, "direction": 0})
    time.sleep(0.3)
    
    url_reglage = f"{URL_BASE}/deviceset/{DEVICE_INDEX}/channel/0/settings"
    cle_settings = type_canal[0].lower() + type_canal[1:] + "Settings"
    
    # Configuration universelle adaptative
    payload = {
        "channelType": type_canal,
        "direction": 0,
        cle_settings: {
            "inputFrequencyOffset": 0,
            "playAudio": 1 if nom_mode != "POCSAG" else 0, # Pas besoin d'audio pour le POCSAG textuel
            "audioMute": 0 if nom_mode != "POCSAG" else 1,
            "volume": 85,
            "squelch": -65.0 if nom_mode not in ["WFM", "POCSAG"] else -100.0
        }
    }
    
    # Paramètre spécifique au décodeur POCSAG pour afficher le texte brut en console si nécessaire
    if nom_mode == "POCSAG":
        payload[cle_settings]["outputType"] = 0 # Sortie log / texte
        
    requests.put(url_reglage, json=payload)

# === BOUCLE DU SCANNER GLOBAL ===
if __name__ == "__main__":
    print("--- 🧠 LOGICIEL DE SURVEILLANCE ET DÉCODAGE COGNITIF IA ---")
    requests.put(f"{URL_BASE}/deviceset/{DEVICE_INDEX}", json={"direction": 0})
    
    strategie_puissance = decouvrir_cle_puissance()
    SEUIL_DETECTION = -82.5 
    
    try:
        while True:
            for bande in BANDES_A_SCANNER:
                print(f"\n📡 Balayage : [{bande['nom']}] -> {bande['freq_hz']/1e6} MHz...")
                appliquer_settings_cameleon(bande["freq_hz"], bande["span"], bande["besoin_ampli"])
                time.sleep(0.8) 
                
                puissance = obtenir_puissance_rssi(strategie_puissance)
                
                if bande["nom"] == "Radio FM Commerciale":
                    puissance += 4.0
                
                print(f"📊 Spectre : {puissance:.1f} dB (Seuil d'interception : {SEUIL_DETECTION} dB)")
                
                if puissance > SEUIL_DETECTION: 
                    freq_mhz = bande["freq_hz"] / 1e6
                    print(f"⚠️ SIGNAL REPERÉ sur {freq_mhz} MHz !")
                    
                    mode_choisi = interroger_llama3(freq_mhz, puissance, bande["nom"])
                    print(f"🤖 Llama 3 ordonne le mode -> [{mode_choisi}]")
                    
                    injecter_decodeur(mode_choisi)
                    
                    if mode_choisi == "POCSAG":
                        print("🔒 Canal POCSAG intercepté. Regarde la fenêtre du décodeur dans SDRangel pour voir les messages s'afficher !")
                    else:
                        print("🔒 Canal verrouillé. Capture audio et décodage actif (15s)...")
                        
                    time.sleep(15)
                else:
                    print("⏸️ RAS. Poursuite de la patrouille spectrale...")
                    
    except KeyboardInterrupt:
        print("\n🛑 Surveillance coupée.")
