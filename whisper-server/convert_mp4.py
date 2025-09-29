import sys
import os

sys.path.insert(0, "/app/src")

# Import audio processing libraries
try:
    import librosa
    import soundfile as sf

    print("Audio libraries available")
except ImportError as e:
    print(f"Missing libraries: {e}")
    sys.exit(1)


def convert_mp4_to_wav(mp4_path, wav_path):
    """Convert MP4 audio to WAV format."""
    try:
        print(f"Loading audio from: {mp4_path}")
        # Load audio with librosa (handles various formats)
        audio, sr = librosa.load(mp4_path, sr=None)  # Keep original sample rate

        print(f"Audio loaded: {len(audio)} samples, {sr} Hz")

        # Save as WAV
        print(f"Saving to: {wav_path}")
        sf.write(wav_path, audio, sr)

        print("Conversion completed successfully!")
        return True

    except Exception as e:
        print(f"Conversion failed: {e}")
        return False


if __name__ == "__main__":
    mp4_file = "/app/audio/Interview med Sebastian.mp4"
    wav_file = "/app/audio/Interview med Sebastian.wav"

    if os.path.exists(mp4_file):
        print(f"Converting {mp4_file} to {wav_file}")
        success = convert_mp4_to_wav(mp4_file, wav_file)
        if success:
            print("Conversion completed!")
        else:
            print("Conversion failed!")
    else:
        print(f"Input file not found: {mp4_file}")
        print("Available files:")
        try:
            files = os.listdir("/app/audio")
            for f in files:
                print(f"  {f}")
        except Exception:
            print("  Could not list directory")
