# Voice Rover
An TinyML Micro based on rp2040 to command a SMARS Rover

# Description
This project aims to define all the steps required to train and ejecute a model that process 3 seconds audio using [MFCCs](https://en.wikipedia.org/wiki/Mel-frequency_cepstrum) representation

# Other sources
[End-to-end tinyML audio classification with the Raspberry Pi RP2040](https://blog.tensorflow.org/2021/09/TinyML-Audio-for-everyone.html)
A demostration on how cortex M devices can be used for on-device ML to detect audio events from its environment
You can see [here the jupyter notebook](https://colab.research.google.com/github/ArmDeveloperEcosystem/ml-audio-classifier-example-for-pico/blob/main/ml_audio_classifier_example_for_pico.ipynb) and [the rp2040 repo](https://github.com/ArmDeveloperEcosystem/ml-audio-classifier-example-for-pico)

# Pipeline
- Audio pipeline: capture 8bits 8ksps audio
    - Normalize to signed (+-1)
- Convert to spectogram [FFT](https://en.wikipedia.org/wiki/Fast_Fourier_transform)
    - Slice in small frames (20-30 ms) -> 25ms
    - Apply FFT to each frame
- Apply Mel-Frequency Ceptstral Coefficients
    - Build the time frame vs MFFC coefficient (e.g: 80 time x 32 MFCCs)
- Neural Network (input 30x32 MFCC)
    - [Conv2D](https://en.wikipedia.org/wiki/Convolutional_neural_network)
    - [ReLu](https://en.wikipedia.org/wiki/Rectified_linear_unit)
    - [Max Pool](https://en.wikipedia.org/wiki/Pooling_layer)
    - Conv2D
    - ReLu
    - [Dense](https://www.baeldung.com/cs/neural-networks-dense-sparse) (32 units)
    - Dense (4 output classes)

## Layers explanation
### Audio to MFCC
This proces audio chunks, normalize it, does FFT per each chunk and applies filtering focused in what humans hears
This [video](https://www.youtube.com/watch?v=SJo7vPgRlBQ) explains it thoughtfully
We end up with a 2D "image" of 80x32 (example)

### Conv2D layer #1
```
Conv2D(filters=8, kernel_size=(3,3), activation='relu')
```
Scans the MFCC image with small sliding windows (kernels)
Learns local patterns in time-frequency space (e.g., rising tone, plosive consonants, vowel shapes)

### ReLU Activation
```
ReLU(x) = max(0, x)
```
Introduces non-linearity (critical for learning complex patterns)
Fast to compute on microcontrollers
Works well with quantization (int8)

### MaxPool2D
```
MaxPool2D(pool_size=(2,2))
```
Reduces spatial resolution by taking the max value in each 2×2 region
Shrinks the feature map size (halves width/height)

### Conv2D layer #2
```
Conv2D(filters=16, kernel_size=(3,3), activation='relu')
```
Learns more complex patterns — combinations of features from the first conv layer
Detects higher-level audio signatures (word-level shapes)

### Flatten
```
Dense(4, activation='softmax')
```
Converts the 2D feature maps into a 1D vector.

# Tools
Install [Jupyter Notebook](https://jupyter.org/install)
```
pip install jupyterlab
jupyter lab

pip install notebook
jupyter notebook

pip install voila
voila
```

# Environment
```
python -m venv tflenv && source tflenv/bin/activate
pip install --upgrade pip
pip install tensorflow numpy soundfile librosa
```