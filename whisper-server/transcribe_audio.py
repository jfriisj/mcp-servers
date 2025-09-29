#!/usr/bin/env python3
"""
Transcribe interview_audio.wav using Whisper MCP server
"""

import json
import subprocess
import sys
import base64
from pathlib import Path

def main():
    # Create base64 content
    audio_path = Path('audio/interview_audio.wav')
    if not audio_path.exists():
        print('❌ Audio file not found', file=sys.stderr)
        return False

    with open(audio_path, 'rb') as f:
        audio_data = f.read()

    test_audio_b64 = base64.b64encode(audio_data).decode('utf-8')
    print(f'📄 Created base64 audio (length: {len(test_audio_b64)} chars)')

    # Docker command
    docker_cmd = ['docker-compose', 'run', '--rm', '-T', 'whisper-server']

    try:
        print('🐳 Starting Docker container...')
        proc = subprocess.Popen(
            docker_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=Path('.')
        )

        if proc is None or proc.stdin is None or proc.stdout is None:
            print('❌ Failed to start Docker process')
            return False

        # Initialize
        print('🔧 Sending initialize request...')
        init_request = {
            'jsonrpc': '2.0',
            'id': 1,
            'method': 'initialize',
            'params': {
                'protocolVersion': '2024-11-05',
                'capabilities': {},
                'clientInfo': {'name': 'transcription-client', 'version': '1.0.0'},
            },
        }

        proc.stdin.write(json.dumps(init_request) + '\n')
        proc.stdin.flush()

        # Read initialize response
        init_line = proc.stdout.readline().strip()
        if not init_line:
            print('❌ No initialize response')
            return False
        init_response = json.loads(init_line)
        server_name = init_response.get('result', {}).get('serverInfo', {}).get('name', 'unknown')
        print(f'✅ Initialize response: {server_name}')

        # Send initialized notification
        initialized_notification = {
            'jsonrpc': '2.0',
            'method': 'notifications/initialized',
        }
        proc.stdin.write(json.dumps(initialized_notification) + '\n')
        proc.stdin.flush()

        # List tools
        print('📋 Requesting tools list...')
        tools_request = {'jsonrpc': '2.0', 'id': 2, 'method': 'tools/list'}
        proc.stdin.write(json.dumps(tools_request) + '\n')
        proc.stdin.flush()

        tools_response = json.loads(proc.stdout.readline().strip())
        tools = tools_response.get('result', {}).get('tools', [])
        print(f'✅ Found {len(tools)} tools')

        # Transcribe file content
        print('🎤 Transcribing audio...')
        transcribe_request = {
            'jsonrpc': '2.0',
            'id': 3,
            'method': 'tools/call',
            'params': {
                'name': 'whisper-transcribe-file-content',
                'arguments': {
                    'file_content': test_audio_b64,
                    'language': 'da',  # Danish
                    'response_format': 'verbose_json',
                },
            },
        }

        proc.stdin.write(json.dumps(transcribe_request) + '\n')
        proc.stdin.flush()

        # Read transcription response
        print('⏳ Waiting for transcription response...')
        import time
        start_time = time.time()
        transcribe_line = None

        while time.time() - start_time < 120:  # Wait up to 2 minutes
            if proc.poll() is not None:
                break
            try:
                line = proc.stdout.readline().strip()
                if line:
                    transcribe_line = line
                    break
            except (OSError, IOError):
                time.sleep(0.1)

        if not transcribe_line:
            print('❌ No transcription response received')
            return False

        transcribe_response = json.loads(transcribe_line)
        result = transcribe_response.get('result', {})
        content_list = result.get('content', [{}])
        content = content_list[0] if content_list else {}
        text = content.get('text', 'No text found')

        print(f'✅ Transcription result: {text}')

        # Close stdin
        proc.stdin.close()

        # Check for errors
        if proc.stderr:
            stderr_output = proc.stderr.read()
            if stderr_output:
                print(f'⚠️  Stderr: {stderr_output}')

        proc.wait()
        print('🎉 Transcription completed successfully!')
        return True

    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)