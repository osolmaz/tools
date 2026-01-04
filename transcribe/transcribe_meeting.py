"""
Takes a meeting recording (audio or video) and transcribes it into a structured format.
Supports video files (MP4, etc.) by extracting audio first.

Why translate with Gemini 2.5 Pro and do the write-up with GPT-4.5?

Because IMO Gemini 2.5 Pro transcription is currently SOTA
and GPT-4.5 is the best model for doing write-ups.
"""

import argparse
import mimetypes
import os
import subprocess
import tempfile
from pathlib import Path
from typing import List, Optional, Tuple
import io

import dotenv
from google import genai
from google.genai import types
from lingua import Language, LanguageDetectorBuilder
from openai import OpenAI
from pydub import AudioSegment
from pydub.silence import detect_nonsilent
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

dotenv.load_dotenv(".env")

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

GEMINI_MODEL = "gemini-2.5-pro-preview-05-06"
OPENAI_MODEL = "gpt-4.5-preview"
PROJECT_ID = os.getenv("PROJECT_ID")


if OPENAI_API_KEY is None or OPENAI_API_KEY == "":
    raise ValueError("OPENAI_API_KEY is not set")

if GEMINI_API_KEY is None or GEMINI_API_KEY == "":
    # Use Vertex AI API
    gemini_client = genai.Client(
        vertexai=True,
        project=PROJECT_ID,
        location="global",
    )
else:
    # Use Gemini API
    gemini_client = genai.Client(
        api_key=os.environ.get("GEMINI_API_KEY"),
    )

openai_client = OpenAI(
    # This is the default and can be omitted
    api_key=OPENAI_API_KEY,
)


def is_video_file(file_path: str) -> bool:
    """Determine if a file is a video file based on extension or MIME type."""
    # Check by extension first
    ext = os.path.splitext(file_path)[1].lower()
    video_extensions = [".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v", ".flv", ".wmv"]
    if ext in video_extensions:
        return True

    # Check by MIME type
    mime_type, _ = mimetypes.guess_type(file_path)
    return mime_type is not None and mime_type.startswith("video/")


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((subprocess.CalledProcessError,)),
    before_sleep=lambda retry_state: print(
        f"\nRetrying audio conversion (attempt {retry_state.attempt_number})..."
    ),
)
def convert_to_mp3(input_path: str, output_path: str = None) -> str:
    """Convert any audio/video file to MP3 format."""
    if output_path is None:
        temp_fd, output_path = tempfile.mkstemp(suffix=".mp3")
        os.close(temp_fd)

    try:
        cmd = [
            "ffmpeg",
            "-i",
            input_path,
            "-vn",  # No video
            "-acodec",
            "mp3",
            "-ab",
            "192k",
            "-ar",
            "44100",
            "-y",
            output_path,
        ]

        subprocess.run(cmd, capture_output=True, text=True, check=True)
        return output_path

    except subprocess.CalledProcessError as e:
        print(f"Error converting to MP3: {e}")
        print(f"FFmpeg stderr: {e.stderr}")
        raise
    except FileNotFoundError:
        print("FFmpeg not found. Please install FFmpeg.")
        print(
            "Install with: brew install ffmpeg (macOS) or apt-get install ffmpeg (Ubuntu)"
        )
        raise


def extract_audio_from_video(video_path: str, output_path: str = None) -> str:
    """Extract audio from video file using FFmpeg."""
    if output_path is None:
        # Create a temporary file for the extracted audio
        temp_fd, output_path = tempfile.mkstemp(suffix=".mp3")
        os.close(temp_fd)  # Close the file descriptor, we just need the path

    try:
        # Use FFmpeg to extract audio
        cmd = [
            "ffmpeg",
            "-i",
            video_path,
            "-vn",  # No video
            "-acodec",
            "mp3",  # Audio codec
            "-ab",
            "192k",  # Audio bitrate
            "-ar",
            "44100",  # Audio sample rate
            "-y",  # Overwrite output file if it exists
            output_path,
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"Audio extracted successfully to: {output_path}")
        return output_path

    except subprocess.CalledProcessError as e:
        print(f"Error extracting audio: {e}")
        print(f"FFmpeg stderr: {e.stderr}")
        raise
    except FileNotFoundError:
        print(
            "FFmpeg not found. Please install FFmpeg to extract audio from video files."
        )
        print(
            "Install with: brew install ffmpeg (macOS) or apt-get install ffmpeg (Ubuntu)"
        )
        raise


def chunk_audio_with_silence_detection(
    audio_path: str,
    chunk_duration_ms: int = 30 * 60 * 1000,
    min_silence_len: int = 1000,
    silence_thresh: int = -40,
    use_silence_detection: bool = False,
) -> List[AudioSegment]:
    """Split audio into chunks based on duration and optionally silence detection.

    Args:
        audio_path: Path to the audio file
        chunk_duration_ms: Target chunk duration in milliseconds (default 30 minutes)
        min_silence_len: Minimum length of silence to be considered (in ms)
        silence_thresh: Silence threshold in dBFS
        use_silence_detection: Whether to use silence detection for better chunk boundaries

    Returns:
        List of AudioSegment chunks
    """
    audio = AudioSegment.from_file(audio_path)
    chunks = []

    # If audio is shorter than chunk duration, return as single chunk
    if len(audio) <= chunk_duration_ms:
        return [audio]

    start = 0
    while start < len(audio):
        # Define the ideal end point
        ideal_end = start + chunk_duration_ms

        # If this would be the last chunk, take everything remaining
        if ideal_end >= len(audio):
            chunks.append(audio[start:])
            break

        # Determine the best split point
        best_split = ideal_end

        if use_silence_detection:
            # Look for silence in a window around the ideal end point (±2 minutes)
            window_start = max(start, ideal_end - 2 * 60 * 1000)
            window_end = min(len(audio), ideal_end + 2 * 60 * 1000)

            # Detect non-silent parts in the window
            window_audio = audio[window_start:window_end]
            nonsilent_ranges = detect_nonsilent(
                window_audio,
                min_silence_len=min_silence_len,
                silence_thresh=silence_thresh,
            )

            # Find the best split point (longest silence closest to ideal_end)
            if nonsilent_ranges:
                # Find gaps between nonsilent ranges
                for i in range(len(nonsilent_ranges) - 1):
                    gap_start = window_start + nonsilent_ranges[i][1]
                    gap_end = window_start + nonsilent_ranges[i + 1][0]
                    gap_middle = (gap_start + gap_end) // 2

                    # If this gap is closer to ideal_end, use it
                    if abs(gap_middle - ideal_end) < abs(best_split - ideal_end):
                        best_split = gap_middle

        # Create the chunk
        chunks.append(audio[start:best_split])
        start = best_split

    return chunks


def combine_audio_segments(segments: List[AudioSegment]) -> bytes:
    """Combine multiple audio segments into a single MP3 bytes object."""
    if not segments:
        return b""

    combined = segments[0]
    for segment in segments[1:]:
        combined = combined + segment

    # Export to bytes
    buffer = io.BytesIO()
    combined.export(buffer, format="mp3")
    return buffer.getvalue()


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=60),
    retry=retry_if_exception_type((Exception,)),
    before_sleep=lambda retry_state: print(
        f"\nRetrying transcript generation (attempt {retry_state.attempt_number})..."
    ),
)
def generate_first_transcript(
    bytes_data: bytes,
    mime_type: str,
    has_speaker_samples: bool = False,
    custom_prompt: str = None,
):
    if has_speaker_samples:
        prompt_text = (
            "This audio file begins with voice samples for speaker identification. "
            "Each person introduces themselves by saying their name and a test phrase. "
            "Use these voice samples to identify and label speakers throughout the main recording. "
            "\n\n"
            "Instructions:\n"
            "1. Listen to the initial voice samples where people introduce themselves\n"
            "2. Match voices in the main recording to these samples\n"
            "3. Label speakers by their actual names (not 'Speaker 1', 'Speaker 2')\n"
            "4. If you cannot match a voice to a sample, use 'Unknown Speaker'\n"
            "5. Do NOT include the voice sample section in the transcript\n"
            "6. Start the transcript from where the actual meeting/conversation begins\n"
            "\n\n"
            "Output the transcript with proper paragraphs and speaker names clearly indicated. "
            "Do not include filler sounds like 'um' or 'uh'. "
            "Output just the transcript, and no other commentary."
        )
    else:
        prompt_text = (
            "Transcribe this meeting recording. "
            "Output it as proper paragraphs with speaker changes clearly indicated when possible. "
            "Do not include filler sounds like 'um' or 'uh'. "
            "If you can identify different speakers, please indicate them (e.g., Speaker 1, Speaker 2, etc.). "
            "Output just the transcript, and no other commentary."
        )

    # Prepend custom prompt if provided
    if custom_prompt:
        prompt_text = custom_prompt + "\n\n" + prompt_text

    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_bytes(data=bytes_data, mime_type=mime_type),
                types.Part.from_text(text=prompt_text),
            ],
        ),
    ]
    generate_content_config = types.GenerateContentConfig(
        response_mime_type="text/plain",
    )
    ret = ""
    for chunk in gemini_client.models.generate_content_stream(
        model=GEMINI_MODEL,
        contents=contents,
        config=generate_content_config,
    ):
        print(chunk.text, end="")
        ret += chunk.text
    return ret


def detect_language_with_lingua(text: str):
    # Create a language detector with common languages
    languages = [
        Language.ENGLISH,
        Language.SPANISH,
        Language.FRENCH,
        Language.GERMAN,
        Language.ITALIAN,
        Language.PORTUGUESE,
        Language.RUSSIAN,
        Language.ARABIC,
        Language.CHINESE,
        Language.JAPANESE,
        Language.KOREAN,
        Language.TURKISH,
    ]

    detector = LanguageDetectorBuilder.from_languages(*languages).build()

    # Detect the language
    detected_language = detector.detect_language_of(text)

    # If no language was detected, return None
    if detected_language is None:
        return "Unknown"

    return detected_language.name


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=60),
    retry=retry_if_exception_type((Exception,)),
    before_sleep=lambda retry_state: print(
        f"\nRetrying translation (attempt {retry_state.attempt_number})..."
    ),
)
def translate_transcript_into_english(transcript: str):
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=transcript),
                types.Part.from_text(
                    text="Translate this meeting transcript into English. "
                    "Maintain the speaker indicators and paragraph structure. "
                    "Output just the transcript, and no other commentary."
                ),
            ],
        ),
    ]
    generate_content_config = types.GenerateContentConfig(
        response_mime_type="text/plain",
    )
    ret = ""
    for chunk in gemini_client.models.generate_content_stream(
        model=GEMINI_MODEL,
        contents=contents,
        config=generate_content_config,
    ):
        print(chunk.text, end="")
        ret += chunk.text
    return ret


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=60),
    retry=retry_if_exception_type((Exception,)),
    before_sleep=lambda retry_state: print(
        f"\nRetrying transcript cleaning (attempt {retry_state.attempt_number})..."
    ),
)
def clean_transcript(transcript: str):
    response = openai_client.responses.create(
        model=OPENAI_MODEL,
        input=transcript
        + (
            "\n\n---\n\n"
            "- Above is a meeting transcript.\n"
            "- Restructure it better while keeping "
            "- ALL THE INFORMATION included in there.\n"
            "Start with a tl;dr bullet point summary that is not overly long.\n"
            "- Then provide key discussion points and decisions made.\n"
            "- Include action items if any were mentioned.\n"
            "- The rest of the document can be any structure that makes sense for a meeting, "
            "as long as it's succinct, easy to read and understand.\n"
            "- Output markdown, and start with a top-level heading.\n"
            "- Output just the transcript, and no other commentary."
        ),
    )

    print(response.output_text)
    return response.output_text


def is_text_file(file_path: str) -> bool:
    """Determine if a file is a text file based on extension or MIME type."""
    # Check by extension first
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".txt":
        return True

    # Check by MIME type
    mime_type, _ = mimetypes.guess_type(file_path)
    return mime_type == "text/plain"


def process_speaker_samples(speaker_sample_paths: List[str]) -> Optional[AudioSegment]:
    """Process and combine speaker samples into a single audio segment."""
    if not speaker_sample_paths:
        return None

    combined_samples = None

    for sample_path in speaker_sample_paths:
        if not os.path.exists(sample_path):
            print(f"Warning: Speaker sample file not found: {sample_path}")
            continue

        # Convert to MP3 first
        temp_mp3 = None
        try:
            print(f"Processing speaker sample: {sample_path}")
            temp_mp3 = convert_to_mp3(sample_path)

            # Load the audio
            sample_audio = AudioSegment.from_mp3(temp_mp3)

            # Add 1 second of silence after each sample
            sample_with_silence = sample_audio + AudioSegment.silent(duration=1000)

            if combined_samples is None:
                combined_samples = sample_with_silence
            else:
                combined_samples = combined_samples + sample_with_silence

        finally:
            # Clean up temp file
            if temp_mp3 and os.path.exists(temp_mp3):
                os.unlink(temp_mp3)

    return combined_samples


def main(
    input_file: str,
    output_file: str | None = None,
    speaker_samples: List[str] = None,
    chunk_duration: int = 30,
    custom_prompt: str = None,
    use_silence_detection: bool = False,
):
    # If output_file is not provided, use the same name as the input file
    if output_file is None:
        # Get the directory of the input file
        directory = os.path.dirname(input_file)
        # Get the base filename without extension
        base_name = os.path.basename(input_file)
        base_without_ext = os.path.splitext(base_name)[0]
        # Create output file path in the same directory as source file
        output_file = os.path.join(
            directory, base_without_ext + "_meeting_transcript.md"
        )

    # Check if the input is a text file
    is_text = is_text_file(input_file)
    is_video = is_video_file(input_file)

    temp_audio_file = None
    temp_files = []  # Track all temp files for cleanup

    try:
        # Process speaker samples first
        speaker_audio = None
        if speaker_samples:
            print("\nProcessing speaker samples...")
            speaker_audio = process_speaker_samples(speaker_samples)
            if speaker_audio:
                print(f"Combined {len(speaker_samples)} speaker samples")

        if is_text:
            # For text files, read the content directly
            print(f"Detected a text file: {input_file}")
            with open(input_file, "r") as f:
                first_transcript = f.read()
            print("Reading text content...")
        elif is_video:
            # For video files, extract audio first
            print(f"Detected a video file: {input_file}")
            print("Extracting audio from video...")
            temp_audio_file = extract_audio_from_video(input_file)

            # Now process the extracted audio
            with open(temp_audio_file, "rb") as f:
                audio_bytes = f.read()

            print("Generating transcript from extracted audio...")

            # Convert to MP3 for consistency
            temp_mp3 = convert_to_mp3(temp_audio_file)
            temp_files.append(temp_mp3)

            # Chunk the audio
            print(f"\nChunking audio into {chunk_duration}-minute segments...")
            audio_chunks = chunk_audio_with_silence_detection(
                temp_mp3,
                chunk_duration_ms=chunk_duration * 60 * 1000,
                use_silence_detection=use_silence_detection,
            )
            print(f"Created {len(audio_chunks)} chunks")

            # Process each chunk
            all_transcripts = []
            for i, chunk in enumerate(audio_chunks):
                print(f"\nProcessing chunk {i + 1}/{len(audio_chunks)}...")

                # Combine speaker samples with chunk if available
                if speaker_audio:
                    combined_audio = (
                        speaker_audio + AudioSegment.silent(duration=2000) + chunk
                    )
                else:
                    combined_audio = chunk

                # Convert to bytes
                chunk_bytes = combine_audio_segments([combined_audio])

                # Generate transcript for this chunk
                chunk_transcript = generate_first_transcript(
                    chunk_bytes,
                    "audio/mp3",
                    has_speaker_samples=bool(speaker_audio),
                    custom_prompt=custom_prompt,
                )
                all_transcripts.append(chunk_transcript)

            # Combine all transcripts
            first_transcript = "\n\n".join(all_transcripts)
        else:
            # For audio files, handle as before
            mime_type, _ = mimetypes.guess_type(input_file)
            if mime_type is None:
                # Default to audio/mpeg if detection fails
                mime_type = "audio/mpeg"

            print(f"Detected MIME type: {mime_type}")

            with open(input_file, "rb") as f:
                audio_bytes = f.read()

            # Convert to MP3 and chunk
            print("Converting to MP3...")
            temp_mp3 = convert_to_mp3(input_file)
            temp_files.append(temp_mp3)

            print(f"\nChunking audio into {chunk_duration}-minute segments...")
            audio_chunks = chunk_audio_with_silence_detection(
                temp_mp3,
                chunk_duration_ms=chunk_duration * 60 * 1000,
                use_silence_detection=use_silence_detection,
            )
            print(f"Created {len(audio_chunks)} chunks")

            # Process each chunk
            all_transcripts = []
            for i, chunk in enumerate(audio_chunks):
                print(f"\nProcessing chunk {i + 1}/{len(audio_chunks)}...")

                # Combine speaker samples with chunk if available
                if speaker_audio:
                    combined_audio = (
                        speaker_audio + AudioSegment.silent(duration=2000) + chunk
                    )
                else:
                    combined_audio = chunk

                # Convert to bytes
                chunk_bytes = combine_audio_segments([combined_audio])

                # Generate transcript for this chunk
                chunk_transcript = generate_first_transcript(
                    chunk_bytes,
                    "audio/mp3",
                    has_speaker_samples=bool(speaker_audio),
                    custom_prompt=custom_prompt,
                )
                all_transcripts.append(chunk_transcript)

            # Combine all transcripts
            first_transcript = "\n\n".join(all_transcripts)
    except FileNotFoundError:
        print(f"Error: File '{input_file}' not found")
        return
    except Exception as e:
        print(f"Error processing file: {e}")
        return
    finally:
        # Clean up temporary audio file if it was created
        if temp_audio_file and os.path.exists(temp_audio_file):
            os.unlink(temp_audio_file)
            print(f"Cleaned up temporary audio file: {temp_audio_file}")

        # Clean up all other temp files
        for temp_file in temp_files:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    print("\nDetecting language using lingua-py...")
    detected_language = detect_language_with_lingua(first_transcript)
    print(f"Detected language: {detected_language}")

    translated_transcript = None

    if detected_language != "ENGLISH":
        print("\nTranslating transcript into English...")
        translated_transcript = translate_transcript_into_english(first_transcript)
        print("\nFinal transcript:")
        print(translated_transcript)
        transcript_to_clean = translated_transcript
    else:
        print("\nContent is already in English. No translation needed.")
        transcript_to_clean = first_transcript

    print("\nCleaning transcript...")
    cleaned_transcript = clean_transcript(transcript_to_clean)
    print("\nFinal transcript:")
    print(cleaned_transcript)

    with open(output_file, "w") as f:
        f.write(cleaned_transcript)

        if translated_transcript is not None:
            f.write("\n\n---\n\n## Translated Transcript\n\n")
            f.write(
                "<details>\n<summary>Click to see the translated transcript</summary>\n"
            )
            f.write(translated_transcript)

            f.write("\n\n</details>\n\n")
            # Write the original transcript in the detected language
            f.write("\n\n---\n\n## Original transcript\n\n")
            f.write(
                f"<details>\n<summary>Click to see the original transcript in {detected_language.capitalize()}</summary>\n\n"
            )
            f.write(first_transcript)
            f.write("\n\n</details>\n\n")
        else:
            f.write("\n\n---\n\n## Original transcript\n\n")
            f.write(
                "<details>\n<summary>Click to see the original transcript</summary>\n\n"
            )
            f.write(first_transcript)
            f.write("\n\n</details>\n\n")

    print(f"\nTranscript saved to {output_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Process meeting recordings (audio or video) using AI"
    )
    parser.add_argument(
        "input_file",
        help="Path to the audio file (mp3, ogg, wav), video file (mp4, mov, avi, etc.), or text file (txt)",
    )
    parser.add_argument(
        "-o",
        "--output_file",
        help="Path to the output file (supports md, txt, etc.)",
        default=None,
    )
    parser.add_argument(
        "-s",
        "--speaker-samples",
        nargs="+",
        help="Path(s) to speaker sample audio files (will be converted to MP3)",
        default=None,
    )
    parser.add_argument(
        "-c",
        "--chunk-duration",
        type=int,
        default=30,
        help="Chunk duration in minutes (default: 30)",
    )
    parser.add_argument(
        "-p",
        "--prompt",
        type=str,
        help="Custom prompt to prepend to the transcription instructions",
        default=None,
    )
    parser.add_argument(
        "--use-silence-detection",
        action="store_true",
        help="Enable silence detection for better chunk boundaries (disabled by default)",
    )
    args = parser.parse_args()

    main(
        args.input_file,
        output_file=args.output_file,
        speaker_samples=args.speaker_samples,
        chunk_duration=args.chunk_duration,
        custom_prompt=args.prompt,
        use_silence_detection=args.use_silence_detection,
    )
