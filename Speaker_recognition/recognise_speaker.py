from AudioRec import AudioRec

def audio_fn(name, audio_id):
    file_name = '%s/%s_audio_%d.wav' % (name, name, audio_id)
    return file_name

def test_recognition_speakers(audio_rec):
    print('Mathieu, 2')
    print(audio_rec.check_audio(audio_fn('Mathieu', 2)))

    print('\n\nMathieu, 4')
    print(audio_rec.check_audio(audio_fn('Mathieu', 4)))

    print('\n\nEnrique, 2') 
    print(audio_rec.check_audio(audio_fn('Enrique', 2)))

    print('\n\nEnrique, 5')
    print(audio_rec.check_audio(audio_fn('Enrique', 5)))

    print('\n\nBenjamin, 3')
    print(audio_rec.check_audio(audio_fn('Benjamin', 3)))

    print('\n\nBenjamin, 5')
    print(audio_rec.check_audio(audio_fn('Benjamin', 5)))

    print('\n\nSandratra, 2')
    print(audio_rec.check_audio(audio_fn('Sandratra', 2)))

    print('\n\nSandratra, 4')
    print(audio_rec.check_audio(audio_fn('Sandratra', 4)))

if __name__ == "__main__":
    audio_rec = AudioRec()
    test_recognition_speakers(audio_rec)