import json
import queue
import sys
import time
from datetime import datetime
import wave

import speech_recognition
import torch
import sounddevice as sd
from num2t4ru import num2text
from vosk import Model, KaldiRecognizer

hours_units = (('час', 'часа', 'часов'), 'm')
minutes_units = (('минута', 'минуты', 'минут'), 'f')

ask_time_commands = ['сколько сейчас времени', 'скажи время', 'время', 'сколько времени']

language = 'ru'
model_id = 'ru_v3'
sample_rate = 48000
speaker = 'baya'
put_accent = True
put_yo = True
device = torch.device('cpu')

recognizer = speech_recognition.Recognizer()
microphone = speech_recognition.Microphone()

model, _ = torch.hub.load(repo_or_dir='snakers4/silero-models',
                          model='silero_tts',
                          language=language,
                          speaker=model_id)

model.to(device)

model_for_recognition = Model("model")
samplerate = 16000
device = 1

q = queue.Queue()


def callback(indata, status):
    if status:
        print(status, file=sys.stderr)
    q.put(bytes(indata))


def offline_recognition():
    recognized_data = ''
    wave_audio_file = wave.open("microphone-results.wav", "rb")
    offline_recognizer = KaldiRecognizer(model_for_recognition, wave_audio_file.getframerate())
    data = wave_audio_file.readframes(wave_audio_file.getnframes())
    if len(data) > 0:
        if offline_recognizer.AcceptWaveform(data):
            recognized_data = offline_recognizer.Result()
            recognized_data = json.loads(recognized_data)
            recognized_data = recognized_data["text"]

    return recognized_data


def recognition():
    with microphone:
        recognized_text = ''
        recognizer.adjust_for_ambient_noise(source=microphone, duration=1)
        print('Listening...')
        audio = recognizer.listen(source=microphone)
        with open("microphone-results.wav", "wb") as file:
            file.write(audio.get_wav_data())
        try:
            print("Started recognition...")
            recognized_text = recognizer.recognize_google(audio_data=audio, language=language).lower()
        except speech_recognition.RequestError:
            recognized_text = offline_recognition()
        except:
            pass

        return recognized_text


def voice_acting(text: str):
    audio = model.apply_tts(text=text,
                            speaker=speaker,
                            sample_rate=sample_rate,
                            put_accent=put_accent,
                            put_yo=put_yo)

    sd.play(audio, sample_rate)
    time.sleep(len(audio) / sample_rate)
    sd.stop()


def say_current_time():
    now = datetime.now()
    current_time = now.strftime("%H:%M")
    hour = int(now.strftime("%H"))
    min = int(now.strftime("%M"))
    print("Текущее время: ", current_time)
    hour_str = num2text(hour, hours_units)
    min_str = num2text(min, minutes_units)
    voice_acting(hour_str + min_str)


if __name__ == '__main__':
    while True:
        recognized_text = recognition()
        print(recognized_text)
        if recognized_text in ask_time_commands:
            say_current_time()
        elif recognized_text:
            voice_acting(recognized_text)
