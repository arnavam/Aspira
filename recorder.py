import speech_recognition as sr
import time

def speech():
    r = sr.Recognizer() 
    start_time = time.time()



    with sr.Microphone() as source:
        print("Talk") 
        audio= r.listen(source,timeout=10,phrase_time_limit=50)
        print("Time over, thanks")
        #recognizer.energy_threshold = 4000  # Increase this value if there's too much background noise
        
        
        try:
            audio_text=r.recognize_google(audio)
            # using google speech recognition
            print(f"Text: {audio_text}")
            end_time = time.time()
            print(f"F-string time: {end_time - start_time} seconds")
            return audio_text
        except:
            print("Sorry, I did not get that")
            return("Not found")
# import pyaudio
# import wave
# import numpy as np
# import time

# def record_audio_until_silence(output_filename, silence_threshold=1000, silence_duration=3, rate=44100, channels=1, chunk_size=1024):
#     """
#     Records audio from the microphone and stops when silence is detected for a specified duration.
    
#     Parameters:
#     - output_filename (str): The name of the output file (e.g., 'output.wav').
#     - silence_threshold (int): The threshold below which sound is considered silence. Default is 1000.
#     - silence_duration (int): The duration (in seconds) of silence to detect before stopping the recording. Default is 3 seconds.
#     - rate (int): The sample rate (e.g., 44100 Hz).
#     - channels (int): Number of audio channels (1 for mono, 2 for stereo).
#     - chunk_size (int): The size of each chunk of audio data.

#     Returns:
#     None
#     """
    
#     # Initialize the PyAudio object
#     p = pyaudio.PyAudio()

#     # Open the stream for audio input
#     stream = p.open(format=pyaudio.paInt16,  # Audio format (16-bit PCM)
#                     channels=channels,        # Number of audio channels
#                     rate=rate,                # Sample rate
#                     input=True,               # Input stream (microphone)
#                     frames_per_buffer=chunk_size)  # Number of frames per buffer

#     print("Recording...")

#     frames = []
#     silent_chunks = 0  # Count consecutive silent chunks

#     while True:
#         # Read data from the stream
#         data = stream.read(chunk_size)
#         frames.append(data)

#         # Convert the data to numpy array for analysis
#         audio_data = np.frombuffer(data, dtype=np.int16)
        
#         # Calculate the amplitude (volume) of the audio signal
#         amplitude = np.linalg.norm(audio_data)  # Euclidean norm (L2 norm) of the signal
        
#         # If the amplitude is below the silence threshold, increment the silent_chunks counter
#         if amplitude < silence_threshold:
#             silent_chunks += 1
#         else:
#             silent_chunks = 0  # Reset if sound is detected

#         # If silence lasts for the specified duration, stop recording
#         if silent_chunks > silence_duration * (rate / chunk_size):
#             print("Silence detected, stopping recording.")
#             break

#     # Stop and close the stream
#     stream.stop_stream()
#     stream.close()
#     p.terminate()

#     # Save the recorded audio as a .wav file
#     with wave.open(output_filename, 'wb') as wf:
#         wf.setnchannels(channels)       # Set number of channels
#         wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))  # Sample width (2 bytes for 16-bit)
#         wf.setframerate(rate)           # Set the sample rate (Hz)
#         wf.writeframes(b''.join(frames))  # Write audio data to the file

#     print(f"Audio saved to {output_filename}")


# # Example usage
# if __name__ == '__main__':
#     record_audio_until_silence("recorded_audio.wav", silence_threshold=1000, silence_duration=3)  # Stops after 3 seconds of silence
