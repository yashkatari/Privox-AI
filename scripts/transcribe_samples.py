import argparse
import sys
import os

# Ensure project root is on sys.path so top-level packages (like `stt`) import correctly
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from stt.streaming_whisper import load_whisper_model, transcribe_with_model

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model-size', default='medium')
    args = parser.parse_args()

    model = load_whisper_model(args.model_size)
    files = [
        os.path.join('stt-d', 'clean', 'QS1.mp3'),
        os.path.join('stt-d', 'clean', 'QS2.mp3'),
        os.path.join('stt-d', 'clean', 'QS3.mp3'),
    ]

    for f in files:
        print('---')
        print('File:', f)
        if not os.path.exists(f):
            print('Missing file')
            continue
        txt = transcribe_with_model(f, model)
        print('Transcript:', repr(txt))

if __name__ == '__main__':
    main()
