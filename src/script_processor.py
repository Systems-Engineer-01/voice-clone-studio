"""
Voice Clone Studio — Procesador de Guiones
============================================
Sprint 2: Divide textos largos en fragmentos óptimos para síntesis TTS.

Uso:
    python -m src.script_processor scripts/ejemplo.txt
    python -m src.script_processor scripts/ejemplo.txt --max-chars 200
    python -m src.script_processor scripts/ejemplo.txt --output output/mis_fragmentos.json
"""

import argparse
import json
import re
import sys
from pathlib import Path

# ──────────────────────────────────────────────────────────────
# Configuración por defecto
# ──────────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT = PROJECT_ROOT / "output" / "fragments.json"
DEFAULT_MAX_CHARS = 250


# ──────────────────────────────────────────────────────────────
# Limpieza de texto
# ──────────────────────────────────────────────────────────────

def clean_text(text: str) -> str:
    """
    Normaliza el texto para síntesis TTS:
    - Reemplaza comillas tipográficas por rectas
    - Normaliza guiones largos
    - Colapsa saltos de línea múltiples en espacios
    - Elimina espacios extra
    - Elimina espacios antes de signos de puntuación
    """
    # Comillas tipográficas → rectas
    replacements = {
        "\u201c": '"',  # "
        "\u201d": '"',  # "
        "\u2018": "'",  # '
        "\u2019": "'",  # '
        "\u00ab": '"',  # «
        "\u00bb": '"',  # »
    }
    for old, new in replacements.items():
        text = text.replace(old, new)

    # Guiones largos → guion normal
    text = text.replace("\u2014", "-")  # —
    text = text.replace("\u2013", "-")  # –

    # Puntos suspensivos tipográficos → tres puntos
    text = text.replace("\u2026", "...")

    # Saltos de línea → espacios
    text = re.sub(r"\r\n|\r|\n", " ", text)

    # Tabs → espacios
    text = text.replace("\t", " ")

    # Colapsar espacios múltiples
    text = re.sub(r" {2,}", " ", text)

    # Eliminar espacios antes de puntuación
    text = re.sub(r"\s+([.,;:!?\)])", r"\1", text)

    # Eliminar espacios después de paréntesis de apertura
    text = re.sub(r"(\()\s+", r"\1", text)

    return text.strip()


# ──────────────────────────────────────────────────────────────
# División en oraciones
# ──────────────────────────────────────────────────────────────

def split_into_sentences(text: str) -> list[str]:
    """
    Divide el texto en oraciones usando puntuación como delimitador.
    Maneja abreviaturas comunes en español para no cortar incorrectamente.
    """
    # Proteger abreviaturas comunes (no son fin de oración)
    abbreviations = [
        "Dr.", "Dra.", "Sr.", "Sra.", "Srta.", "Ud.", "Uds.",
        "etc.", "vs.", "vol.", "cap.", "pág.", "núm.", "tel.",
        "Prof.", "Ing.", "Lic.", "Arq.", "Mtro.", "Mtra.",
        "a.m.", "p.m.", "EE.UU.", "S.A.", "S.L.",
    ]

    # Reemplazar temporalmente las abreviaturas
    protected = text
    placeholders = {}
    for i, abbr in enumerate(abbreviations):
        placeholder = f"__ABBR{i}__"
        placeholders[placeholder] = abbr
        protected = protected.replace(abbr, placeholder)

    # Dividir por fin de oración: . ! ? ¿ ¡ seguidos de espacio o fin de texto
    # También maneja "..." como fin de oración
    raw_sentences = re.split(r"(?<=[\.\!\?\u2026])\s+", protected)

    # Restaurar abreviaturas y limpiar
    sentences = []
    for sent in raw_sentences:
        for placeholder, abbr in placeholders.items():
            sent = sent.replace(placeholder, abbr)
        sent = sent.strip()
        if sent:
            sentences.append(sent)

    return sentences


# ──────────────────────────────────────────────────────────────
# Fragmentación
# ──────────────────────────────────────────────────────────────

def split_into_fragments(
    text: str,
    max_chars: int = DEFAULT_MAX_CHARS,
) -> list[str]:
    """
    Divide el texto en fragmentos de máximo `max_chars` caracteres,
    respetando límites de oración (nunca corta palabras).

    Si una oración individual excede max_chars, se subdivide por
    comas o, como último recurso, por el límite de palabras más
    cercano al máximo.
    """
    sentences = split_into_sentences(text)
    fragments: list[str] = []
    current_fragment = ""

    for sentence in sentences:
        # Si la oración cabe en el fragmento actual
        candidate = f"{current_fragment} {sentence}".strip()
        if len(candidate) <= max_chars:
            current_fragment = candidate
            continue

        # Guardar fragmento actual si tiene contenido
        if current_fragment:
            fragments.append(current_fragment)
            current_fragment = ""

        # Si la oración cabe sola en un fragmento
        if len(sentence) <= max_chars:
            current_fragment = sentence
            continue

        # Oración demasiado larga: subdividir por comas
        sub_parts = _split_long_sentence(sentence, max_chars)
        for part in sub_parts[:-1]:
            fragments.append(part)
        current_fragment = sub_parts[-1] if sub_parts else ""

    # No olvidar el último fragmento
    if current_fragment:
        fragments.append(current_fragment)

    return fragments


def _split_long_sentence(sentence: str, max_chars: int) -> list[str]:
    """
    Subdivide una oración larga, primero por comas y luego
    por límite de palabras si es necesario.
    """
    # Intentar dividir por comas
    clauses = re.split(r",\s*", sentence)

    parts: list[str] = []
    current = ""

    for clause in clauses:
        candidate = f"{current}, {clause}".strip(", ") if current else clause

        if len(candidate) <= max_chars:
            current = candidate
            continue

        if current:
            parts.append(current)
            current = ""

        # Si la cláusula sola es demasiado larga, dividir por palabras
        if len(clause) > max_chars:
            word_parts = _split_by_words(clause, max_chars)
            parts.extend(word_parts[:-1])
            current = word_parts[-1] if word_parts else ""
        else:
            current = clause

    if current:
        parts.append(current)

    return parts


def _split_by_words(text: str, max_chars: int) -> list[str]:
    """
    Último recurso: divide por palabras sin exceder max_chars.
    Nunca corta una palabra a la mitad.
    """
    words = text.split()
    parts: list[str] = []
    current = ""

    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) <= max_chars:
            current = candidate
        else:
            if current:
                parts.append(current)
            current = word

    if current:
        parts.append(current)

    return parts


# ──────────────────────────────────────────────────────────────
# Pipeline completo
# ──────────────────────────────────────────────────────────────

def process_script(
    input_path: Path,
    output_path: Path,
    max_chars: int = DEFAULT_MAX_CHARS,
) -> list[str]:
    """
    Pipeline completo: leer → limpiar → fragmentar → guardar JSON.
    """
    print("=" * 60)
    print("[Procesador] Procesador de Guiones — Voice Clone Studio")
    print("=" * 60)

    # Leer archivo
    if not input_path.exists():
        print(f"\n[ERROR] No se encontró el archivo: {input_path}")
        sys.exit(1)

    print(f"\n[INFO] Leyendo: {input_path}")
    raw_text = input_path.read_text(encoding="utf-8")
    print(f"   Caracteres originales: {len(raw_text):,}")

    # Limpiar
    print("\n[INFO] Limpiando texto...")
    cleaned = clean_text(raw_text)
    print(f"   Caracteres tras limpieza: {len(cleaned):,}")

    # Fragmentar
    print(f"\n[INFO] Dividiendo en fragmentos (máx. {max_chars} caracteres)...")
    fragments = split_into_fragments(cleaned, max_chars)

    # Estadísticas
    lengths = [len(f) for f in fragments]
    avg_len = sum(lengths) / len(lengths) if lengths else 0
    max_len = max(lengths) if lengths else 0
    min_len = min(lengths) if lengths else 0

    print(f"   Fragmentos generados: {len(fragments)}")
    print(f"   Longitud promedio: {avg_len:.0f} caracteres")
    print(f"   Rango: {min_len}-{max_len} caracteres")

    # Guardar JSON
    output_path.parent.mkdir(parents=True, exist_ok=True)

    output_data = {
        "source_file": str(input_path.name),
        "max_chars": max_chars,
        "total_fragments": len(fragments),
        "fragments": [
            {"index": i, "text": frag, "chars": len(frag)}
            for i, frag in enumerate(fragments, start=1)
        ],
    }

    output_path.write_text(
        json.dumps(output_data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\n[INFO] Guardado en: {output_path}")

    # Mostrar preview
    print("\n[PREVIEW] Preview de fragmentos:")
    print("-" * 60)
    for i, frag in enumerate(fragments[:5], start=1):
        preview = frag[:80] + "..." if len(frag) > 80 else frag
        print(f"   [{i:02d}] ({len(frag):3d} chars) {preview}")
    if len(fragments) > 5:
        print(f"   ... y {len(fragments) - 5} fragmentos más")

    print("\n" + "=" * 60)
    print(f"[EXITO] ¡Listo! {len(fragments)} fragmentos guardados en {output_path}")
    print("=" * 60 + "\n")

    return fragments


# ──────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="script_processor",
        description="Divide guiones de texto en fragmentos óptimos para TTS.",
    )
    parser.add_argument(
        "input",
        type=Path,
        help="Ruta al archivo .txt con el guion (ej: scripts/ejemplo.txt)",
    )
    parser.add_argument(
        "--max-chars",
        type=int,
        default=DEFAULT_MAX_CHARS,
        help=f"Máximo de caracteres por fragmento (default: {DEFAULT_MAX_CHARS})",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help=f"Ruta de salida para el JSON (default: {DEFAULT_OUTPUT})",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    # Resolver rutas
    input_path = Path(args.input).resolve()
    output_path = Path(args.output).resolve() if args.output else DEFAULT_OUTPUT

    process_script(input_path, output_path, args.max_chars)


if __name__ == "__main__":
    main()
