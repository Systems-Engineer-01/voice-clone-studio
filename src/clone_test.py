"""
Voice Clone Studio — Prueba de Concepto
========================================
Sprint 1: Clonación de voz con Coqui TTS (XTTS-v2)

Convierte muestras MP4 en un WAV de referencia, luego sintetiza
texto en español con la voz clonada.

Uso:
    python -m src.clone_test
"""

import sys
from pathlib import Path

from src.voice_engine import VoiceEngine, convert_mp4_to_wav

# ──────────────────────────────────────────────────────────────
# Configuración
# ──────────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Archivos de entrada (muestras de voz en MP4)
AUDIO_SAMPLES_DIR = PROJECT_ROOT / "audio_samples"
MP4_FILES = [
    AUDIO_SAMPLES_DIR / "prueba1.mp4",
    AUDIO_SAMPLES_DIR / "prueba2.mp4",
    AUDIO_SAMPLES_DIR / "prueba3.mp4",
    AUDIO_SAMPLES_DIR / "prueba4.mp4",
]

# Archivo WAV combinado (referencia de voz para el modelo)
SPEAKER_WAV = AUDIO_SAMPLES_DIR / "mi_voz.wav"

# Salida
OUTPUT_DIR = PROJECT_ROOT / "output"
OUTPUT_FILE = OUTPUT_DIR / "prueba_1.wav"

# Texto a sintetizar
TEXT = "Hola, esta es una prueba de mi voz clonada"
LANGUAGE = "es"


# ──────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────

def main():
    print("\n[INFO] Voice Clone Studio — Prueba de Concepto")
    print("─" * 60)

    # Paso 1: Convertir MP4 a WAV combinado
    try:
        print("\nPASO 1:")
        wav_path = convert_mp4_to_wav(MP4_FILES, SPEAKER_WAV)
    except (FileNotFoundError, RuntimeError) as e:
        print(f"\n[ERROR] {e}")
        sys.exit(1)

    # Paso 2: Sintetizar con XTTS-v2
    try:
        print("\n" + "=" * 60)
        print("PASO 2: Síntesis de voz con XTTS-v2")
        print("=" * 60)

        engine = VoiceEngine(speaker_wav=wav_path, language=LANGUAGE)

        print(f"[INFO] Sintetizando texto en '{LANGUAGE}':")
        print(f'   "{TEXT}"\n')

        result = engine.synthesize(text=TEXT, output_path=OUTPUT_FILE)
    except (FileNotFoundError, RuntimeError) as e:
        print(f"\n[ERROR] {e}")
        sys.exit(1)

    # Resumen final
    size_kb = result.stat().st_size / 1024
    print(f"\n[EXITO] Audio generado: {result} ({size_kb:.1f} KB)")

    print("\n" + "=" * 60)
    print("[EXITO] ¡COMPLETADO!")
    print("=" * 60)
    print(f"   Referencia de voz : {SPEAKER_WAV}")
    print(f"   Audio generado    : {result}")
    print(f'   Texto sintetizado : "{TEXT}"')
    print(f"   Idioma            : {LANGUAGE}")
    print("─" * 60 + "\n")


if __name__ == "__main__":
    main()
