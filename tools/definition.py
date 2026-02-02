import os
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Optional, Type, List
from .implement import KubernetesTools
from typing import Literal

BoutiqueServiceName=Literal['adservice','cartservice','checkoutservice','currencyservice','emailservice','frontend','paymentservice','productcatalogservice','recommendationservice','redis-cart','shippingservice']
ClusterScopeResource = {
    "nodes", "node",
    "persistentvolumes", "pv","persistentvolume",
    "storageclasses", "sc","storageclass"
}
NodeName=Literal['master','worker-01','worker-02','worker-03']
SystemServiceName=Literal['kube-schedule','kubelet', 'kube-proxy','containerd']

def create_k8s_tools(case_path: str):
    if not os.path.exists(case_path):
            raise FileNotFoundError(f"Snapshot file not found: {case_path}")
    k8s_tools_instance = KubernetesTools(
        case_path=case_path
    )

    class GetResourcesInput(BaseModel):
        """(Updated) Input parameters for the GetResources tool"""
        resource_type: str = Field(description="**REQUIRED**. The type of resource to list. (e.g., 'pods', 'services', 'deployments', 'nodes').")
        namespace: Optional[str] = Field(
            default=None,
            description=(
            "The Kubernetes namespace to query. "
            "**CRITICAL**: If the `resource_type` is a namespaced resource (e.g., 'pods', 'deployments', 'services'), "
            "you MUST provide the namespace (default is 'boutique'). "
            "However, if the `resource_type` is a cluster-scoped resource (e.g., 'nodes', 'persistentvolumes'), "
            "DO NOT include the `namespace` parameter in your tool call at all."
            )
        )
        name: Optional[str] = Field(default=None, description="Optional. The specific name of the resource to retrieve a single item (e.g., 'checkoutservice-xyz'). If omitted, returns a list of all resources.")
        show_labels: bool = Field(default=False, description="If True, adds `--show-labels`. **MUTUALLY EXCLUSIVE** with `output_wide` and `label_selector`. Do not set this if you use the others.")
        output_wide: bool = Field(default=False, description="If True, adds `-o wide` to show extra info like Node IP. **MUTUALLY EXCLUSIVE** with `show_labels` and `label_selector`.")
        label_selector: Optional[str] = Field(default=None, description="Filter by label (e.g., 'app=frontend'). **MUTUALLY EXCLUSIVE** with `show_labels` and `output_wide`. **SUPPORTED ONLY FOR**: pods, services, deployments, and persistentvolumeclaims (PVCs).")

    class GetResourcesTool(BaseTool):
        name: str = "GetResources"
        description: str = (
        "Simulates `kubectl get` to retrieve resource lists or details. "
        "Use this tool FIRST to verify the status of Pods or Nodes. "
        "IMPORTANT: The options `show_labels`, `output_wide`, and `label_selector` are mutually exclusive—you can only use ONE at a time."
        )
        args_schema: Type[BaseModel] = GetResourcesInput

        def _run(
            self,
            resource_type: str,
            namespace: Optional[str] = None,
            name: Optional[str] = None,
            show_labels: bool = False,
            output_wide: bool = False,
            label_selector: Optional[str] = None
        ) -> str:
            try:
                if resource_type in ClusterScopeResource:
                    default_namespace = "boutique"
                else:
                    default_namespace = namespace
                return k8s_tools_instance.GetResources(
                    resource_type=resource_type,                   
                    namespace=default_namespace,
                    name=name,
                    show_labels=show_labels,
                    output_wide=output_wide,
                    label_selector=label_selector
                )
            except ValueError as e:
                # Convert Python exceptions into strings the LLM can understand
                return f"Error: {e}"


    class DescribeResourceInput(BaseModel):
        """(Updated) Input parameters for the DescribeResource tool"""
        resource_type: str = Field(description="**REQUIRED**. The type of resource to describe (e.g., 'pod', 'node', 'service', 'pvc').")
        name: str = Field(description="**REQUIRED**. The EXACT name of the specific resource to inspect (e.g., 'checkoutservice-7d9b7c9-xyz'). You cannot describe 'all' resources; you must target a specific instance found via GetResources.")
        namespace: Optional[str] = Field(
            default=None,
            description=(
            "The Kubernetes namespace to query. "
            "**CRITICAL**: If the `resource_type` is a namespaced resource (e.g., 'pods', 'deployments', 'services'), "
            "you MUST provide the namespace (default is 'boutique'). "
            "However, if the `resource_type` is a cluster-scoped resource (e.g., 'nodes', 'persistentvolumes'), "
            "DO NOT include the `namespace` parameter in your tool call at all."
            )
        )
    class DescribeResourceTool(BaseTool):
        name: str = "DescribeResource"
        description: str = (
        "Simulates `kubectl describe`. Use this tool when you find a Pod in a non-Running state (e.g., Pending, CrashLoopBackOff) or a Node in NotReady state. " 
        "It provides critical 'Events' (at the bottom of the output) and 'Conditions' which are essential for identifying why a resource is failing."
        "DO NOT use this tool to describe 'namespaces',Namespace-level details such as ResourceQuota can be retrieved directly via the `GetResources` tool "
        )
        args_schema: Type[BaseModel] = DescribeResourceInput

        def _run(self, resource_type: str,
                 name: str,
                 namespace: Optional[str] = None) -> str:
            # (Updated) Call the Python instance
            try:
                if resource_type in ClusterScopeResource:
                    default_namespace = "boutique"
                else:
                    default_namespace = namespace
                return k8s_tools_instance.DescribeResource(
                    resource_type=resource_type,
                    name=name,
                    namespace=default_namespace
                )
            except ValueError as e:
                return f"Error: {e}"

    class GetAppYAMLInput(BaseModel):
        app_name: BoutiqueServiceName = Field(description=f"**REQUIRED**. The name of the microservice to inspect (e.g., 'frontend', 'redis-cart', 'adservice').")
        
    class GetAppYAMLTool(BaseTool):
        name: str = "GetAppYAML"
        description: str = (
        "Retrieves the raw YAML configuration file (Source of Truth) for a specific service. "
        "Use this tool to perform **Static Configuration Analysis**. "
        "It is essential for checking defined Resource Limits (CPU/Memory), Liveness/Readiness Probes, Environment Variables, and Image Tags. "
        )
        args_schema: Type[BaseModel] = GetAppYAMLInput

        def _run(self, app_name: str) -> str:
            # (Updated) Call the Python instance
            try:
                validated_input = GetAppYAMLInput(
                app_name=app_name
                )
                return k8s_tools_instance.GetAppYAML(app_name=validated_input.app_name)
            except (ValueError, FileNotFoundError) as e:
                return f"Error: {e}"


    class GetRecentLogsInput(BaseModel):
        """(Updated) Input parameters for the GetPodLogs tool"""
        namespace: str = Field(description="**REQUIRED**. The Kubernetes namespace")
        service_name: BoutiqueServiceName = Field(description="**REQUIRED**. The high-level **Microservice Name** (e.g., 'frontend', 'cartservice', 'redis-cart'). Do NOT provide the full specific Pod name (like 'frontend-7d9b7c9-xyz'). Just provide the service name, and the tool will automatically show the logs for you.")
        
    class GetRecentLogsTool(BaseTool):
        name: str = "GetRecentLogs"
        description: str = (
        "Retrieves the raw, complete standard output logs from the container. "
        "This tool is most effective when the Pod is **NOT in a normal Running state** (e.g., CrashLoopBackOff, ImagePullBackOff, or immediate startup failure), where you need to see the raw startup sequence to diagnose why it crashed. "
        "**CONTRAST**: "
        "- Use `GetErrorLogs` for running services with many logs. "
        "- Use `GetRecentLogs` (this tool) for startup failures or hard crashes where every single line matters."
    )
        args_schema: Type[BaseModel] = GetRecentLogsInput

        def _run(self, namespace: str, service_name: str) -> str:
            # (Updated) Call the Python instance
            try:
                validated_input = GetRecentLogsInput(
                namespace=namespace,
                service_name=service_name
                )
                return k8s_tools_instance.GetRecentLogs(
                    namespace=validated_input.namespace,
                    service_name=validated_input.service_name
                )
            except ValueError as e:
                return f"Error: {e}"

    class GetErrorLogsInput(BaseModel):
        namespace: str = Field(description="**REQUIRED**. The Kubernetes namespace.")
        service_name: BoutiqueServiceName = Field(description="**REQUIRED**. The high-level **Microservice Name** (e.g., 'frontend', 'cartservice', 'redis-cart').")

    class GetErrorLogsTool(BaseTool):
        name: str = "GetErrorLogs"
        description: str = (
            "Retrieves a **Statistical Summary** of application error logs, grouped by error templates/patterns (including count and frequency). "
            "**WHEN TO USE**: "
            "1. **Performance Faults**: When a service is **Running** and handling traffic, raw logs (`GetRecentLogs`) are often too noisy (thousands of lines). Use this tool to get a clean signal. "
            "2. **Pattern Recognition**: Use this to quickly identify the *type* of exception (e.g., 'Connection Refused', 'Timeout') dominating the errors. "
            "**CONTRAST**: "
            "- Use `GetErrorLogs` (this tool) for running services with many logs. "
            "- Use `GetRecentLogs` for startup failures or hard crashes where every single line matters."
        )
        args_schema: Type[BaseModel] = GetErrorLogsInput
        def _run(self, namespace: str, service_name: str) -> str:
        # (Updated) Call the Python instance
            try:
                validated_input = GetErrorLogsInput(
                namespace=namespace,
                service_name=service_name
                )
                return k8s_tools_instance.GetErrorLogs(
                    namespace=validated_input.namespace,
                    service_name=validated_input.service_name
                )
            except ValueError as e:
                return f"Error: {e}"
            
    class CheckServiceConnectivityInput(BaseModel):
        """(Updated) Input parameters for the CheckServiceConnectivity tool"""
        service_name: BoutiqueServiceName= Field(
        description="**REQUIRED**. The target Service DNS name. You must choose from the predefined list."
        )
        port: int = Field(description="**REQUIRED**. The target TCP port number to test (e.g., 6379, 8080). **TIP**: You should verify the correct port number using `GetResources` or `GetAppYAML` first; do not guess.")
        namespace: str = Field(description="**REQUIRED**. The Kubernetes namespace. ")

    class CheckServiceConnectivityTool(BaseTool):
        name: str = "CheckServiceConnectivity"
        description: str = (
        "Performs an **Active Network Reachability Test**. "
        "It spins up a temporary ephemeral pod inside the cluster and attempts a TCP handshake (`nc -zv`) to the target service. "
        "**Use Cases**: "
        "1. Distinguish between Application crashes (app is reachable but returns error) vs. Network failures (app is unreachable). "
        "2. Verify if Kubernetes Service discovery (DNS/IP routing) is working. "
        "3. Check if Network Policies are blocking traffic."
        )
        args_schema: Type[BaseModel] = CheckServiceConnectivityInput

        def _run(self, service_name: str, port: int, namespace: str) -> str:
            # (Updated) Call the Python instance
            try:
                validated_input = CheckServiceConnectivityInput(
                service_name=service_name,
                port=port,
                namespace=namespace
                )
                return k8s_tools_instance.CheckServiceConnectivity(
                    service_name=validated_input.service_name,
                    port=validated_input.port,
                    namespace=validated_input.namespace
                )
            except ValueError as e:
                return f"Error: {e}"

                

    class GetServiceDependenciesInput(BaseModel):
        """(Added) Input parameters for the GetServiceDependencies tool"""
        service_name: BoutiqueServiceName = Field(description=f"**REQUIRED**. The name of the service (We recommend using 'frontend' to obtain the global topology at one time).")
       
    class GetServiceDependenciesTool(BaseTool):
        name: str = "GetServiceDependencies"
        description: str = (
        "Retrieves the Topology (Upstream/Downstream relationships) of a service. "
        "**CRITICAL USE CASE**: Use this for **Performance Issues** (Latency/Slowness) or **Cascading Failures**. "
        "Use this tool to trace the 'Call Graph' downwards and find the **Most Downstream Service** in the chain, as that is usually the Root Cause of the bottleneck."
        )
        args_schema: Type[BaseModel] = GetServiceDependenciesInput

        def _run(self, service_name: str) -> str:
            try:
                validated_input = GetServiceDependenciesInput(
                service_name=service_name
                )
                return k8s_tools_instance.GetServiceDependencies(validated_input.service_name)
            except ValueError as e:
                return f"Error: {e}"

    class GetClusterConfigurationTool(BaseTool):
        name: str = "GetClusterConfiguration"
        description: str = (
        "Retrieves a **Holistic Health Summary** of all nodes in the cluster. "
        "It reveals critical scheduling constraints that `GetResources` hides, specifically: "
        "1. **Node Taints**: Why a pod is refused on a node. "
        "2. **Node Conditions**: MemoryPressure, DiskPressure, or PIDPressure. "
        "3. **Allocatable Resources**: Total CPU/Memory capacity available. "
        "4. **Node Labels**: Crucial for NodeAffinity/NodeSelector matching. "
        "Use this instead of running `DescribeResource` on every single node."
        )
        
        def _run(self) -> str:
            # _run method also has no arguments
            try:
                return k8s_tools_instance.GetClusterConfiguration()
            except Exception as e:
                return f"Error: {e}"
            
    class GetAlertsTool(BaseTool):
        name: str = "GetAlerts"
        description: str = (
        "Retrieves active alerts triggered by metric anomalies (e.g., High Latency, Error Rate Spikes, CPU Saturation). "
        "**WHEN TO USE**: Strictly for **Performance Faults** (e.g., user reports 'slow' or 'timeout') on services that are already **Running**. "
        "**INTERPRETATION LOGIC**: "
        "1. If returns **Alerts**: You have found a performance bottleneck "
        "2. If returns **Empty**: It implies the service is handling traffic normally (no metric anomaly). "
        "**WARNING**: DO NOT use this tool for **Startup/Scheduling Faults** (e.g., Pending, CrashLoopBackOff) or other early-stage lifecycle failures. "
        "Because if a Pod never started, it generates no traffic metrics, so this tool will return empty. This does NOT mean the service is healthy. "
        )
        
        def _run(self) -> str:
            # _run method also has no arguments
            try:
                return k8s_tools_instance.GetAlerts()
            except Exception as e:
                return f"Error: {e}"
                
    class CheckNodeServiceStatusInput(BaseModel):
        node_name: NodeName = Field(description="**REQUIRED**. The target Node Name (e.g., 'worker-01').")
        service_name: SystemServiceName = Field(description="**REQUIRED**. The system component name to inspect. Valid targets typically include: 'kubelet', 'kube-proxy', 'containerd', or 'kube-scheduler'. ")
   
    class CheckNodeServiceStatusTool(BaseTool):
        name: str = "CheckNodeServiceStatus"
        description: str = (
            "Checks the systemd/operating status of critical Kubernetes infrastructure components on a specific Node. "
            "Use this when you have verified that the Application Configuration (`GetAppYAML`) is correct, yet the Pod fails to start or behave as expected. "
            "If the App logic is fine, the issue likely lies in the underlying Infrastructure layer."
            )

        args_schema: Type[BaseModel] = CheckNodeServiceStatusInput

        def _run(self,node_name: str, service_name: str) -> str:
        # _run method also has no arguments
            try:
                validated_input = CheckNodeServiceStatusInput(
                node_name=node_name,
                service_name=service_name
                )
                return k8s_tools_instance.CheckNodeServiceStatus(validated_input.node_name,validated_input.service_name)
            except Exception as e:
                return f"Error: {e}"
            
    tools_list = [
    GetResourcesTool(),
    DescribeResourceTool(),
    GetAppYAMLTool(),
    GetRecentLogsTool(),
    CheckServiceConnectivityTool(),
    GetClusterConfigurationTool(),
    GetServiceDependenciesTool(),
    GetErrorLogsTool(),
    GetAlertsTool(),
    CheckNodeServiceStatusTool()
    ]
    return tools_list