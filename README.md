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
    git clone [https://github.com/your-org/Cloud-OpsBench.git](https://github.com/your-org/Cloud-OpsBench.git)
    cd Cloud-OpsBench
    ```

2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
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
