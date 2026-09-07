# 🎙️ Voice Clone Studio

Sistema de clonación de voz basado en **Coqui TTS** con el modelo **XTTS-v2**.
Permite generar audio con una voz clonada a partir de muestras de referencia.

---

## 🎯 Objetivo

Construir un pipeline de clonación de voz que permita:

1. **Capturar** muestras de audio de una voz objetivo.
2. **Procesar** y normalizar las muestras para el modelo.
3. **Generar** audio sintético con la voz clonada usando XTTS-v2.
4. **Exportar** el resultado en formatos estándar (WAV, MP3).

---

## 📋 Requisitos Previos

- **Python** 3.10 o superior
- **ffmpeg** instalado y en el PATH ([descargar](https://ffmpeg.org/download.html))
- **GPU con CUDA** (recomendado) — el modelo funciona en CPU pero es significativamente más lento
- ~5 GB de espacio libre (para PyTorch + modelo XTTS-v2)

---

## 🚀 Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/tu-usuario/voice-clone-studio.git
cd voice-clone-studio
```

### 2. Crear y activar el entorno virtual

```bash
# Crear
python -m venv venv

# Activar (Windows)
venv\Scripts\activate

# Activar (macOS/Linux)
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

> ⚠️ **Nota:** La instalación de `torch` y `TTS` puede tardar varios minutos
> dependiendo de tu conexión. Si necesitas una versión específica de CUDA,
> consulta la [guía oficial de PyTorch](https://pytorch.org/get-started/locally/).

---

## 📁 Estructura del Proyecto

```
voice-clone-studio/
├── audio_samples/          # Muestras de audio de la voz a clonar
│   ├── prueba1.mp4         #   ← Coloca aquí tus 4 muestras
│   ├── prueba2.mp4
│   ├── prueba3.mp4
│   └── prueba4.mp4
├── scripts/                # Guiones de texto para sintetizar
│   └── ejemplo.txt         #   ← Guion de ejemplo incluido
├── output/                 # Archivos generados
│   ├── prueba_1.wav        #   ← Audio clonado
│   └── fragments.json      #   ← Fragmentos procesados
├── src/                    # Código fuente principal
│   ├── __init__.py
│   ├── clone_test.py       # Sprint 1: Clonación de voz
│   └── script_processor.py # Sprint 2: Procesador de guiones
├── .gitignore
├── README.md
└── requirements.txt
```

---

## ▶️ Uso

### Prueba de concepto — Clonación de voz

#### 1. Preparar muestras de audio

Coloca 4 archivos MP4 con muestras de tu voz en `audio_samples/`:

```
audio_samples/
├── prueba1.mp4
├── prueba2.mp4
├── prueba3.mp4
└── prueba4.mp4
```

> 💡 **Tip:** Grabaciones de 10-30 segundos cada una, con voz clara y sin ruido
> de fondo, producen los mejores resultados.

#### 2. Activar el entorno virtual e instalar dependencias

```bash
# Windows
venv\Scripts\activate
pip install -r requirements.txt

# macOS/Linux
source venv/bin/activate
pip install -r requirements.txt
```

#### 3. Ejecutar el script de clonación

```bash
python -m src.clone_test
```

El script automáticamente:
1. **Convierte** los 4 MP4 → un único `audio_samples/mi_voz.wav` (mono, 22050 Hz)
2. **Descarga** el modelo XTTS-v2 (~1.8 GB, solo la primera vez)
3. **Sintetiza** el texto *"Hola, esta es una prueba de mi voz clonada"* en español
4. **Guarda** el resultado en `output/prueba_1.wav`

#### 4. Reproducir el resultado

```bash
# Windows
start output\prueba_1.wav

# macOS
open output/prueba_1.wav

# Linux
xdg-open output/prueba_1.wav
```

---

### Procesador de guiones

Divide textos largos en fragmentos óptimos para síntesis TTS (máx. 250 caracteres
por fragmento, respetando límites de oración).

```bash
# Procesar el guion de ejemplo
python -m src.script_processor scripts/ejemplo.txt

# Personalizar máximo de caracteres
python -m src.script_processor scripts/ejemplo.txt --max-chars 200

# Especificar archivo de salida
python -m src.script_processor scripts/mi_guion.txt --output output/mi_guion.json
```

El resultado se guarda en `output/fragments.json` con esta estructura:

```json
{
  "source_file": "ejemplo.txt",
  "max_chars": 250,
  "total_fragments": 9,
  "fragments": [
    {"index": 1, "text": "Bienvenidos al podcast...", "chars": 192},
    ...
  ]
}
```

---

## 🗺️ Roadmap

- [x] **Sprint 0** — Setup inicial del proyecto
- [x] **Sprint 1** — Prueba de concepto de clonación de voz (XTTS-v2)
- [x] **Sprint 2** — Procesamiento de guiones (fragmentación para TTS)
- [x] **Sprint 3** — Pipeline completo (guion → voz clonada)
- [ ] **Sprint 4** — Interfaz web (Gradio/Streamlit)

---

### Pipeline Completo (Narración de un Guion)

El pipeline de narración orquesta todo el proceso: divide el guion en fragmentos, sintetiza cada fragmento y los une en un solo archivo con silencios.

#### 1. Crear el archivo de referencia (una sola vez)
Si aún no lo has hecho, convierte tus MP4 en un WAV de referencia:
```bash
python -m src.clone_test
```

#### 2. Escribir el guion
Crea un archivo de texto con tu guion (ej. `scripts/mi_guion.txt`).

#### 3. Generar la narración
```bash
python -m src.generate_narration scripts/mi_guion.txt
```

Opciones avanzadas:
```bash
# Cambiar la voz de referencia y formato de salida
python -m src.generate_narration scripts/mi_guion.txt --speaker audio_samples/otra_voz.wav --format mp3

# Cambiar el tiempo de silencio entre fragmentos a 500ms
python -m src.generate_narration scripts/mi_guion.txt --silence 500
```

El resultado final se guardará en `output/narracion_final.wav` (o `.mp3`).

---

## 📄 Licencia

Este proyecto es de uso personal/educativo. Consulta la licencia de
[Coqui TTS](https://github.com/coqui-ai/TTS) para restricciones del modelo.