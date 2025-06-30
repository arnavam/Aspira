from gtts import gTTS
import subprocess
import os
from pydub import AudioSegment
import time
import shutil
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
    subprocess.run(
        'cd Wav2Lip && python inference.py --checkpoint_path checkpoints/wav2lip_gan.pth --face "filelists/mona_clip.mp4" --audio "filelists/test.wav"',
        shell=True,
        check=True
    )



    # Define file paths
    old_file = os.path.join("..", "frontend", "public", "result_voice.mp4")
    new_file = os.path.join("Wav2Lip", "results", "result_voice.mp4")
    destination = os.path.join("..", "frontend", "public")

    # Remove the old file if it exists
    if os.path.exists(old_file):
        os.remove(old_file)

    # Copy the new file
    shutil.copy(new_file, destination)
