**Cloud-OpsBench** is the first large-scale, reproducible benchmark designed specifically for **Agentic Root Cause Analysis (RCA)** in cloud systems.

Traditional AIOps benchmarks suffer from a dichotomy: they are either static data dumps (lacking interactivity) or dynamic live environments (lacking determinism/reproducibility). Cloud-OpsBench resolves this by introducing the **State Snapshot Paradigm**. It freezes the complete context of a Kubernetes cluster at the moment of failure—including control plane objects, metrics, and logs—into an immutable persistence layer, providing a zero-latency, deterministic interface for tool interaction.

![Overview of Cloud-OpsBench](docs/images/overview.png)


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
| **Admission Control** | Quota or permission violations (e.g., NamespaceQuotaExceeded) | Hard | 58 |
| **Scheduling** | Pods pending due to constraints (e.g., NodeAffinityMismatch) | Medium | 164 |
| **Startup** | Image pull or mount errors (e.g., CrashLoopBackOff) | Easy | 62 |
| **Runtime** | App crashes or probe failures (e.g., OOMKilled) | Easy | 45 |
| **Service Routing** | Traffic routing failures (e.g., ServiceSelectorMismatch) | Medium | 54 |
| **Performance** | Latency/Throughput degradation (e.g., PodCPUOverload) | Hard | 21 |
| **Infrastructure** | Node/Control plane outages (e.g., KubeletUnavailable) | Hard | 48 |
| **Total** | **40 distinct fault types** | - | **452** |
