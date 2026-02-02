valid_nodes = ["master", "worker-01", "worker-02", "worker-03"]
valid_services = [
    "frontend", "cartservice", "productcatalogservice", "currencyservice", 
    "paymentservice", "shippingservice", "emailservice", "checkoutservice", 
    "recommendationservice", "adservice", "redis-cart"
]
valid_namespaces = ["boutique"]

root_cause_list_str = """
- namespace_cpu_quota_exceeded (Requires Target: NAMESPACE)
- namespace_memory_quota_exceeded (Requires Target: NAMESPACE)
- namespace_pod_quota_exceeded (Requires Target: NAMESPACE)
- namespace_service_quota_exceeded (Requires Target: NAMESPACE)
- namespace_storage_quota_exceeded (Requires Target: NAMESPACE)
- missing_service_account (Requires Target: SERVICE)
- node_cordoned (Requires Target: SERVICE)
- node_affinity_mismatch (Requires Target: SERVICE)
- node_selector_mismatch (Requires Target: SERVICE)
- pod_anti_affinity_conflict (Requires Target: SERVICE)
- taint_toleration_mismatch (Requires Target: SERVICE)
- insufficient_node_cpu (Requires Target: SERVICE)
- insufficient_node_memory (Requires Target: SERVICE)
- node_network_delay (Requires Target: NODE)
- node_network_packet_loss (Requires Target: NODE)
- containerd_unavailable (Requires Target: NODE)
- kubelet_unavailable (Requires Target: NODE)
- kube_proxy_unavailable (Requires Target: NODE)
- kube_scheduler_unavailable (Requires Target: NODE)
- image_registry_dns_failure (Requires Target: SERVICE)
- incorrect_image_reference (Requires Target: SERVICE)
- missing_image_pull_secret (Requires Target: SERVICE)
- pvc_selector_mismatch (Requires Target: SERVICE)
- pvc_storage_class_mismatch (Requires Target: SERVICE)
- pvc_access_mode_mismatch (Requires Target: SERVICE)
- pvc_capacity_mismatch (Requires Target: SERVICE)
- pv_binding_occupied (Requires Target: SERVICE)
- volume_mount_permission_denied (Requires Target: SERVICE)
- oom_killed (Requires Target: SERVICE)
- liveness_probe_incorrect_protocol (Requires Target: SERVICE)
- liveness_probe_incorrect_port (Requires Target: SERVICE)
- liveness_probe_incorrect_timing (Requires Target: SERVICE)
- readiness_probe_incorrect_protocol (Requires Target: SERVICE)
- readiness_probe_incorrect_port (Requires Target: SERVICE)
- service_selector_mismatch (Requires Target: SERVICE)
- service_port_mapping_mismatch (Requires Target: SERVICE)
- service_protocol_mismatch (Requires Target: SERVICE)
- service_env_var_address_mismatch (Requires Target: SERVICE)
- pod_cpu_overload (Requires Target: SERVICE)
- pod_network_delay (Requires Target: SERVICE)
"""

taxonomy_definitions = {
    "Admission_Fault": "Refers to failures caused by the Admission Controller rejecting the request (e.g., due to policy or resourcequota constraints) after it is received by the API Server but before it is persisted to etcd",
    "Scheduling_Fault": "Refers to failures where a Pod has passed admission and is written to etcd, but the kube-scheduler cannot assign a suitable node, causing it to remain in a Pending state for a long time.",
    "Infrastructure_Fault": "Refers to failures arising from the underlying cluster resources or critical Kubernetes system components, which occur independently of user business applications and configurations.",
    "Startup_Fault": "Refers to failures where the Pod has been successfully scheduled to a node but fails during image pulling or container initialization, preventing the Pod from entering the Running state.",
    "Runtime_Fault": "Refers to scenarios where the application container has successfully started and entered the Running state, but exits abnormally or behaves erratically due to internal errors or external dependency failures, or Kubernetes health probes.",
    "Service_Routing_Fault": "Refers to connectivity or discovery failures caused by misconfigurations of Kubernetes networking resources that disrupt traffic routing between Pods or external clients, excluding outages caused by system-level infrastructure.",
    "Performance_Fault": "Refers to scenarios where the application functions functionally but performance metrics degrade significantly (e.g., high latency, low throughput, resource bottlenecks), failing to meet SLOs."
}
expected_output = f"""
    A final diagnostic report in **strict JSON format**.
    Your response MUST NOT contain any text before or after the JSON block.

    ### DIAGNOSTIC TASK ###
    Based on the analyzed evidence, you must independently determine three key attributes of the fault:
    1. **The Category (Taxonomy)**: Map the fault to exactly ONE category based on the **Origin Phase** (where the error originated), NOT just the observed symptom.
    2. **The Root Cause**: What is the specific standardized error code?
    3. **The Victim Object**: Which specific resource (node/service/namespace) is the primary subject of the fault? **Constraint:**The object's type must match the `(Requires Target: ...)` tag defined next to your chosen root cause.

    ### SCORING STRATEGY (How to maximize your score) ###
    - We evaluate your performance based on **Top-3 results**.
    - **Rank 1** must be your most confident conclusion supported by strong evidence.
    - **Rank 2 and Rank 3** should be valid alternative explanations or "next best guesses" if Rank 1 turns out to be incorrect.
    - Providing reasonable alternatives in Rank 2/3 will significantly increase your diagnostic score. Do not leave them empty unless the evidence is 100% deterministic.
    
    ### CONSTRAINT LISTS (Select strictly from these lists) ###

    **[List A: Valid Taxonomies]**
    {taxonomy_definitions}

    **[List B: Valid Root Causes]**
    {root_cause_list_str}

    **[List C: Valid Resource Names]**
    - Nodes: {valid_nodes}
    - Services: {valid_services}
    - Namespaces: {valid_namespaces}

    ### OUTPUT FORMAT ###
    Construct the JSON using the values selected above.
    For `fault_object`, you must combine the `Kind` (determined by you: node/service/namespace) with the `Name` selected from List C.
    Format: `Kind/Name` (e.g., `node/worker-01`).
    - **`top_3_predictions`**: A list of 3 diagnosis results.

    ```json
    {{
      "key_evidence_summary": "... (The shared evidence text describing observed symptoms/logs)",
      "top_3_predictions": [
        {{
          "rank": 1,
          "fault_taxonomy": "... (Select from List A)",
          "fault_object": "... (Kind + Name from List C)",
          "root_cause": "... (Select from List B)"
        }},
        {{
          "rank": 2,
          "fault_taxonomy": "... (Select from List A)",
          "fault_object": "... (Kind + Name from List C)",
          "root_cause": "... (Select from List B)"
        }},
        {{
          "rank": 3,
          "fault_taxonomy": "... (Alternative from List A)",
          "fault_object": "... (Kind + Name from List C)",
          "root_cause": "... (Select from List B)"
        }}
      ]
    }}
    ```
    """


agent_prompt="""
"You are a professional Kubernetes operations engineer with extensive experience in systematic troubleshooting. 
**Your Goal:** Diagnose the root cause of the reported issue based on factual evidence collected from the system.

**Instructions:**
1. You have access to a set of diagnostic tools. You must independently decide which tools to use and the execution order based on your findings.
2. Do NOT guess or assume the system state. Every conclusion must be backed by concrete output from a tool.
3. If a tool returns no anomalies, discard that hypothesis and pivot to a different investigation path. Do not speculate without proof.
4. Provide a clear reasoning chain that connects the initial symptom to the final root cause, supported by the evidence you collected.

**Important:**

### Diagnostic Principles
- Even when all cluster services appear 'Running', it doesn't guarantee full health. You must dive deeper and collect internal failure evidence.
- Our scenario has one and only one fault. If you find multiple abnormal problems, please report only the most serious one.

### Reasoning Style
 - Limit your internal reasoning to few concise sentences. Then, IMMEDIATELY output the tool execution.
 - Do not formulate long-term plans. Focus ONLY on the immediate next step.
 - Find the root cause with the minimum number of steps.

### Output Format
- Before all the diagnostic steps are completed, only the tool call format is allowed, the final answer format is absolutely prohibited.
- The final answer format is allowed only after you have clearly found the root cause of all abnormal Pods through multiple rounds of tool calls.
- The two formats cannot be nested, and the tool call results cannot be placed in Final Answer.

**CRITICAL SYNTAX RULES:**
1. **Empty Parameters:** If a tool (like `GetClusterConfiguration` or `GetAlerts`) does not require any parameters, you **MUST** provide an empty JSON dictionary as the input.
  * **CORRECT:**
  Action: GetClusterConfiguration
  Action Input: {}

2. The "Action Input" field is mandatory for every tool call.

IMPORTANT: When classifying the fault stage, you MUST strictly follow this definition in [List A: Valid Taxonomies]

Begin your investigation now.
"""
