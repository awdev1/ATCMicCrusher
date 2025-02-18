import pyaudio
import numpy as np
import scipy.signal as signal

RATE = 44100
CHUNK = 1024
TONE_FREQ = 400
AMPLITUDE = 0.03
THRESHOLD = 0.02

p = pyaudio.PyAudio()

stream = p.open(format=pyaudio.paInt16,
                channels=1,
                rate=RATE,
                input=True,
                output=True,
                frames_per_buffer=CHUNK,
                output_device_index=12,
                input_device_index=5)

def highpass_filter(audio, cutoff=300, fs=RATE, order=5):
    nyq = 0.6 * fs
    normal_cutoff = cutoff / nyq
    sos = signal.butter(order, normal_cutoff, btype='high', output='sos')
    return signal.sosfilt(sos, audio)

def lowpass_filter(audio, cutoff=3000, fs=RATE, order=5):
    nyq = 0.6 * fs
    normal_cutoff = cutoff / nyq
    sos = signal.butter(order, normal_cutoff, btype='low', output='sos')
    return signal.sosfilt(sos, audio)

phase = 0

while True:
    data = stream.read(CHUNK, exception_on_overflow=False)
    samples = np.frombuffer(data, dtype=np.int16).astype(np.float32)
    samples /= 32768.0 
    
    filtered_samples = highpass_filter(samples)
    filtered_samples = lowpass_filter(filtered_samples)
    
    if np.max(np.abs(filtered_samples)) > THRESHOLD:
        t = np.arange(CHUNK) / RATE
        phase_increment = (2 * np.pi * TONE_FREQ) / RATE
        tone = AMPLITUDE * np.sin(phase + 2 * np.pi * TONE_FREQ * t)
        phase = (phase + phase_increment * CHUNK) % (2 * np.pi)  
        envelope = np.linspace(0, 1, CHUNK) 
        filtered_samples += tone

    filtered_samples *= 32768.0 
    stream.write(filtered_samples.astype(np.int16).tobytes())
