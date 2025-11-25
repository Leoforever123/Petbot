#!/usr/bin/env python3
"""
Audio Device Test Script
Tests if PulseAudio is working and can receive audio input
"""

import pyaudio
import numpy as np
import sys
import time

def list_audio_devices():
    """List all available audio devices"""
    print("=" * 60)
    print("Available Audio Devices:")
    print("=" * 60)
    
    p = pyaudio.PyAudio()
    info = p.get_host_api_info_by_index(0)
    num_devices = info.get('deviceCount')
    
    if num_devices == 0:
        print("❌ No audio devices found!")
        p.terminate()
        return None, p
    
    default_input_device = None
    
    for i in range(num_devices):
        device_info = p.get_device_info_by_host_api_device_index(0, i)
        device_name = device_info.get('name')
        max_input_channels = device_info.get('maxInputChannels')
        max_output_channels = device_info.get('maxOutputChannels')
        default_sample_rate = device_info.get('defaultSampleRate')
        
        device_type = []
        if max_input_channels > 0:
            device_type.append(f"Input (channels: {max_input_channels})")
            if default_input_device is None:
                default_input_device = i
        if max_output_channels > 0:
            device_type.append(f"Output (channels: {max_output_channels})")
        
        type_str = ", ".join(device_type) if device_type else "Unknown"
        
        print(f"\n[Device {i}]")
        print(f"  Name: {device_name}")
        print(f"  Type: {type_str}")
        print(f"  Sample Rate: {default_sample_rate} Hz")
    
    print("\n" + "=" * 60)
    
    if default_input_device is not None:
        print(f"✅ Default input device found: Device {default_input_device}")
    else:
        print("❌ No input devices found!")
    
    return default_input_device, p


def test_audio_recording(device_index=None, duration=3, sample_rate=16000, chunk_size=512):
    """Test audio recording from the specified device"""
    print("\n" + "=" * 60)
    print(f"Testing Audio Recording (Duration: {duration}s)")
    print("=" * 60)
    
    p = pyaudio.PyAudio()
    
    try:
        # Open audio stream
        print(f"\n📡 Opening audio stream...")
        print(f"   Sample Rate: {sample_rate} Hz")
        print(f"   Channels: 1 (Mono)")
        print(f"   Chunk Size: {chunk_size} samples")
        
        if device_index is not None:
            print(f"   Device Index: {device_index}")
        
        stream = p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=sample_rate,
            input=True,
            input_device_index=device_index,
            frames_per_buffer=chunk_size
        )
        
        print("✅ Audio stream opened successfully!")
        print(f"\n🎤 Recording for {duration} seconds... (Please make some noise!)")
        print("   " + "-" * 50)
        
        frames = []
        num_chunks = int(sample_rate / chunk_size * duration)
        max_amplitude = 0
        total_rms = 0
        
        for i in range(num_chunks):
            try:
                data = stream.read(chunk_size, exception_on_overflow=False)
                frames.append(data)
                
                # Calculate audio levels
                audio_data = np.frombuffer(data, dtype=np.int16)
                amplitude = np.abs(audio_data).max()
                rms = np.sqrt(np.mean(audio_data.astype(np.float32) ** 2))
                
                max_amplitude = max(max_amplitude, amplitude)
                total_rms += rms
                
                # Visual feedback
                level_bars = int(amplitude / 32768 * 40)
                bar = "█" * level_bars + "░" * (40 - level_bars)
                print(f"   [{bar}] RMS: {int(rms):5d}", end='\r')
                
            except Exception as e:
                print(f"\n❌ Error reading audio data: {e}")
                break
        
        print("\n   " + "-" * 50)
        
        # Close stream
        stream.stop_stream()
        stream.close()
        
        # Analysis
        avg_rms = total_rms / num_chunks if num_chunks > 0 else 0
        
        print("\n📊 Recording Analysis:")
        print(f"   Total chunks recorded: {len(frames)}")
        print(f"   Max amplitude: {max_amplitude} / 32768 ({max_amplitude/32768*100:.1f}%)")
        print(f"   Average RMS: {avg_rms:.1f}")
        
        if max_amplitude < 100:
            print("\n⚠️  WARNING: Very low audio levels detected!")
            print("   - Check if your microphone is muted")
            print("   - Check microphone volume settings")
            print("   - Try making louder sounds")
        elif max_amplitude < 1000:
            print("\n⚠️  Low audio levels detected")
            print("   - Consider increasing microphone volume")
        else:
            print("\n✅ Audio levels look good!")
        
        if avg_rms < 10:
            print("\n⚠️  Mostly silence detected")
            print("   - Make sure you're making sounds during recording")
            print("   - Check if PulseAudio is configured correctly")
        else:
            print("✅ Sound is being captured!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Failed to record audio: {e}")
        print("\nPossible solutions:")
        print("  1. Make sure PulseAudio is running:")
        print("     $ pulseaudio --check")
        print("     $ pulseaudio --start")
        print("  2. Check PulseAudio configuration:")
        print("     $ pactl info")
        print("  3. List PulseAudio sources:")
        print("     $ pactl list sources short")
        print("  4. Set default source if needed:")
        print("     $ pactl set-default-source <source-name>")
        return False
    finally:
        p.terminate()


def test_audio_playback(device_index=None, duration=2, sample_rate=16000):
    """Test audio playback (output) to the specified device"""
    print("\n" + "=" * 60)
    print(f"Testing Audio Playback (Duration: {duration}s)")
    print("=" * 60)
    
    p = pyaudio.PyAudio()
    
    try:
        # Generate a test tone (440 Hz, A4 note)
        print("\n🔊 Generating test tone (440 Hz - A4 note)...")
        
        frequency = 440  # Hz
        t = np.linspace(0, duration, int(sample_rate * duration))
        
        # Generate sine wave
        audio_data = np.sin(2 * np.pi * frequency * t)
        
        # Apply fade in/out to avoid clicks
        fade_samples = int(sample_rate * 0.1)  # 100ms fade
        audio_data[:fade_samples] *= np.linspace(0, 1, fade_samples)
        audio_data[-fade_samples:] *= np.linspace(1, 0, fade_samples)
        
        # Convert to int16
        audio_data = (audio_data * 32767 * 0.5).astype(np.int16)
        
        print(f"\n📡 Opening audio output stream...")
        print(f"   Sample Rate: {sample_rate} Hz")
        print(f"   Channels: 1 (Mono)")
        print(f"   Format: 16-bit PCM")
        
        if device_index is not None:
            print(f"   Device Index: {device_index}")
        
        stream = p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=sample_rate,
            output=True,
            output_device_index=device_index,
            frames_per_buffer=1024
        )
        
        print("✅ Audio output stream opened successfully!")
        print(f"\n🔊 Playing test tone for {duration} seconds...")
        print("   (You should hear a constant beep)")
        
        # Play audio
        stream.write(audio_data.tobytes())
        
        # Close stream
        stream.stop_stream()
        stream.close()
        
        print("\n✅ Playback completed!")
        
        # Ask user if they heard it
        print("\n" + "=" * 60)
        heard = input("Did you hear the test tone? (y/n): ").strip().lower()
        
        if heard == 'y':
            print("✅ Audio output is working!")
            return True
        else:
            print("❌ Audio output may not be working properly")
            print("\nPossible issues:")
            print("  - Audio is muted in Windows")
            print("  - WSL audio forwarding not configured")
            print("  - Wrong output device selected")
            return False
        
    except Exception as e:
        print(f"\n❌ Failed to play audio: {e}")
        print("\nPossible solutions:")
        print("  1. Check if PulseAudio is running")
        print("  2. Check audio sinks:")
        print("     $ pactl list sinks short")
        print("  3. Set default sink if needed:")
        print("     $ pactl set-default-sink <sink-name>")
        print("  4. For WSL2, ensure audio forwarding is set up")
        return False
    finally:
        p.terminate()


def check_pulseaudio():
    """Check if PulseAudio is running"""
    print("\n" + "=" * 60)
    print("Checking PulseAudio Status")
    print("=" * 60)
    
    import subprocess
    
    try:
        # Check if PulseAudio is running
        result = subprocess.run(['pulseaudio', '--check'], 
                              capture_output=True, 
                              timeout=2)
        
        if result.returncode == 0:
            print("✅ PulseAudio is running")
        else:
            print("❌ PulseAudio is not running")
            print("\nTo start PulseAudio, run:")
            print("  $ pulseaudio --start")
            return False
        
        # Get PulseAudio info
        result = subprocess.run(['pactl', 'info'], 
                              capture_output=True, 
                              text=True, 
                              timeout=2)
        
        if result.returncode == 0:
            print("\n📋 PulseAudio Info:")
            for line in result.stdout.split('\n')[:10]:  # First 10 lines
                if line.strip():
                    print(f"   {line}")
        
        # List audio sources (input)
        result = subprocess.run(['pactl', 'list', 'sources', 'short'], 
                              capture_output=True, 
                              text=True, 
                              timeout=2)
        
        if result.returncode == 0 and result.stdout.strip():
            print("\n🎤 Available PulseAudio Sources (Input):")
            for line in result.stdout.strip().split('\n'):
                print(f"   {line}")
        else:
            print("\n⚠️  No PulseAudio sources found")
            print("   You may need to configure audio forwarding from Windows")
        
        # List audio sinks (output)
        result = subprocess.run(['pactl', 'list', 'sinks', 'short'], 
                              capture_output=True, 
                              text=True, 
                              timeout=2)
        
        if result.returncode == 0 and result.stdout.strip():
            print("\n🔊 Available PulseAudio Sinks (Output):")
            for line in result.stdout.strip().split('\n'):
                print(f"   {line}")
        else:
            print("\n⚠️  No PulseAudio sinks found")
            print("   You may need to configure audio forwarding from Windows")
        
        return True
        
    except FileNotFoundError:
        print("❌ PulseAudio commands not found!")
        print("   Make sure PulseAudio is installed:")
        print("   $ sudo apt install pulseaudio")
        return False
    except subprocess.TimeoutExpired:
        print("❌ PulseAudio commands timed out")
        return False
    except Exception as e:
        print(f"❌ Error checking PulseAudio: {e}")
        return False


def main():
    print("\n" + "=" * 60)
    print("🎵 AUDIO DEVICE TEST SCRIPT")
    print("=" * 60)
    
    # Check PulseAudio
    pulseaudio_ok = check_pulseaudio()
    
    # List audio devices
    default_device, p = list_audio_devices()
    
    if default_device is None:
        print("\n❌ Cannot proceed: No input devices available")
        print("\nTroubleshooting steps:")
        print("1. Make sure PulseAudio is running and configured correctly")
        print("2. For WSL2, ensure audio forwarding is set up:")
        print("   - Install PulseAudio on Windows (or use WSLg)")
        print("   - Configure PULSE_SERVER environment variable")
        print("3. Check if audio devices are available:")
        print("   $ pactl list sources short")
        if p:
            p.terminate()
        sys.exit(1)
    
    if p:
        p.terminate()
    
    # Test 1: Audio Playback (Output)
    print("\n" + "=" * 60)
    print("TEST 1: Audio Output (Playback)")
    print("=" * 60)
    input("Press ENTER to start playback test... ")
    
    playback_success = test_audio_playback(device_index=None)  # Use default output
    
    # Test 2: Audio Recording (Input)
    print("\n" + "=" * 60)
    print("TEST 2: Audio Input (Recording)")
    print("=" * 60)
    input("Press ENTER to start recording test... ")
    
    recording_success = test_audio_recording(device_index=default_device)
    
    # Final summary
    print("\n" + "=" * 60)
    print("📋 TEST SUMMARY")
    print("=" * 60)
    
    print(f"\n🔊 Audio Output (Playback): {'✅ PASS' if playback_success else '❌ FAIL'}")
    print(f"🎤 Audio Input (Recording): {'✅ PASS' if recording_success else '❌ FAIL'}")
    
    if playback_success and recording_success:
        print("\n✅ All audio tests passed!")
        print("\nYour audio setup appears to be working correctly.")
        print("If ASR/TTS still doesn't work, check:")
        print("  - ROS 2 environment variables")
        print("  - Python virtual environment compatibility")
        print("  - Node specific configurations")
    elif playback_success and not recording_success:
        print("\n⚠️  Output works but input doesn't")
        print("\nFix the microphone/input issues:")
        print("  - Check microphone permissions")
        print("  - Check PulseAudio source configuration")
    elif not playback_success and recording_success:
        print("\n⚠️  Input works but output doesn't")
        print("\nFix the speaker/output issues:")
        print("  - Check if audio is muted")
        print("  - Check PulseAudio sink configuration")
        print("  - For WSL2, ensure audio forwarding is set up")
    else:
        print("\n❌ Both audio tests failed")
        print("\nPlease fix the audio setup before running ASR/TTS nodes.")
    
    print("=" * 60)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
