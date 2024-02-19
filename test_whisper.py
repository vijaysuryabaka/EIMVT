import pyaudio
import numpy as np
import whisper

# Load the Whisper model
model = whisper.load_model("base")

RATE = 16000
CHUNK = 1024  # Number of audio frames per buffer

def listen_and_transcribe():
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16,
                    channels=1,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)

    print("Listening...")

    try:
        while True:
            frames = []
            for _ in range(0, int(RATE / CHUNK * 5)):  # Record 5 seconds of audio
                data = stream.read(CHUNK)
                frames.append(np.frombuffer(data, np.int16))
            
            # Concatenate all frames and convert to float
            audio_np = np.hstack(frames)
            audio_float = audio_np.astype(np.float32) / np.iinfo(np.int16).max  # Convert to float32 and normalize

            # Pass the floating point audio data to Whisper
            result = model.transcribe(audio_float)
            print(f"Detected language: {result['language']}")
            print(f"Transcript: {result['text']}")

            # Break or continue here based on your application's needs
            break

    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()

listen_and_transcribe()
