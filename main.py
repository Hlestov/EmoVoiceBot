import logging
import os
from pathlib import Path

import nest_asyncio
nest_asyncio.apply()

from transformers import AutoConfig, AutoModel, Wav2Vec2FeatureExtractor
from aiogram import Bot, Dispatcher, executor, types
from utils import predict, ogg2wav


# initialize model
TRUST = True

config = AutoConfig.from_pretrained('Aniemore/wav2vec2-xlsr-53-russian-emotion-recognition', trust_remote_code=TRUST)
model_ = AutoModel.from_pretrained("Aniemore/wav2vec2-xlsr-53-russian-emotion-recognition", trust_remote_code=TRUST)
feature_extractor = Wav2Vec2FeatureExtractor.from_pretrained("Aniemore/wav2vec2-xlsr-53-russian-emotion-recognition")

device = "cpu"
model_.to(device)


# setup bot
API_TOKEN = '<PASTE YOUR TOKEN>'

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)


@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.reply("""Привет! Я бот, который может определить эмоциональный
     окрас голосовых сообщений. Просто отправьте мне голосовое сообщение, и я 
     верну вам мой анализ вашего настроения и эмоционального состояния. """)


async def get_answer(file: types.File, file_name: str, path: str):
    Path(f"{path}").mkdir(parents=True, exist_ok=True)

    # Save the voice message file
    ogg_path = f"{path}/{file_name}"
    wav_path = os.path.splitext(ogg_path)[0] + '.wav'
    await bot.download_file(file_path=file.file_path, destination=ogg_path)

    # Convert the file from Ogg to Wav format
    ogg2wav(ogg_path)
    
    # Remove the Ogg file
    os.remove(ogg_path)
    
    # Generate predictions for the Wav file
    prediction = predict(wav_path, sampling_rate=16000)
    
    # Remove the Wav file
    os.remove(wav_path)
    
    # Create a message with the emotions and scores
    answer = ''
    for emotion in prediction:
        answer += emotion['Emotion'] + ' -> ' + emotion['Score'] + '\n'

    return answer


@dp.message_handler(content_types=[types.ContentType.VOICE])
async def voice_message_handler(message: types.Message):
    voice = await message.voice.get_file()
    path = "/content/voices"

    emotions = await get_answer(file=voice, file_name=f"{voice.file_id}.ogg", path=path)
    await message.reply(emotions)


if name == '__main__':
    executor.start_polling(dp, skip_updates=True)
