import re
from queue import Queue
from threading import Thread

import sounddevice as sd
import torch
from chatterbox.tts_turbo import ChatterboxTurboTTS

# CHATTERBOX
# Load the Turbo model
model = ChatterboxTurboTTS.from_pretrained(device="cuda", nano=True)
model.prepare_conditionals(r"Voices\Mccunnpt2.wav")
print("\n\nloaded\n\n")
VOLUME = 1

def _generate_chunks(text: str, chunks: Queue):
    sentences = re.split(r"(?<=[.!?。！？])\s*", text.strip())

    try:
        with torch.inference_mode():
            for sentence in filter(None, sentences):
                wav = model.generate(sentence)
                chunks.put(wav.squeeze(0).numpy())
    except Exception as error: #noqa
        chunks.put(error)
    finally:
        chunks.put(None)



async def read_text_chatterbox(text: str):
    chunks = Queue(maxsize=2)
    producer = Thread(target=_generate_chunks, args=(text, chunks), daemon=True)
    producer.start()


    with sd.OutputStream(
        samplerate=model.sr,
        channels=1,
        dtype="float32",
    ) as stream:
        while (chunk := chunks.get()) is not None:
            if isinstance(chunk, Exception):
                raise chunk
            stream.write((chunk * VOLUME).reshape(-1, 1))

    producer.join()
