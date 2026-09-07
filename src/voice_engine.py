"""
Voice Clone Studio — Motor de Voz
===================================
Módulo reutilizable para síntesis de voz con Coqui TTS (XTTS-v2).

Centraliza la carga del modelo, conversión de audio y síntesis.
El modelo se carga una sola vez y se reutiliza para múltiples síntesis.

Uso como módulo:
    from src.voice_engine import VoiceEngine, convert_mp4_to_wav

    engine = VoiceEngine(speaker_wav="audio_samples/mi_voz.wav")
    engine.synthesize("Hola mundo", output_path="output/test.wav")
"""

import sys
import traceback
from pathlib import Path

# ──────────────────────────────────────────────────────────────
# Constantes
# ──────────────────────────────────────────────────────────────

MODEL_NAME = "tts_models/multilingual/multi-dataset/xtts_v2"
PROJECT_ROOT = Path(__file__).resolve().parent.parent


# ──────────────────────────────────────────────────────────────
# Conversión de audio MP4 → WAV
# ──────────────────────────────────────────────────────────────

def convert_mp4_to_wav(mp4_files: list[Path], output_wav: Path) -> Path:
    """
    Concatena múltiples archivos MP4 y los exporta como un único
    WAV mono a 22050 Hz (formato óptimo para XTTS-v2).

    Requiere ffmpeg instalado en el PATH.
    """
    from pydub import AudioSegment

    print("=" * 60)
    print("Conversión MP4 → WAV")
    print("=" * 60)

    # Verificar que todos los MP4 existen
    missing = [f for f in mp4_files if not f.exists()]
    if missing:
        print("\n[ERROR] No se encontraron los siguientes archivos:")
        for f in missing:
            print(f"   • {f}")
        raise FileNotFoundError(
            f"Faltan {len(missing)} archivo(s) de audio. "
            f"Colócalos en: {mp4_files[0].parent}"
        )

    # Concatenar todos los audios
    print(f"\n[INFO] Cargando {len(mp4_files)} archivos de audio...")
    combined = AudioSegment.empty()

    for mp4_path in mp4_files:
        print(f"   - {mp4_path.name}")
        try:
            segment = AudioSegment.from_file(str(mp4_path), format="mp4")
            combined += segment
        except Exception as e:
            raise RuntimeError(
                f"Error al procesar {mp4_path.name}: {e}. "
                "Verifica que ffmpeg esté instalado: ffmpeg -version"
            ) from e

    # Convertir a mono, 22050 Hz, 16-bit y exportar
    combined = combined.set_channels(1).set_frame_rate(22050).set_sample_width(2)

    output_wav.parent.mkdir(parents=True, exist_ok=True)
    combined.export(str(output_wav), format="wav")

    duration_sec = len(combined) / 1000.0
    size_mb = output_wav.stat().st_size / (1024 * 1024)
    print(f"\n[EXITO] WAV generado: {output_wav}")
    print(f"   Duración: {duration_sec:.1f}s | Tamaño: {size_mb:.2f} MB")
    print(f"   Formato: mono, 22050 Hz, 16-bit PCM")

    return output_wav


# ──────────────────────────────────────────────────────────────
# Motor de Voz (clase reutilizable)
# ──────────────────────────────────────────────────────────────

class VoiceEngine:
    """
    Motor de síntesis de voz con XTTS-v2.

    Carga el modelo una sola vez y permite sintetizar múltiples
    textos reutilizando la misma instancia. Esto es crítico
    porque cargar XTTS-v2 toma ~30 segundos.
    """

    def __init__(
        self,
        speaker_wav: str | Path,
        language: str = "es",
        device: str | None = None,
    ):
        """
        Inicializa el motor de voz.

        Args:
            speaker_wav: Ruta al WAV de referencia de voz.
            language: Idioma para síntesis (default: "es").
            device: "cuda" o "cpu". Si None, autodetecta.
        """
        import torch
        from TTS.api import TTS

        self.speaker_wav = Path(speaker_wav)
        self.language = language

        # Verificar WAV de referencia
        if not self.speaker_wav.exists():
            raise FileNotFoundError(
                f"No se encontró el archivo de referencia: {self.speaker_wav}"
            )

        # Detectar dispositivo
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device

        print(f"\nDispositivo: {self.device.upper()}", end="")
        if self.device == "cuda":
            print(f" ({torch.cuda.get_device_name(0)})")
        else:
            print(" (sera mas lento que con GPU)")

        # Cargar modelo
        print(f"\nCargando modelo: {MODEL_NAME}")
        print("   (La primera ejecucion descarga ~1.8 GB, por favor espera...)\n")

        try:
            self._tts = TTS(MODEL_NAME).to(self.device)
        except Exception as e:
            tb = traceback.format_exc()
            raise RuntimeError(
                f"Error al cargar el modelo: {e}\nTraceback:\n{tb}\n"
                "Posibles soluciones:\n"
                "  1. Verifica tu conexión a internet (primera descarga)\n"
                "  2. Asegúrate de tener suficiente espacio en disco (~2 GB)\n"
                "  3. Si usas GPU, verifica que CUDA esté instalado correctamente\n"
                f"  4. Versión de PyTorch: {torch.__version__}"
            ) from e

        print("[EXITO] Modelo cargado exitosamente.\n")

    def synthesize(
        self,
        text: str,
        output_path: str | Path,
        language: str | None = None,
        temperature: float = 0.7,
        speed: float = 1.0,
        repetition_penalty: float = 2.0,
    ) -> Path:
        """
        Sintetiza un texto y lo guarda como WAV.

        Args:
            text: Texto a sintetizar.
            output_path: Ruta de salida para el archivo WAV.
            language: Idioma (usa el del constructor si no se especifica).
            temperature: Variabilidad de la voz generada (default 0.7).
            speed: Velocidad del habla (default 1.0).
            repetition_penalty: Penalización por repetición (default 2.0).

        Returns:
            Path al archivo generado.
        """
        output_path = Path(output_path)
        lang = language or self.language

        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            self._tts.tts_to_file(
                text=text,
                file_path=str(output_path),
                speaker_wav=str(self.speaker_wav),
                language=lang,
                split_sentences=True,
                temperature=temperature,
                speed=speed,
                repetition_penalty=repetition_penalty,
            )
        except Exception as e:
            raise RuntimeError(f"Error durante la síntesis: {e}") from e

        # Verificar resultado
        if not output_path.exists() or output_path.stat().st_size == 0:
            raise RuntimeError(
                f"El archivo de salida está vacío o no se generó: {output_path}"
            )

        return output_path

    def synthesize_batch(
        self,
        fragments: list[str],
        output_dir: str | Path,
        prefix: str = "frag",
        language: str | None = None,
        temperature: float = 0.7,
        speed: float = 1.0,
        repetition_penalty: float = 2.0,
    ) -> list[Path]:
        """
        Sintetiza múltiples fragmentos de texto, generando un WAV
        por cada uno.

        Args:
            fragments: Lista de textos a sintetizar.
            output_dir: Directorio donde guardar los WAVs.
            prefix: Prefijo para los nombres de archivo.
            language: Idioma (usa el del constructor si no se especifica).
            temperature: Variabilidad de la voz generada (default 0.7).
            speed: Velocidad del habla (default 1.0).
            repetition_penalty: Penalización por repetición (default 2.0).

        Returns:
            Lista de Paths a los archivos generados.
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        generated: list[Path] = []
        total = len(fragments)

        for i, text in enumerate(fragments, start=1):
            output_path = output_dir / f"{prefix}_{i:03d}.wav"
            preview = text[:60] + "..." if len(text) > 60 else text
            print(f"   [{i:02d}/{total:02d}] \"{preview}\"")

            self.synthesize(text, output_path, language, temperature, speed, repetition_penalty)

            size_kb = output_path.stat().st_size / 1024
            print(f"           -> {output_path.name} ({size_kb:.0f} KB)")

            generated.append(output_path)

        return generated
