import os
import yt_dlp
from pydub import AudioSegment

DOWNLOAD_DIR = "downloades"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


def download_youtube_audio(url: str) -> str:
    """Download YouTube audio and convert it to WAV."""

    output_path = os.path.join(
        DOWNLOAD_DIR,
        "%(id)s.%(ext)s"
    )

    ydl_opts = {
        "format": "bestaudio[ext=m4a]/bestaudio/best",

        "outtmpl": output_path,

        "noplaylist": True,

        "quiet": False,

        # Use the web client.
        # Do NOT force Android because it can trigger SABR/403 errors.
        "extractor_args": {
            "youtube": {
                "player_client": ["web"],
            }
        },

        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
                "preferredquality": "192",
            }
        ],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

            filename = ydl.prepare_filename(info)

            # yt-dlp may return .webm, .m4a, etc.
            wav_path = os.path.splitext(filename)[0] + ".wav"

    except yt_dlp.utils.DownloadError as e:
        raise RuntimeError(
            "YouTube download failed. "
            "YouTube may be blocking the Streamlit server request. "
            f"Details: {e}"
        ) from e

    if not os.path.exists(wav_path):
        raise FileNotFoundError(
            f"WAV file was not created: {wav_path}"
        )

    return wav_path


def convert_to_wav(input_path: str) -> str:
    """Convert a local audio/video file to WAV."""

    output_path = os.path.splitext(input_path)[0] + "_converted.wav"

    audio = AudioSegment.from_file(input_path)

    # Whisper works well with mono 16 kHz audio.
    audio = audio.set_channels(1)
    audio = audio.set_frame_rate(16000)

    audio.export(output_path, format="wav")

    return output_path


def chunk_audio(wav_path: str, chunk_minutes: int = 10) -> list:
    """Split WAV audio into smaller chunks."""

    audio = AudioSegment.from_wav(wav_path)

    chunk_ms = chunk_minutes * 60 * 1000

    chunks = []

    for i, start in enumerate(range(0, len(audio), chunk_ms)):
        chunk = audio[start:start + chunk_ms]

        chunk_path = f"{wav_path}_chunk_{i}.wav"

        chunk.export(chunk_path, format="wav")

        chunks.append(chunk_path)

    return chunks


def process_input(source: str) -> list:
    """Process a YouTube URL or local audio/video file."""

    if source.startswith(("http://", "https://")):

        print("Detected YouTube URL. Downloading audio...")

        wav_path = download_youtube_audio(source)

    else:

        print("Detected local file. Converting to WAV...")

        wav_path = convert_to_wav(source)

    print("Chunking audio...")

    chunks = chunk_audio(wav_path)

    print(f"Audio ready — {len(chunks)} chunk(s) created.")

    return chunks