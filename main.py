import os
import time
import tempfile
from pprint import pprint
import mimetypes
import speech_recognition as sr
from pydub import AudioSegment
from moviepy.editor import VideoFileClip
import yaml

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
    chunks = split_audio(wav_file, chunk_length_ms=55000)

    # Transcreve cada chunk e remove o arquivo após a transcrição
    transcriptions = []
    canTranscribe = False
    for chunk in chunks:
        tries = 3
        t = 0
        while t <= tries:
            try:
                transcription = transcribe_audio(chunk)
                pprint(transcription)
                transcriptions.append(transcription)
                # Remove o arquivo chunk
                os.remove(chunk)
                time.sleep(1)
                canTranscribe = True
            except:
                t += 1
                time.sleep(20)
                canTranscribe = False
                continue
    if canTranscribe:
        print(f"Transcrição do arquivo {file_path} concluída com sucesso.")
        # Salvar transcrição completa em arquivo yaml
        with open('transcription.yaml', 'w') as file:
            yaml.dump(transcriptions, file)
    else:
        print(f"Não foi possível transcrever o chunk {chunk} após {tries} tentativas.")
        # Salvar transcrição parcial em arquivo yaml
        with open('transcription.yaml', 'w') as file:
            yaml.dump(transcriptions, file)
        # Junta os chuncks não salvos em um arquivo WAV e salva para transcrição posterior com o mesmo nome file_path
        join_chunks(chunks, file_path)








    # Remove o arquivo WAV temporário, se foi gerado neste processo
    if wav_file != file_path:
        os.remove(wav_file)

    # Junta as transcrições
    full_transcription = ' '.join(transcriptions)

    # Imprime a transcrição completa
    print(full_transcription)
    return full_transcription

def convert_audio_to_wav(audio_file_path):
    '''
    Converte um arquivo de áudio para WAV.
    :param audio_file_path:
    :return:
    '''
    # Converte arquivos de áudio para WAV
    audio = AudioSegment.from_file(audio_file_path)
    temp_wav = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
    audio.export(temp_wav.name, format='wav')
    return temp_wav.name

def extract_audio_from_video(video_file_path):
    '''
    Extrai o áudio de um arquivo de vídeo e salva como WAV.
    :param video_file_path:
    :return:
    '''
    # Extrai o áudio do vídeo e salva como arquivo WAV temporário
    video = VideoFileClip(video_file_path)
    temp_wav = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
    video.audio.write_audiofile(temp_wav.name)
    video.close()
    return temp_wav.name

def split_audio(file_path, chunk_length_ms=55000):
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
        temp_chunk = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
        chunk.export(temp_chunk.name, format='wav')
        chunks.append(temp_chunk.name)

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
                print(f"Ocorreu um erro: {e}. Tentando novamente em 20 segundos...")
                time.sleep(20)  # Sleep de 20 segundos em caso de erro
                continue
            else:
                print(f"Transcrição falhou após {retries} tentativas.")
                return f"Ocorreu um erro: {e}"
    # Se chegar aqui, todas as tentativas falharam
    return "Transcrição falhou após múltiplas tentativas"

# Inicializa o reconhecedor
recognizer = sr.Recognizer()

# Exemplo de uso
file_1 = r"F:\Gravações\2024-11-07 10-54-00.mp4"
transcricao = process_file(file_1)
