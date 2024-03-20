import librosa
import numpy as np
import matplotlib.pyplot as plt

def detect_pauses(audio_file, threshold=1, min_pause_duration=1):
    # Load audio file
    y, sr = librosa.load(audio_file, sr=None)
    
    # Compute short-time energy
    energy = librosa.feature.rms(y=y)
    # print(energy)
    
    # Apply thresholding
    pauses = np.where(energy < threshold)
    plt.figure(figsize=(10, 5))
    plt.imshow(pauses, cmap='viridis', aspect='auto', origin='lower')
    plt.colorbar(label='Energy')
    plt.xlabel('Time (frame index)')
    plt.ylabel('Energy')
    plt.title('Energy of the Audio Signal')
    plt.show()
    print(pauses)
    
    # Detect pause segments
    pause_segments = []
    start = None
    for i in range(len(pauses[1])):
        if start is None:
            start = pauses[1][i]
        elif pauses[1][i] > pauses[1][i-1] + 1:
            end = pauses[1][i-1]
            if end - start >= sr * min_pause_duration:
                pause_segments.append((start, end))
            start = pauses[1][i]
    
    return pause_segments

# Example usage
audio_file = "output_20240318_224706.wav"
pause_segments = detect_pauses(audio_file)
print("Pause segments:", pause_segments)
