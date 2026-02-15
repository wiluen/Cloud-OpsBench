**Cloud-OpsBench** is the first large-scale, reproducible benchmark designed specifically for **Agentic Root Cause Analysis (RCA)** in cloud systems.

Traditional AIOps benchmarks suffer from a dichotomy: they are either static data dumps (lacking interactivity) or dynamic live environments (lacking determinism/reproducibility). Cloud-OpsBench resolves this by introducing the **State Snapshot Paradigm**. It freezes the complete context of a Kubernetes cluster at the moment of failure—including control plane objects, metrics, and logs—into an immutable persistence layer, providing a zero-latency, deterministic interface for tool interaction.

![Overview of Cloud-OpsBench](https://github.com/wiluen/Cloud-OpsBench/blob/main/resource/overview.png)


## 🌟 Key Features

* **🕵️ True Agentic Evaluation**: Supports agents actively exploring the system using tools like `kubectl` (mimicking human SREs), rather than performing passive classification.
* **📸 State Snapshot Paradigm**:
    * **High-Fidelity**: Captures full Kubernetes manifests, Prometheus metrics, and container logs.
    * **100% Reproducible**: Decouples state storage from tool interaction, eliminating environmental noise like network jitter.
    * **Zero-Cost Replay**: Runs a full benchmark on a laptop without maintaining expensive, live Kubernetes clusters.
* **📊 Full-Stack Coverage**: Features **452** distinct fault cases across **40** root cause types, covering the entire K8s stack (Runtime, Scheduling, Infrastructure, etc.).
* **📏 Process-Centric Evaluation**: Evaluates not just the diagnosis outcome, but the quality of the investigation trajectory (alignment with expert reasoning).

## 📂 Dataset Statistics

Cloud-OpsBench is built upon the Google Online Boutique microservices architecture. The distribution of fault categories is as follows:

| Fault Category | Description | Difficulty | # Cases |
| :--- | :--- | :--- | :--- |
| **Admission Control** | Requests rejected by API server due to quota or permission violations. | Hard | 58 |
| **Scheduling** | Pods stay Pending due to unsatisfied node constraints or affinity rules | Medium | 164 |
| **Startup** | Container creation fails due to image pull or storage mount errors. | Easy | 62 |
| **Runtime** | Application crashes or fails health probes during execution. | Easy | 45 |
| **Service Routing** | Traffic routing failures between internal components. | Medium | 54 |
| **Performance** | Non-fatal degradation (latency/throughput) due to saturation | Hard | 21 |
| **Infrastructure** | Outages in underlying cluster control plane or node components. | Hard | 48 |
| **Total** | **40 distinct fault types** | - | **452** |

## 🚀 Getting Started

### Prerequisites

* Python 3.9+
* Pip
* (Optional) Docker if running the live environment generator

### Installation

1.  Clone the repository:
    ```bash
    git clone [https://github.com/your-org/Cloud-OpsBench.git](https://github.com/your-org/Cloud-OpsBench.git)
    cd Cloud-OpsBench
    ```

2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

### Data Preparation

The benchmark relies on "State Snapshots" which act as the deterministic environment. Download the dataset (approx. 2.5GB):

```bash
# Download and unzip the snapshot data
python scripts/download_data.py --target ./data --version v1.0
Running an Evaluation
You can evaluate an agent (e.g., OpenAI GPT-4o, DeepSeek-V3, or a custom LangChain agent) using the main benchmark script.

Basic Usage:

Bash

python run_benchmark.py \
    --model gpt-4o \
    --agent_type react \
    --output_dir results/ \
    --max_steps 15 \
    --cases all
