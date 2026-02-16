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

| Fault Category | Description | Difficulty | Cases |
| :--- | :--- | :--- | :--- |
| **Admission Control** | Requests rejected by API server due to quota or permission violations. | Hard | 58 |
| **Scheduling** | Pods stay Pending due to unsatisfied node constraints or affinity rules. | Medium | 164 |
| **Startup** | Container creation fails due to image pull or storage mount errors. | Easy | 62 |
| **Runtime** | Application crashes or fails health probes during execution. | Easy | 45 |
| **Service Routing** | Traffic routing failures between internal components. | Medium | 54 |
| **Performance** | Non-fatal degradation (latency/throughput) due to saturation. | Hard | 21 |
| **Infrastructure** | Outages in underlying cluster control plane or node components. | Hard | 48 |
| **Total** | **40 distinct fault types** | - | **452** |

## 🧰 Supported Diagnostic Tools

Cloud-OpsBench provides a suite of **10 specialized diagnostic tools** designed to mimic the capabilities of human SREs. These tools allow agents to inspect resources, check connectivity, analyze telemetry, and diagnose infrastructure issues within the deterministic environment.

| Category | Tool Name | Arguments | Description |
| :--- | :--- | :--- | :--- |
| **Resource Inspection** | `GetResources` | `resource_type`, `namespace`, `resource_name` | Lists resources in a namespace with status and extended attributes. |
| | `DescribeResource` | `resource_type`, `resource_name`, `namespace` | Retrieves runtime details of a specific resource, including state, conditions, and events. |
| | `GetAppYAML` | `service_name` | Fetches the deployment configuration YAML for a given service. |
| **Service Interaction** | `GetServiceDependencies` | `service_name` | Returns the service dependency graph in a tree structure. |
| | `CheckServiceConnectivity` | `namespace`, `service_name`, `port` | Tests service reachability via TCP handshake; returns connection success or failure. |
| **Telemetry Analysis** | `GetAlerts` | *(None)* | Retrieves cluster metric anomalies from the threshold-based detector, returning abnormal metrics and deviation magnitude. |
| | `GetRecentLogs` | `service_name`, `namespace` | Fetches recent logs (default: 50 lines) of a service for general error detection. |
| | `GetErrorLogs` | `service_name`, `namespace` | Returns a summary of abnormal logs by matching keywords (e.g., `ERROR`, `FAIL`). |
| **Infra Diagnostics** | `GetClusterConfiguration` | *(None)* | Retrieves cluster-wide node details, including resources, labels, taints, and status. |
| | `CheckNodeServiceStatus` | `node_name`, `component_name` | Probes liveness of control plane components on a node; returns process status, runtime state, and log snippets. |
## 🚀 Getting Started

### Prerequisites

* Python 3.10+
* Pip

### Installation

1.  Clone the repository:
    ```bash
    git clone https://github.com/wiluen/Cloud-OpsBench.git
    cd Cloud-OpsBench
    ```

2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3.  Setup Langfuse (Observability):
    We use [Langfuse](https://github.com/langfuse/langfuse) to trace and visualize the agent's ReAct reasoning process. and this project is built upon the [CrewAI](https://github.com/crewAIInc/crewAI) framework. Run the following commands to deploy it locally:

    ```bash
    # Get a copy of the latest Langfuse repository
    git clone https://github.com/langfuse/langfuse.git
    cd langfuse

    # Run the langfuse docker compose
    docker compose up
    ```
    
### ⚙️ Configuration & Usage

The project uses `config.yaml` for unified configuration management. Before running a diagnosis task, please modify the parameters below as needed.

#### 1. Modify Configuration (`config.yaml`)

Configure your LLM credentials, observability settings (Langfuse), and specific diagnosis task parameters:

```yaml
# config.yaml

# 1. LLM Model Settings
llm:
  model: "gpt-4o"            # Model identifier
  api_base: "https://api..." # API Endpoint
  api_key: "sk-..."          # API Key
  temperature: 0
  max_tokens: 4096

# 2. Langfuse Observability Settings
langfuse:
  public_key: "pk-..."
  secret_key: "sk-..."
  base_url: "http://localhost:3000"

# 3. Diagnosis Task Settings
diagnosis:
  # Fault Category: ["service", "admission", "startup", "runtime", "performance", "scheduling", "infrastructure"]
  fault_category: "startup" 
  
  # Prompt Strategy: ["base", "icl" (In-Context Learning), "cot" (Chain of Thought), "rag"]
  prompt_strategy: "base"
  
  # Workspace Path (IMPORTANT: Update this to your local absolute path)
  workspace_path: "/root/k8srca/Cloud-OpsBench"
  
  max_iterations: 15
```
#### 2. Run the Diagnosis Agent
Once configured, execute the main script to start the diagnosis process:

```bash
python main.py
```
#### 3. Evaluate Diagnosis Results
Execute the evaluation script to get the outcome and process-based metrics:

```bash
python evaluation.py
```

## 🏆 Leaderboard

Evaluation results on the Cloud-OpsBench test set. Metrics include Outcome Effectiveness (A@k, TCR) and Process Quality (Trajectory Alignment, Tool Usage, etc.).

| Model | A@1↑ | A@3↑ | TCR↑ | Exact↑ | InO.↑ | AnyO.↑ | Rel.↑ | Cov.↑ | Steps↓ | IAC↓ | MTTI↓ | RAR↓ | ZTDR↓ |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Qwen3-235B** | 0.50 | 0.53 | 0.96 | 0.13 | 0.38 | 0.41 | 0.55 | 0.67 | 5.34 | 0.22 | 143.55 | 0.06 | 0.17 |
| **DeepSeek-V3.2** | **0.73** | **0.79** | **0.99** | 0.00 | **0.53** | **0.63** | 0.43 | **0.88** | 10.00 | 0.25 | 975.41 | 0.11 | 0.00 |
| **GPT-5** | 0.67 | 0.75 | **0.99** | **0.16** | 0.38 | 0.48 | **0.65** | 0.77 | 5.57 | **0.04** | 172.57 | 0.05 | 0.04 |
| **GPT-4o** | 0.49 | 0.55 | **0.99** | 0.14 | 0.45 | 0.46 | 0.63 | 0.78 | 5.67 | 0.27 | **23.27** | **0.02** | 0.02 |
| **Claude-4-Sonnet**| 0.50 | 0.54 | 0.98 | 0.05 | 0.24 | 0.25 | 0.46 | 0.52 | **4.25** | 0.12 | 39.19 | 0.05 | 0.32 |
| **Qwen3-14B** | 0.34 | 0.43 | 0.82 | 0.04 | 0.31 | 0.42 | 0.63 | 0.71 | 5.82 | 0.40 | 108.51 | 0.10 | 0.00 |
| **Qwen3-8B** | 0.21 | 0.23 | 0.92 | 0.01 | 0.15 | 0.20 | 0.36 | 0.47 | 5.46 | 0.40 | 86.53 | 0.16 | 0.27 |

**Metrics Key:**
* **Outcome**: `A@k` (Top-k Accuracy), `TCR` (Task Completion Rate).
* **Process (Alignment)**: `Exact` (Exact Match), `InO.` (In-Order Match), `AnyO.` (Any-Order Match).
* **Process (Tool Use)**: `Rel.` (Relevance), `Cov.` (Coverage), `Steps` (Avg. Steps), `IAC` (Invalid Action Count).
* **Efficiency**: `MTTI` (Mean Time to Identify - simulated), `RAR` (Redundant Action Rate), `ZTDR` (Zero-Turn Diagnosis Rate).
