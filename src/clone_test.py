"""
Voice Clone Studio — Prueba de Concepto
========================================
Sprint 1: Clonación de voz con Coqui TTS (XTTS-v2)

Convierte muestras MP4 en un WAV de referencia, luego sintetiza
texto en español con la voz clonada.

Uso:
    python -m src.clone_test
"""

import os
import sys
from pathlib import Path

# ──────────────────────────────────────────────────────────────
# Configuración
# ──────────────────────────────────────────────────────────────

# Directorio raíz del proyecto (relativo al script)
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

# Modelo
MODEL_NAME = "tts_models/multilingual/multi-dataset/xtts_v2"


# ──────────────────────────────────────────────────────────────
# Paso 1: Convertir MP4 → WAV combinado
# ──────────────────────────────────────────────────────────────

def convert_mp4_to_wav(mp4_files: list[Path], output_wav: Path) -> Path:
    """
    Concatena múltiples archivos MP4 y los exporta como un único
    WAV mono a 22050 Hz (formato óptimo para XTTS-v2).

    Requiere ffmpeg instalado en el PATH.
    """
    from pydub import AudioSegment

    print("=" * 60)
    print("PASO 1: Conversión MP4 → WAV")
    print("=" * 60)

    # Verificar que todos los MP4 existen
    missing = [f for f in mp4_files if not f.exists()]
    if missing:
        print("\n❌ ERROR: No se encontraron los siguientes archivos:")
        for f in missing:
            print(f"   • {f}")
        print(f"\n💡 Coloca tus muestras de voz en: {AUDIO_SAMPLES_DIR}")
        print("   Nombres esperados: audio1.mp4, audio2.mp4, audio3.mp4, audio4.mp4")
        sys.exit(1)

    # Concatenar todos los audios
    print(f"\n📂 Cargando {len(mp4_files)} archivos de audio...")
    combined = AudioSegment.empty()

    for mp4_path in mp4_files:
        print(f"   ✓ {mp4_path.name}")
        try:
            segment = AudioSegment.from_file(str(mp4_path), format="mp4")
            combined += segment
        except Exception as e:
            print(f"\n❌ ERROR al procesar {mp4_path.name}: {e}")
            print("💡 Verifica que ffmpeg esté instalado: ffmpeg -version")
            sys.exit(1)

    # Convertir a mono, 22050 Hz, 16-bit y exportar
    combined = combined.set_channels(1).set_frame_rate(22050).set_sample_width(2)

    output_wav.parent.mkdir(parents=True, exist_ok=True)
    combined.export(str(output_wav), format="wav")

    duration_sec = len(combined) / 1000.0
    size_mb = output_wav.stat().st_size / (1024 * 1024)
    print(f"\n✅ WAV generado: {output_wav}")
    print(f"   Duración: {duration_sec:.1f}s | Tamaño: {size_mb:.2f} MB")
    print(f"   Formato: mono, 22050 Hz, 16-bit PCM")

    return output_wav


# ──────────────────────────────────────────────────────────────
# Paso 2: Sintetizar voz clonada con XTTS-v2
# ──────────────────────────────────────────────────────────────

def synthesize_voice(
    text: str,
    speaker_wav: Path,
    output_path: Path,
    language: str = "es",
) -> Path:
    """
    Carga el modelo XTTS-v2 y sintetiza el texto con la voz de
    referencia. El modelo se descarga automáticamente la primera vez.
    """
    import torch
    from TTS.api import TTS

    print("\n" + "=" * 60)
    print("PASO 2: Síntesis de voz con XTTS-v2")
    print("=" * 60)

    # Verificar que el WAV de referencia existe
    if not speaker_wav.exists():
        print(f"\n❌ ERROR: No se encontró el archivo de referencia: {speaker_wav}")
        print("   Ejecuta primero el paso de conversión MP4 → WAV.")
        sys.exit(1)

    # Detectar dispositivo (GPU / CPU)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"\n🖥️  Dispositivo: {device.upper()}", end="")
    if device == "cuda":
        print(f" ({torch.cuda.get_device_name(0)})")
    else:
        print(" (será más lento que con GPU)")

    # Cargar modelo (se descarga automáticamente si no existe)
    print(f"\n📦 Cargando modelo: {MODEL_NAME}")
    print("   (La primera ejecución descarga ~1.8 GB, por favor espera...)\n")

    try:
        tts = TTS(MODEL_NAME).to(device)
    except Exception as e:
        print(f"\n❌ ERROR al cargar el modelo: {e}")
        print("\n💡 Posibles soluciones:")
        print("   1. Verifica tu conexión a internet (primera descarga)")
        print("   2. Asegúrate de tener suficiente espacio en disco (~2 GB)")
        print("   3. Si usas GPU, verifica que CUDA esté instalado correctamente")
        print(f"   4. Versión de PyTorch: {torch.__version__}")
        sys.exit(1)

    # Sintetizar
    print(f"🎤 Sintetizando texto en '{language}':")
    print(f'   "{text}"\n')

    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        tts.tts_to_file(
            text=text,
            file_path=str(output_path),
            speaker_wav=str(speaker_wav),
            language=language,
            split_sentences=True,
        )
    except Exception as e:
        print(f"\n❌ ERROR durante la síntesis: {e}")
        sys.exit(1)

    # Verificar resultado
    if not output_path.exists() or output_path.stat().st_size == 0:
        print("\n❌ ERROR: El archivo de salida está vacío o no se generó.")
        sys.exit(1)

    size_kb = output_path.stat().st_size / 1024
    print(f"✅ Audio generado exitosamente: {output_path}")
    print(f"   Tamaño: {size_kb:.1f} KB")

    return output_path


# ──────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────

def main():
    print("\n🎙️  Voice Clone Studio — Prueba de Concepto")
    print("─" * 60)

    # Paso 1: Convertir MP4 a WAV combinado
    wav_path = convert_mp4_to_wav(MP4_FILES, SPEAKER_WAV)

    # Paso 2: Sintetizar con XTTS-v2
    result = synthesize_voice(
        text=TEXT,
        speaker_wav=wav_path,
        output_path=OUTPUT_FILE,
        language=LANGUAGE,
    )

    # Resumen final
    print("\n" + "=" * 60)
    print("🎉 ¡COMPLETADO!")
    print("=" * 60)
    print(f"   Referencia de voz : {SPEAKER_WAV}")
    print(f"   Audio generado    : {result}")
    print(f"   Texto sintetizado : \"{TEXT}\"")
    print(f"   Idioma            : {LANGUAGE}")
    print("─" * 60 + "\n")


if __name__ == "__main__":
    main()
