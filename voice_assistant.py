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

from requests_to_google import get_weather_information

hours_units = (('час', 'часа', 'часов'), 'm')
minutes_units = (('минута', 'минуты', 'минут'), 'f')
temperature_units = (('градус', 'градуса', 'градусов'), 'm')

ask_time_commands = ['сколько сейчас времени', 'скажи время', 'время', 'сколько времени']
ask_weather_commands = ['расскажи о погоде', 'погода', 'какая погода']
help_commands = ['помощь']

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
            print("Recognition...")
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
    print("Время: ", current_time)
    hour_str = num2text(hour, hours_units)
    min_str = num2text(min, minutes_units)
    voice_acting(hour_str + min_str + '.')


def say_weather():
    temperature, sky = get_weather_information()
    if temperature and sky:
        temperature_str = num2text(int(temperature), temperature_units)
        print(f'Температура: {temperature}')
        print(f'Осадки: {sky}')
        voice_acting(temperature_str + '.' + sky + '.')


def help_():
    print('Чтобы получить информацию о возможностях помощника скажите:', ', '.join(help_commands))
    print('Чтобы узнать время скажите одну из следующих команд:', ', '.join(ask_time_commands))
    print('Чтобы узнать погоду скажите одну из следующих команд:', ', '.join(ask_weather_commands))
    message = 'Я могу рассказать о погоде или сказать текущее время.'
    voice_acting(message)


if __name__ == '__main__':
    while True:
        recognized_text = recognition()
        print(recognized_text)
        if recognized_text in ask_time_commands:
            say_current_time()
        elif recognized_text in ask_weather_commands:
            say_weather()
        elif recognized_text in help_commands:
            help_()
        elif recognized_text:
            voice_acting(recognized_text + '.')
