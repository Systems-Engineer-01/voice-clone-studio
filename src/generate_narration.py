"""
Voice Clone Studio — Generador de Narración Completo
======================================================
Sprint 3: Pipeline completo (Guion → Narración con Voz Clonada).

Lee un guion, lo divide en fragmentos óptimos, sintetiza cada
fragmento con XTTS-v2 usando la voz de referencia y une todos los
archivos con silencios entre ellos para crear la narración final.

Uso:
    python -m src.generate_narration scripts/ejemplo.txt
    python -m src.generate_narration scripts/ejemplo.txt --format mp3 --silence 500
"""

import argparse
import os
import shutil
import sys
from pathlib import Path

from src.script_processor import process_script, DEFAULT_MAX_CHARS
from src.voice_engine import VoiceEngine

# ──────────────────────────────────────────────────────────────
# Configuración por defecto
# ──────────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SPEAKER_WAV = PROJECT_ROOT / "audio_samples" / "mi_voz.wav"
DEFAULT_OUTPUT = PROJECT_ROOT / "output" / "narracion_final"
TEMP_DIR = PROJECT_ROOT / "output" / "temp_fragments"


# ──────────────────────────────────────────────────────────────
# Concatenación de Audio
# ──────────────────────────────────────────────────────────────

def join_audio_fragments(
    fragment_paths: list[Path],
    output_path: Path,
    silence_ms: int,
    export_format: str = "wav",
) -> Path:
    """
    Une múltiples archivos WAV en uno solo, insertando un silencio
    entre cada fragmento.
    """
    from pydub import AudioSegment

    print(f"\n[INFO] Uniendo {len(fragment_paths)} fragmentos...")
    print(f"   Silencio entre fragmentos: {silence_ms} ms")

    # Crear segmento de silencio
    silence = AudioSegment.silent(duration=silence_ms)
    
    # Inicializar con el primer fragmento
    try:
        combined = AudioSegment.from_file(str(fragment_paths[0]), format="wav")
    except Exception as e:
        raise RuntimeError(f"Error al leer {fragment_paths[0].name}: {e}") from e

    # Añadir los demás con silencio de por medio
    for path in fragment_paths[1:]:
        try:
            segment = AudioSegment.from_file(str(path), format="wav")
            combined += silence + segment
        except Exception as e:
            raise RuntimeError(f"Error al leer {path.name}: {e}") from e

    # Exportar
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"   Exportando a {export_format.upper()}...")
    try:
        combined.export(str(output_path), format=export_format)
    except Exception as e:
        raise RuntimeError(f"Error al exportar {output_path.name}: {e}") from e

    # Estadísticas
    duration_sec = len(combined) / 1000.0
    size_mb = output_path.stat().st_size / (1024 * 1024)
    print(f"\n[EXITO] Audio final generado: {output_path}")
    print(f"   Duración: {duration_sec / 60:.1f} min ({duration_sec:.1f} s)")
    print(f"   Tamaño: {size_mb:.2f} MB")

    return output_path


# ──────────────────────────────────────────────────────────────
# Pipeline Principal
# ──────────────────────────────────────────────────────────────

def run_pipeline(
    input_script: Path,
    speaker_wav: Path,
    output_base: Path,
    export_format: str = "wav",
    silence_ms: int = 300,
    max_chars: int = DEFAULT_MAX_CHARS,
    language: str = "es",
):
    """
    Orquesta el flujo completo de generación de narración.
    """
    print("\n" + "=" * 60)
    print("[INFO] Voice Clone Studio — Generador de Narración")
    print("=" * 60)

    # 1. Verificar inputs
    if not input_script.exists():
        print(f"\n[ERROR] No se encontró el guion: {input_script}")
        sys.exit(1)
        
    if not speaker_wav.exists():
        print(f"\n[ERROR] No se encontró la voz de referencia: {speaker_wav}")
        print("   Asegúrate de haber ejecutado el Sprint 1 primero o especifica")
        print("   una ruta válida con --speaker.")
        sys.exit(1)

    output_file = output_base.with_suffix(f".{export_format}")

    # 2. Procesar el guion (Fragmentación)
    # Reutilizamos el script_processor del Sprint 2
    json_path = TEMP_DIR / "fragments.json"
    fragments = process_script(input_script, json_path, max_chars)
    
    if not fragments:
        print("\n[ERROR] El guion está vacío o no se pudieron generar fragmentos.")
        sys.exit(1)

    # 3. Inicializar Motor de Voz y Sintetizar
    try:
        print("\n" + "=" * 60)
        print("[INFO] Inicializando Motor de Voz...")
        print("=" * 60)
        
        engine = VoiceEngine(speaker_wav=speaker_wav, language=language)
        
        print("\n" + "=" * 60)
        print(f"[INFO] Sintetizando {len(fragments)} fragmentos...")
        print("=" * 60)
        
        # Limpiar/crear directorio temporal
        if TEMP_DIR.exists():
            shutil.rmtree(TEMP_DIR)
        TEMP_DIR.mkdir(parents=True)
        
        # Sintetizar todos los fragmentos
        fragment_wavs = engine.synthesize_batch(fragments, TEMP_DIR)
        
    except Exception as e:
        print(f"\n[ERROR] durante la síntesis: {e}")
        sys.exit(1)

    # 4. Unir y Exportar
    try:
        print("\n" + "=" * 60)
        print("[INFO] Ensamblando Narración Final...")
        print("=" * 60)
        
        result = join_audio_fragments(
            fragment_paths=fragment_wavs,
            output_path=output_file,
            silence_ms=silence_ms,
            export_format=export_format,
        )
    except Exception as e:
        print(f"\n[ERROR] al ensamblar el audio: {e}")
        sys.exit(1)

    # 5. Limpieza
    print("\n[INFO] Limpiando archivos temporales...")
    shutil.rmtree(TEMP_DIR, ignore_errors=True)

    print("\n" + "=" * 60)
    print("[EXITO] ¡NARRACIÓN COMPLETADA CON ÉXITO!")
    print("=" * 60)
    print(f"   Guion original : {input_script.name}")
    print(f"   Voz de ref.    : {speaker_wav.name}")
    print(f"   Archivo final  : {result}")
    print("─" * 60 + "\n")


# ──────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="generate_narration",
        description="Genera una narración completa a partir de un guion de texto.",
    )
    parser.add_argument(
        "input",
        type=Path,
        help="Ruta al archivo .txt con el guion (ej: scripts/mi_guion.txt)",
    )
    parser.add_argument(
        "--speaker",
        type=Path,
        default=DEFAULT_SPEAKER_WAV,
        help=f"WAV de referencia de voz (default: {DEFAULT_SPEAKER_WAV.relative_to(PROJECT_ROOT)})",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Ruta base de salida sin extensión (default: output/narracion_final)",
    )
    parser.add_argument(
        "--format",
        type=str,
        choices=["wav", "mp3"],
        default="wav",
        help="Formato de audio de salida (default: wav)",
    )
    parser.add_argument(
        "--silence",
        type=int,
        default=300,
        help="Silencio entre fragmentos en milisegundos (default: 300)",
    )
    parser.add_argument(
        "--max-chars",
        type=int,
        default=DEFAULT_MAX_CHARS,
        help=f"Máximo de caracteres por fragmento (default: {DEFAULT_MAX_CHARS})",
    )
    parser.add_argument(
        "--language",
        type=str,
        default="es",
        help="Idioma de síntesis (default: es)",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    # Resolver rutas
    input_path = Path(args.input).resolve()
    speaker_path = Path(args.speaker).resolve()
    output_base = Path(args.output).resolve()

    run_pipeline(
        input_script=input_path,
        speaker_wav=speaker_path,
        output_base=output_base,
        export_format=args.format,
        silence_ms=args.silence,
        max_chars=args.max_chars,
        language=args.language,
    )


if __name__ == "__main__":
    main()
