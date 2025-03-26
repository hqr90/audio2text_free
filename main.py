import os
import time
import tempfile
from pprint import pprint
import mimetypes
import speech_recognition as sr
from pydub import AudioSegment
from moviepy.editor import VideoFileClip
import yaml
import warnings
import random
from spleeter.separator import Separator
from spleeter.audio.adapter import AudioAdapter
import soundfile as sf
import os

# Cria um separador com o modelo de 2 stems (voz e acompanhamento)
separator = Separator('spleeter:2stems')

# Caminho do arquivo de entrada
input_audio_path = 'input.wav'
# Diretório de saída
output_directory = 'output'

# Realiza a separação
separator.separate_to_file(input_audio_path, output_directory)


warnings.filterwarnings("ignore", category=RuntimeWarning)


# Inicializa o reconhecedor
recognizer = sr.Recognizer()


import os
import time
import tempfile
from pprint import pprint
import mimetypes
import speech_recognition as sr
from pydub import AudioSegment
from moviepy.video.io.VideoFileClip import VideoFileClip
import yaml
import warnings
import random

# Inicializa o reconhecedor
recognizer = sr.Recognizer()

def convert_audio_to_wav(audio_file_path):
    '''
    Converte um arquivo de áudio para WAV.
    :param audio_file_path:
    :return:
    '''
    # Converte arquivos de áudio para WAV
    audio = AudioSegment.from_file(audio_file_path)
    fd, temp_wav_name = tempfile.mkstemp(suffix='.wav')
    os.close(fd)  # Fecha o descritor de arquivo
    audio.export(temp_wav_name, format='wav')
    return temp_wav_name

def extract_audio_from_video(video_file_path):
    '''
    Extrai o áudio de um arquivo de vídeo e salva como WAV.
    :param video_file_path:
    :return:
    '''
    # Extrai o áudio do vídeo e salva como arquivo WAV temporário
    video = VideoFileClip(video_file_path)
    fd, temp_wav_name = tempfile.mkstemp(suffix='.wav')
    os.close(fd)
    video.audio.write_audiofile(temp_wav_name)
    video.close()
    return temp_wav_name

def split_audio(file_path, chunk_length_ms=30000):  # 30 segundos
    '''
    Divide um arquivo de áudio em chunks de tamanho especificado.
    :param file_path:
    :param chunk_length_ms:
    :return:
    '''
    # Carrega o áudio completo
    audio = AudioSegment.from_wav(file_path)

    # Lista para armazenar os caminhos dos chunks
    chunks = []

    # Divide o áudio em chunks
    for i in range(0, len(audio), chunk_length_ms):
        chunk = audio[i:i + chunk_length_ms]
        fd, temp_chunk_name = tempfile.mkstemp(suffix='.wav')
        os.close(fd)
        chunk.export(temp_chunk_name, format='wav')
        chunks.append(temp_chunk_name)

    return chunks

def transcribe_audio(file_path, retries=3):
    '''
    Transcreve um arquivo de áudio usando a API do Google.
    :param file_path:
    :param retries:
    :return:
    '''
    for attempt in range(retries):
        try:
            with sr.AudioFile(file_path) as source:
                audio = recognizer.record(source)
                # Reconhece a fala usando a API do Google
                text = recognizer.recognize_google(audio, language="pt-BR")
                time.sleep(1)  # Sleep de 1 segundo após transcrição bem-sucedida
                return text
        except Exception as e:
            if attempt < retries - 1:
                print(f"Ocorreu um erro: {e}. Tentando novamente em 10 segundos...")
                time.sleep(10)  # Sleep de 10 segundos em caso de erro
                continue
            else:
                print(f"Transcrição falhou após {retries} tentativas.")
                return f"Ocorreu um erro: {e}"
    # Se chegar aqui, todas as tentativas falharam
    return "Transcrição falhou após múltiplas tentativas"

def transcribe_random_chunks(chunks, x):
    '''
    Transcreve x chunks aleatórios e descarta os demais.
    :param chunks: lista de caminhos dos chunks de áudio
    :param x: número de chunks a serem transcritos
    :return: lista de transcrições
    '''
    if x > len(chunks):
        x = len(chunks)  # Não pode transcrever mais chunks do que existem

    # Seleciona x chunks aleatórios
    selected_chunks = random.sample(chunks, x)

    transcriptions = []
    canTranscribe = False
    for chunk in selected_chunks:
        transcription = transcribe_audio(chunk)
        pprint(transcription)
        transcriptions.append(transcription)
        canTranscribe = True if transcription else False
        time.sleep(10)  # Espera 10 segundos entre as requisições

    # Remove todos os chunks, incluindo os não utilizados
    for chunk in chunks:
        os.remove(chunk)

    if canTranscribe:
        print(f"Transcrição de {x} chunks concluída com sucesso.")
    else:
        print(f"Não foi possível transcrever os chunks selecionados.")

    return transcriptions

def join_chunks(chunks, file_path):
    '''
    Junta os chunks em um único arquivo WAV e salva no caminho especificado.
    :param chunks:
    :param file_path:
    :return:
    '''
    # Carrega os chunks
    audio = AudioSegment.from_wav(chunks[0])
    for i in range(1, len(chunks)):
        chunk = AudioSegment.from_wav(chunks[i])
        audio = audio + chunk
    audio.export(file_path, format='wav')
    return audio

def process_file(file_path):
    '''
    Processa um arquivo de áudio ou vídeo, transcrevendo o áudio.
    :param file_path:
    :return:
    '''
    # Identifica o tipo de arquivo
    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type is None:
        print("Não foi possível identificar o tipo de arquivo.")
        return

    if mime_type.startswith('audio'):
        # É um arquivo de áudio
        if file_path.lower().endswith('.wav'):
            # Se for WAV, continua
            wav_file = file_path
        else:
            # Converte para WAV
            wav_file = convert_audio_to_wav(file_path)
    elif mime_type.startswith('video'):
        # É um arquivo de vídeo, extrai o áudio
        wav_file = extract_audio_from_video(file_path)
    else:
        print("Tipo de arquivo não suportado.")
        return

    # Divide o áudio em chunks
    chunks = split_audio(wav_file, chunk_length_ms=30000)  # 30 segundos

    # Transcreve cada chunk e remove o arquivo após a transcrição
    transcriptions = []
    canTranscribe = False
    for chunk in chunks:
        transcription = transcribe_audio(chunk)
        pprint(transcription)
        transcriptions.append(transcription)
        # Remove o arquivo chunk
        os.remove(chunk)
        time.sleep(10)  # Espera 10 segundos entre as requisições
        canTranscribe = True if transcription else False

    if canTranscribe:
        print(f"Transcrição do arquivo {file_path} concluída com sucesso.")
    else:
        print(f"Não foi possível transcrever o arquivo {file_path}.")

    # Salvar transcrição completa em arquivo yaml
    with open('transcription.yaml', 'w', encoding='utf-8') as file:
        yaml.dump(transcriptions, file, allow_unicode=True)

    # Remove o arquivo WAV temporário, se foi gerado neste processo
    if wav_file != file_path:
        os.remove(wav_file)

    # Junta as transcrições
    full_transcription = ' '.join(transcriptions)

    # Imprime a transcrição completa
    print(full_transcription)
    return full_transcription

def process_file_random_chunks(file_path, x=5):
    '''
    Processa um arquivo de áudio ou vídeo, transcrevendo x chunks aleatórios.
    :param file_path:
    :param x:
    :return:
    '''
    # Identifica o tipo de arquivo
    '''
       Processa um arquivo de áudio ou vídeo, transcrevendo o áudio.
       :param file_path:
       :return:
       '''
    # Identifica o tipo de arquivo
    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type is None:
        print("Não foi possível identificar o tipo de arquivo.")
        return

    if mime_type.startswith('audio'):
        # É um arquivo de áudio
        if file_path.lower().endswith('.wav'):
            # Se for WAV, continua
            wav_file = file_path
        else:
            # Converte para WAV
            wav_file = convert_audio_to_wav(file_path)
    elif mime_type.startswith('video'):
        # É um arquivo de vídeo, extrai o áudio
        wav_file = extract_audio_from_video(file_path)
    else:
        print("Tipo de arquivo não suportado.")
        return

    # Divide o áudio em chunks
    chunks = split_audio(wav_file, chunk_length_ms=30000)  # 30 segundos

    # Transcreve cada chunk e remove o arquivo após a transcrição
    transcriptions = []
    canTranscribe = False
    for chunk in chunks:
        transcription = transcribe_random_chunks(chunk, x)
        pprint(transcription)
        transcriptions.append(transcription)
        # Remove o arquivo chunk
        os.remove(chunk)
        time.sleep(10)  # Espera 10 segundos entre as requisições
        canTranscribe = True if transcription else False

    if canTranscribe:
        print(f"Transcrição do arquivo {file_path} concluída com sucesso.")
    else:
        print(f"Não foi possível transcrever o arquivo {file_path}.")

    # Salvar transcrição completa em arquivo yaml
    with open('transcription.yaml', 'w', encoding='utf-8') as file:
        yaml.dump(transcriptions, file, allow_unicode=True)

    # Remove o arquivo WAV temporário, se foi gerado neste processo
    if wav_file != file_path:
        os.remove(wav_file)

    # Junta as transcrições
    full_transcription = ' '.join(transcriptions)

    # Imprime a transcrição completa
    print(full_transcription)
    return full_transcription

