import gradio as gr
import os
import shutil
import tempfile
import sys
import io
from pathlib import Path

# Forzar UTF-8 en stdout/stderr para evitar errores con emojis en Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from src.script_processor import clean_text, split_into_fragments, DEFAULT_MAX_CHARS
from src.voice_engine import VoiceEngine
from src.generate_narration import join_audio_fragments

def process_and_synthesize(speaker_audio, script_text, silence_ms, max_chars, language, temperature, speed, repetition_penalty):
    """
    Función principal de Gradio para procesar el texto y generar la narración.
    """
    if not speaker_audio:
        raise gr.Error("Debes proporcionar un audio de referencia.")
    
    if not script_text.strip():
        raise gr.Error("El guion no puede estar vacío.")

    # 1. Preparar texto
    cleaned_text = clean_text(script_text)
    fragments = split_into_fragments(cleaned_text, max_chars=int(max_chars))
    
    if not fragments:
        raise gr.Error("No se pudieron generar fragmentos a partir del texto.")

    # 2. Inicializar Motor de Voz
    try:
        # speaker_audio es el path al archivo subido
        engine = VoiceEngine(speaker_wav=speaker_audio, language=language)
    except Exception as e:
        raise gr.Error(f"Error al inicializar el motor de voz: {str(e)}")

    # 3. Crear directorio temporal para los fragmentos
    temp_dir = Path(tempfile.mkdtemp(prefix="voice_clone_"))
    
    try:
        # 4. Sintetizar fragmentos
        fragment_wavs = engine.synthesize_batch(
            fragments=fragments,
            output_dir=temp_dir,
            language=language,
            temperature=float(temperature),
            speed=float(speed),
            repetition_penalty=float(repetition_penalty)
        )
        
        # 5. Unir audios
        # Guardaremos el final en el mismo temp_dir pero lo devolvemos
        output_file = temp_dir / "narracion_final.wav"
        
        join_audio_fragments(
            fragment_paths=fragment_wavs,
            output_path=output_file,
            silence_ms=int(silence_ms),
            export_format="wav"
        )
        
        return str(output_file)

    except Exception as e:
        raise gr.Error(f"Error durante la generación: {str(e)}")
        
    finally:
        # Nota: Gradio se encarga de servir el archivo.
        # Podríamos borrar los fragmentos intermedios para ahorrar espacio.
        for wav in temp_dir.glob("frag_*.wav"):
            wav.unlink(missing_ok=True)


# ──────────────────────────────────────────────────────────────
# Interfaz de Gradio
# ──────────────────────────────────────────────────────────────

with gr.Blocks(title="Voice Clone Studio", theme=gr.themes.Soft()) as app:
    gr.Markdown(
        """
        # 🎙️ Voice Clone Studio
        **Sprint 4: Interfaz Web.** Genera narraciones completas con tu propia voz clonada.
        """
    )
    
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### 1. Voz de Referencia")
            speaker_input = gr.Audio(
                label="Sube o graba un audio de referencia (WAV/MP4)",
                type="filepath",
            )
            
            gr.Markdown("### 3. Configuración")
            silence_input = gr.Slider(
                minimum=0, maximum=2000, value=300, step=50,
                label="Silencio entre oraciones (ms)"
            )
            max_chars_input = gr.Slider(
                minimum=50, maximum=400, value=DEFAULT_MAX_CHARS, step=10,
                label="Máx. caracteres por fragmento (optimización TTS)"
            )
            language_input = gr.Dropdown(
                choices=["es", "en", "fr", "de", "it", "pt", "pl", "tr", "ru", "nl", "cs", "ar", "zh-cn", "ja", "hu", "ko"],
                value="es",
                label="Idioma"
            )
            
            with gr.Accordion("Configuración avanzada", open=False):
                temp_input = gr.Slider(
                    minimum=0.1, maximum=1.0, value=0.7, step=0.05,
                    label="Temperature (variabilidad)"
                )
                speed_input = gr.Slider(
                    minimum=0.5, maximum=1.5, value=1.0, step=0.05,
                    label="Velocidad de habla (speed)"
                )
                rep_pen_input = gr.Slider(
                    minimum=1.0, maximum=10.0, value=2.0, step=0.5,
                    label="Repetition penalty (evita monotonía)"
                )
                reset_btn = gr.Button("Restaurar valores por defecto", size="sm")
                
                def reset_advanced_config():
                    return 0.7, 1.0, 2.0
                
                reset_btn.click(
                    fn=reset_advanced_config,
                    inputs=[],
                    outputs=[temp_input, speed_input, rep_pen_input]
                )
            
            generate_btn = gr.Button(" Generar Narración", variant="primary")

        with gr.Column(scale=2):
            gr.Markdown("### 2. Guion a Narrar")
            
            script_upload = gr.File(
                label="Sube un archivo de texto (.txt) con el guion (Opcional)",
                file_types=[".txt"],
            )
            
            script_input = gr.Textbox(
                label="O escribe o pega el texto aquí...",
                lines=12,
                placeholder="Hola, esta es una prueba de mi voz clonada en la nueva interfaz web."
            )
            
            def load_script_file(file_obj):
                if file_obj is None:
                    return ""
                try:
                    # En Gradio 3.x file_obj tiene el atributo 'name' para la ruta
                    file_path = file_obj.name
                    with open(file_path, "r", encoding="utf-8") as f:
                        return f.read()
                except Exception as e:
                    return f"Error leyendo el archivo: {e}"
                    
            script_upload.change(
                fn=load_script_file,
                inputs=[script_upload],
                outputs=[script_input]
            )
            
            gr.Markdown("### 4. Resultado")
            audio_output = gr.Audio(
                label="Audio Generado",
                type="filepath",
                interactive=False
            )
            
    # Evento
    generate_btn.click(
        fn=process_and_synthesize,
        inputs=[speaker_input, script_input, silence_input, max_chars_input, language_input, temp_input, speed_input, rep_pen_input],
        outputs=[audio_output],
        api_name="synthesize"
    )

if __name__ == "__main__":
    app.launch(server_name="127.0.0.1", server_port=7860, share=False)
