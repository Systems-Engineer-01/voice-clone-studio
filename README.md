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
├── audio_samples/      # Muestras de audio de la voz a clonar
├── scripts/            # Scripts utilitarios (preprocesamiento, conversión, etc.)
├── output/             # Audio generado por el modelo
├── src/                # Código fuente principal del pipeline
│   └── __init__.py
├── .gitignore
├── README.md
└── requirements.txt
```

---

## ▶️ Uso

> 🚧 **En construcción** — El pipeline de clonación se implementará en los
> próximos sprints.

```bash
# Placeholder: ejecutar el pipeline principal
python -m src.main --input audio_samples/mi_muestra.wav --text "Hola mundo"
```

---

## 🗺️ Roadmap

- [x] **Sprint 0** — Setup inicial del proyecto
- [ ] **Sprint 1** — Módulo de carga y validación de audio
- [ ] **Sprint 2** — Integración con XTTS-v2 para síntesis
- [ ] **Sprint 3** — CLI interactivo y exportación de resultados
- [ ] **Sprint 4** — Interfaz web (Gradio/Streamlit)

---

## 📄 Licencia

Este proyecto es de uso personal/educativo. Consulta la licencia de
[Coqui TTS](https://github.com/coqui-ai/TTS) para restricciones del modelo.