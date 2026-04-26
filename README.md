# TinyMLOps for Real-Time Keyword Spotting (RT-KWS) 

An automated, end-to-end Machine Learning Operations (MLOps) pipeline designed to train, compress, and deploy a 1D-CNN for Real-Time Keyword Spotting on the highly resource-constrained **Raspberry Pi Pico W**.

##  Overview

Deploying complex neural networks to edge microcontrollers introduces severe bottlenecks in memory constraints, cross-compilation, and data versioning. This repository contains the architecture for a fully automated **TinyMLOps** pipeline. It bridges Data Engineering, Machine Learning, and DevOps, abstracting heavy computational workloads to the cloud while generating memory-safe, bare-metal C++ binaries for edge execution.

##  Key Features

* **Automated Data Versioning:** Utilizes **DVC (Data Version Control)** backed by **AWS S3** to cryptographically version thousands of acoustic `.wav` files without bloating the Git repository.
* **Cloud API Orchestration:** Leverages **GitHub Actions** to automate CI/CD, triggering the **Edge Impulse REST API** for Mel-Frequency Cepstral Coefficient (MFCC) extraction and model training.
* **Hardware-Aware Compression:** Implements **Int8 Post-Training Quantization (PTQ)** and **Ahead-of-Time (AOT) Compilation** via the EON™ Compiler, eliminating TensorFlow Lite interpreter overhead.
* **Secure OTA Deployment:** Features a custom chunked Over-The-Air (OTA) flashing mechanism, allowing the Pico W to securely poll GitHub Releases and patch its firmware via Wi-Fi with interrupt-disabled flash writing.

##  Hardware & Software Stack

**Target Hardware:**
* **MCU:** Raspberry Pi Pico W (RP2040 Dual-core ARM Cortex-M0+)
* **Clock Speed:** 133 MHz
* **Memory Constraints:** 264 KB SRAM / 2 MB Flash

**Software Infrastructure:**
* **Data Curation:** Python (`librosa`, `pydub`)
* **Storage:** DVC, AWS S3
* **CI/CD Orchestration:** GitHub Actions, Docker
* **Machine Learning:** Edge Impulse Platform (1D-CNN)
* **Embedded Toolchain:** Raspberry Pi Pico SDK, CMake, C/C++

##  Performance Metrics

The implementation of Int8 Quantization and the EON compiler yielded massive reductions in memory overhead while maintaining strict accuracy thresholds on unseen acoustic data.

| Metric | Value | Hardware Constraint Context |
| :--- | :--- | :--- |
| **Testing Accuracy** | `96.46%` | Passed strict SIL Quality Gates (Target classes: Yes, No, Noise). |
| **Neural Network Latency** | `9 ms` | 91% reduction vs. unoptimized Float32 models. |
| **Total Pipeline Latency** | `163 ms` | Includes 154ms DSP (MFCC extraction) + NN inferencing. |
| **Peak RAM Usage** | `15.4 KB` | Consumes < 6% of total Pico W SRAM. |
| **Flash Usage (ROM)** | `84 KB` | Highly compressed, leaving ample space for Wi-Fi stacks and A/B OTA partitions. |

##  Pipeline Architecture

1. **Developer Push:** Raw acoustic data is curated locally (16kHz, 1-second chunks), hashed by DVC, pushed to S3, and `.dvc` pointer files are committed to Git.
2. **CI Trigger:** GitHub Actions spins up an Ubuntu Docker container, authenticates with AWS, and pulls the raw acoustic binaries.
3. **API Cloud Factory:** The dataset is pushed to Edge Impulse. The pipeline triggers DSP extraction and trains a 1D-CNN (Conv1D -> Dropout -> Dense -> Softmax).
4. **Compilation Gate:** The model is evaluated. If it passes the "Iron Triangle" (Accuracy, Peak RAM, Flash limits), it is compiled into raw C++ via the EON compiler.
5. **CMake Integration:** The GitHub runner cross-compiles the C++ logic using the Pico SDK.
6. **CD Release:** The runner tags the release and publishes the compiled `.bin` firmware artifact.
7. **OTA Update:** Remote Pico W devices poll the `/releases/latest` endpoint and sequentially write the chunked binary to permanent Flash memory.

##  Getting Started

### Prerequisites
* AWS CLI configured with S3 access.
* DVC installed locally.
* Edge Impulse Studio API Keys.
* Raspberry Pi Pico C/C++ SDK.

### Initial Setup
1. Clone the repository:
   ```bash
   git clone [https://github.com/rishikesh-pandey/kws-pi-mlops.git](https://github.com/rishikesh-pandey/kws-pi-mlops.git)
   cd kws-pi-mlops
