from gradio_client import Client
import time

try:
    print("Conectando al cliente...")
    client = Client("http://127.0.0.1:7860/")
    
    print("Realizando la inferencia...")
    start = time.time()
    result = client.predict(
		"c:/Antigravity-projects/voice-clone-studio/audio_samples/mi_voz.wav",	# str (filepath or URL to file) in 'Sube o graba un audio de referencia (WAV/MP4)' Audio component
		"Esta es una prueba de la interfaz de Gradio, espero que funcione correctamente sin errores.",	# str in 'Escribe o pega el texto aquí...' Textbox component
		300,	# int | float (numeric value between 0 and 2000) in 'Silencio entre oraciones (ms)' Slider component
		250,	# int | float (numeric value between 50 and 400) in 'Máx. caracteres por fragmento (optimización TTS)' Slider component
		"es",	# str in 'Idioma' Dropdown component
		api_name="/synthesize"
    )
    print("Resultado exitoso:")
    print(result)
    print(f"Tiempo: {time.time() - start:.2f}s")
except Exception as e:
    print(f"Error: {e}")
