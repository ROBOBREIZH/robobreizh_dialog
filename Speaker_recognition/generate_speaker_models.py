from AudioRec import AudioRec

def store_speakers(audio_rec):
    audio_rec.store_speaker('Benjamin')
    audio_rec.store_speaker('Enrique')
    audio_rec.store_speaker('Mathieu')
    audio_rec.store_speaker('Sandratra')

if __name__ == "__main__":
    audio_rec = AudioRec()
    store_speakers(audio_rec)