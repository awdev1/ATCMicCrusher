## Packages
import pyaudio
import customtkinter as ctk
import numpy as np
import scipy.signal as signal

## Filters

RATE = 44100
CHUNK = 1024
TONE_FREQ = 400
AMPLITUDE = 0.03
THRESHOLD = 0.02

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


## GUI
class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.inputs = pyaudio
        self.streaming = False

        self.title("24Audio")
        self.geometry("400x350")
        self.resizable(False, False)

        self.main_frame = ctk.CTkFrame(self, corner_radius=15)
        self.main_frame.pack(pady=20, padx=20, fill="both", expand=True)

        self.title_label = ctk.CTkLabel(self.main_frame, text="24Audio", font=("Roboto", 30, "bold"))
        self.title_label.pack(pady=20)

        self.mic_label = ctk.CTkLabel(self.main_frame, text="Select Input Microphone:")
        self.mic_label.pack(pady=10)

        self.mic_dropdown = ctk.CTkComboBox(self.main_frame, values=self.list_microphone_inputs())
        self.mic_dropdown.pack(pady=10)

        self.start_button = ctk.CTkButton(self.main_frame, text="Start", command=self.start_audio_stream)
        self.start_button.pack(pady=20)

        self.status_label = ctk.CTkLabel(self.main_frame, text="Status: Sleeping 😴", text_color="gray")
        self.status_label.pack(pady=10)
    
    def list_microphone_inputs(self):
        p = pyaudio.PyAudio()

        mic_list = []
        for i in range(p.get_device_count()):
            device_info = p.get_device_info_by_index(device_index=i)
            if device_info["maxInputChannels"] > 0:
               mic_list.append(f"{device_info['name']} (Index: {i})")
               print(f"{device_info['name']} (Index: {i}) | {device_info['maxInputChannels']} input, {device_info['maxOutputChannels']} output")

        p.terminate()
        return mic_list if mic_list else ["No Microphones Found"]
    
    def find_vb_audio_cable(self):
        p = pyaudio.PyAudio()
        vb_index = None

        for i in range(p.get_device_count()):
            device_info = p.get_device_info_by_index(i)
            if "CABLE Output (VB-Audio Virtual" in device_info["name"]:
                vb_index = i
                break
        p.terminate()
        return vb_index

    def start_audio_stream(self):
        selected_mic = self.mic_dropdown.get()
        mic_index = int(selected_mic.split("Index: ")[-1].strip(")"))
        audio_cable_output = self.find_vb_audio_cable()

        print(mic_index)
        print(audio_cable_output)

        self.status_label.configure(text="Status: Streaming Audio! ✅", text_color="green")
        self.start_button.configure(text="Stop")

        if self.streaming is True:
            self.status_label.configure(text="Status: Sleeping 😴", text_color="gray")
            self.streaming = False

            self.start_button.configure(text="Start")
            self.p.terminate()
            return
        
        if not selected_mic:
            self.status_label.configure(text="Status: No microphone selected ❌", text_color="red")
            self.p.terminate()
            return
        
        if not audio_cable_output:
            self.status_label.configure(text="Status: Audio cable not installed or couldn't be found. ❌", text_color="red")
            self.p.terminate()
            return

        self.streaming = True
        self.p = pyaudio.PyAudio()

        self.stream = self.p.open(format=pyaudio.paInt16,
            channels=1,
            rate=RATE,
            input=True,
            output=True,
            frames_per_buffer=CHUNK,
            output_device_index=audio_cable_output,
            input_device_index=mic_index
        )
        
        
        while self.streaming is True: ## Audio loop
            data = self.stream.read(CHUNK, exception_on_overflow=False)
            samples = np.frombuffer(data, dtype=np.int16).astype(np.float32)
            
            samples /= 32768.0 
    
            filtered_samples = highpass_filter(samples)
            filtered_samples = lowpass_filter(filtered_samples)

            phase = 0
            
    
            if np.max(np.abs(filtered_samples)) > THRESHOLD:
                t = np.arange(CHUNK) / RATE
                phase_increment = (2 * np.pi * TONE_FREQ) / RATE
                tone = AMPLITUDE * np.sin(phase + 2 * np.pi * TONE_FREQ * t)
                phase = (phase + phase_increment * CHUNK) % (2 * np.pi)  
                envelope = np.linspace(0, 1, CHUNK)  # noqa: F841
                filtered_samples += tone

            filtered_samples *= 32768.0 
            self.stream.write(filtered_samples.astype(np.int16).tobytes())
        


if __name__ == "__main__":
    app = App()
    app.mainloop()