"""
Takes a voice message or text file and transcribes/processes it into a structured format.

Why translate with Gemini 2.5 Pro and do the write-up with GPT-4.5?

Because IMO Gemini 2.5 Pro transcription is currently SOTA
and GPT-4.5 is the best model for doing write-ups.
"""

import argparse
import mimetypes
import os
import subprocess
import tempfile

import dotenv
from google import genai
from google.genai import types
from lingua import Language, LanguageDetectorBuilder
from openai import OpenAI

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


def generate_first_transcript(bytes_data: bytes, mime_type: str):
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_bytes(data=bytes_data, mime_type=mime_type),
                types.Part.from_text(
                    text="Transcribe this voice message. "
                    "Output it as proper paragraphs. "
                    "Do not include filler sounds like 'um' or 'uh'. "
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


def translate_transcript_into_english(transcript: str):
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=transcript),
                types.Part.from_text(
                    text="Translate this transcript into English. "
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


def clean_transcript(transcript: str):
    response = openai_client.responses.create(
        model=OPENAI_MODEL,
        input=transcript
        + (
            "\n\n---\n\n"
            "- Above is a voice message transcription.\n"
            "- Restructure it better while keeping "
            "- ALL THE INFORMATION included in there.\n"
            "Start with a tl;dr bullet point summary that is not overly long.\n"
            "- The rest of the document can be any structure that makes sense, "
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


def main(input_file: str, output_file: str | None = None):
    # If output_file is not provided, use the same name as the input file
    if output_file is None:
        # Get the directory of the input file
        directory = os.path.dirname(input_file)
        # Get the base filename without extension
        base_name = os.path.basename(input_file)
        base_without_ext = os.path.splitext(base_name)[0]
        # Create output file path in the same directory as source file
        output_file = os.path.join(directory, base_without_ext + ".md")

    # Check if the input is a text file
    is_text = is_text_file(input_file)
    is_video = is_video_file(input_file)

    temp_audio_file = None

    try:
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
            first_transcript = generate_first_transcript(audio_bytes, "audio/mp3")
        else:
            # For audio files, handle as before
            mime_type, _ = mimetypes.guess_type(input_file)
            if mime_type is None:
                # Default to audio/mpeg if detection fails
                mime_type = "audio/mpeg"

            print(f"Detected MIME type: {mime_type}")

            with open(input_file, "rb") as f:
                audio_bytes = f.read()

            print("Generating transcript...")
            first_transcript = generate_first_transcript(audio_bytes, mime_type)
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
        description="Process voice messages or text files using AI"
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
    args = parser.parse_args()

    main(args.input_file, output_file=args.output_file)
