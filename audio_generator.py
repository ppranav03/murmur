import numpy as np
import soundfile as sf
from kokoro import KPipeline

SAMPLE_RATE = 24000  # Kokoro natively outputs 24kHz audio

def _pipeline():
    pipeline = KPipeline(lang_code='a')
    return pipeline

def create_audio(input_str : str = """TLDR: Massage Guns
Massage guns, also known as percussion massagers or power massagers,
are handheld devices that use rapid vibrations to relieve muscle tension and pain.
They typically feature interchangeable heads and adjustable speed settings.
""", filename: str = "output.wav"):
    
    pipeline = _pipeline()

    print("Generating audio... (This will download the 300MB model on the first run)")
    generator = pipeline(input_str, voice='af_heart', speed=1, split_pattern=r'\n+')

    # Kokoro yields one chunk per paragraph; join them with a short pause in between
    pause = np.zeros(int(SAMPLE_RATE * 0.4), dtype=np.float32)
    chunks = []
    for gs, ps, audio in generator:
        chunks.append(np.asarray(audio, dtype=np.float32))
        chunks.append(pause)

    sf.write(filename, np.concatenate(chunks[:-1]), SAMPLE_RATE)
    print(f"Saved audio to {filename}")


if __name__ == "__main__":
    create_audio()
