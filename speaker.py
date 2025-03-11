from gtts import gTTS
import os
from pydub import AudioSegment
import time
def convert(text):
    start_time=time.time()
    mp3_path = "file/temp_audio.mp3"
    output_wav_path="Wav2Lip/filelists/test.wav"
    tts = gTTS(text=text, lang='en', slow=False)  # slow=False for faster speech
    tts.save(mp3_path)

    # Convert mp3 to wav using pydub
    audio = AudioSegment.from_mp3(mp3_path)
    audio.export(output_wav_path, format="wav")


    print(time.time()-start_time)
    os.system('''cd Wav2Lip && python3 inference.py --checkpoint_path checkpoints/wav2lip_gan.pth --face "filelists/mona_clip.mp4" --audio "filelists/test.wav"''')
    os.system("ffplay Wav2Lip/results/result_voice.mp4")
