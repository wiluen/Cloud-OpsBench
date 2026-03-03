from tools.implement import KubernetesTools
import json
import os
import datetime
import random
from typing import List, Dict, Any

# Keep the original service list and namespace configuration
BOUTIQUE=['adservice','cartservice','checkoutservice','currencyservice','emailservice','frontend','paymentservice','productcatalogservice','recommendationservice','redis-cart','shippingservice']
DEFAULT_NAMESPACE='boutique'

class DiagnosticTester:
    """Diagnostic tool used only for interaction testing (no logging or persistence)"""
    def __init__(self, snapshot_path: str, query: str):
        self.k8s_tools = KubernetesTools(snapshot_path)
        self.query = query
        self.snapshot_path = snapshot_path
        # Remove all trace/statistics related attributes
        self.tools = [
            {"name": "GetResources", "method": self.k8s_tools.GetResources, 
             "description": "Get Kubernetes resource information (e.g., pods, services)"},
            {"name": "DescribeResource", "method": self.k8s_tools.DescribeResource,
             "description": "Get detailed description of a specific resource (e.g., Pod events, status)"},
            {"name": "GetAppYAML", "method": self.k8s_tools.GetAppYAML,
             "description": "Get application's YAML configuration (e.g., deployment config, environment variables)"},
            {"name": "GetServiceDependencies", "method": self.k8s_tools.GetServiceDependencies,
             "description": "Get upstream/downstream service dependencies (who calls it / what it calls)"},
            {"name": "GetRecentLogs", "method": self.k8s_tools.GetRecentLogs,
             "description": "Get Pod logs (including previous crash logs)"},
            {"name": "CheckServiceConnectivity", "method": self.k8s_tools.CheckServiceConnectivity,
             "description": "Check service network connectivity (TCP-based)"},
            {"name": "GetClusterConfiguration", "method": self.k8s_tools.GetClusterConfiguration,
             "description": "Get cluster node configuration (resources, labels, taints, etc.)"},
            {"name": "GetAlerts", "method": self.k8s_tools.GetAlerts,
             "description": "Get business alerts (triggered by abnormal metrics)"},
            {"name": "GetErrorLogs", "method": self.k8s_tools.GetErrorLogs,
             "description": "Get error logs (mainly for performance issues with complex logs)"},
            {"name": "CheckNodeServiceStatus", "method": self.k8s_tools.CheckNodeServiceStatus,
             "description": "Get status of key Kubernetes components"}
        ]
    
    def print_welcome(self):
        """Simplified welcome info, only shows test-related content"""
        print("=" * 80)
        print(f"[TEST MODE] K8s incident diagnosis tool (no persistence)")
        print(f"Test fault query: {self.query}")
        print(f"Default namespace: {DEFAULT_NAMESPACE}")
        print("=" * 80)
        print("Follow the diagnostic workflow to select tools; when finished, choose Exit (no data is saved).")
        print("-" * 80)
    
    def print_tool_list(self):
        """Print available tools only; no history"""
        print("\nAvailable tools:")
        for i, tool in enumerate(self.tools, 1):
            print(f"{i}. {tool['name']} - {tool['description']}")
        print(f"{len(self.tools) + 1}. Exit test")
        print("-" * 80)
    
    def get_tool_arguments(self, tool_name: str) -> Dict[str, Any]:
        """Keep original argument input logic; only for interaction testing"""
        args = {}
        
        if tool_name == "GetResources":
            args["namespace"] = DEFAULT_NAMESPACE
            args["resource_type"] = input("Enter resource type (e.g., 'pods', 'services'): ").strip()
            args["name"] = input("Enter resource name (optional, press Enter to skip): ").strip() or None
            
            while True:
                print("Optional parameters (select one or press Enter to skip):")
                print("1. Show labels (--show-labels)")
                print("2. Wide output (-o wide)")
                print("3. Label selector (e.g., 'app=frontend')")
                choice = input("Choose (1-3, or press Enter to skip optional parameters): ").strip()
                
                if not choice:
                    args["show_labels"] = False
                    args["output_wide"] = False
                    args["label_selector"] = None
                    break
                elif choice == "1":
                    args["show_labels"] = True
                    args["output_wide"] = False
                    args["label_selector"] = None
                    break
                elif choice == "2":
                    args["show_labels"] = False
                    args["output_wide"] = True
                    args["label_selector"] = None
                    break
                elif choice == "3":
                    args["show_labels"] = False
                    args["output_wide"] = False
                    args["label_selector"] = input("Enter label selector: ").strip() or None
                    break
                else:
                    print("Invalid selection, please try again (enter 1-3 or press Enter)")
        
        elif tool_name == "DescribeResource":
            args["namespace"] = DEFAULT_NAMESPACE
            args["resource_type"] = input("Enter resource type (e.g., 'pod', 'deployment'): ").strip()
            args["name"] = input("Enter resource name: ").strip()
        
        elif tool_name == "GetAppYAML":
            print(f"Allowed application names: {', '.join(BOUTIQUE)}")
            args["app_name"] = input("Enter application name: ").strip()
        
        elif tool_name == "GetServiceDependencies":
            print(f"Allowed service names: {', '.join(BOUTIQUE)}")
            args["service_name"] = input("Enter service name: ").strip()
        
        elif tool_name == "GetRecentLogs":
            args["namespace"] = DEFAULT_NAMESPACE
            args["service_name"] = input("Enter service name: ").strip()
            args["lines"] = int(input("Enter number of log lines: ").strip())
        
        elif tool_name == "GetErrorLogs":
            args["namespace"] = DEFAULT_NAMESPACE
            args["service_name"] = input("Enter service name: ").strip()

        elif tool_name == "CheckServiceConnectivity":
            args["namespace"] = DEFAULT_NAMESPACE
            args["service_name"] = input("Enter service name: ").strip()
            while True:
                try:
                    args["port"] = int(input("Enter port: ").strip())
                    break
                except ValueError:
                    print("Port must be an integer, please try again")
        
        elif tool_name == "GetClusterConfiguration":
            print("⚠️  GetClusterConfiguration requires no parameters and will directly return cluster configuration")

        elif tool_name == "GetAlerts":
            print("⚠️  GetAlerts requires no parameters and will directly return alert information")
        
        elif tool_name == "CheckNodeServiceStatus":
            args["node_name"] = input("Enter node name: ").strip()
            args["service_name"] = input("Enter service name: ").strip()
        
        return args
    
    def run(self):
        """Simplified run logic; keep only tool invocation and interaction, no logging"""
        self.print_welcome()
        
        while True:
            self.print_tool_list()
            try:
                choice = int(input("Select tool number: ").strip())
                total_tools = len(self.tools)
                
                # Keep exit logic only
                if choice == total_tools + 1:
                    # On exit, show diagnosis result from metadata.json if available
                    meta_path = os.path.join(self.snapshot_path, "metadata.json")
                    if os.path.exists(meta_path):
                        try:
                            with open(meta_path, "r", encoding="utf-8") as f:
                                meta = json.load(f)
                            result = meta.get("result", {})
                            fault_taxonomy = result.get("fault_taxonomy", "N/A")
                            fault_object = result.get("fault_object", "N/A")
                            root_cause = result.get("root_cause", "N/A")

                            print("\n===== Diagnosis Result from Metadata =====")
                            print(f"Fault taxonomy : {fault_taxonomy}")
                            print(f"Fault object   : {fault_object}")
                            print(f"Root cause     : {root_cause}")
                            print("==========================================")
                        except Exception as e:
                            print(f"\n⚠️  Failed to read diagnosis result from metadata.json: {e}")
                    else:
                        print("\n⚠️  metadata.json not found; no diagnosis result available.")

                    print("\n👋 Exiting test mode; no data was saved")
                    return
                
                # Tool selection and invocation
                elif 1 <= choice <= total_tools:
                    tool = self.tools[choice - 1]
                    tool_name = tool["name"]
                    print(f"\nYou selected: {tool_name}")
                    
                    # Get arguments
                    args = self.get_tool_arguments(tool_name)
                    print(f"\nExecuting tool (namespace: {DEFAULT_NAMESPACE})...")
                    
                    # Call tool and output result (no logging)
                    try:
                        result = tool["method"](** args)
                        print("\nTool result:")
                        print("-" * 60)
                        
                        # Keep original result formatting logic (for test display only)
                        if tool_name == "GetRecentLogs":
                            try:
                                if isinstance(result, list):
                                    for log_line in result:
                                        print(log_line)
                                elif isinstance(result, str):
                                    log_list = json.loads(result)
                                    if isinstance(log_list, list):
                                        for log_line in log_list:
                                            print(log_line)
                                    else:
                                        print(result)
                                else:
                                    print(result)
                            except Exception:
                                print(result) 
                        elif tool_name == "GetErrorLogs":
                            try:
                                error_log_data = json.loads(result) if isinstance(result, str) else result
                                pretty_error_log = json.dumps(error_log_data, ensure_ascii=False, indent=2)
                                print(pretty_error_log)
                            except (json.JSONDecodeError, Exception) as e:
                                print(f"⚠️  GetErrorLogs JSON parse failed, raw output: {result}")
                        elif tool_name in ["GetAlerts", "GetClusterConfiguration"]:
                            pretty_json=json.dumps(result, ensure_ascii=False, indent=2)
                            print(pretty_json)
                        else:
                            print(result)
                        print("-" * 60)
                        
                    except Exception as e:
                        print(f"\n❌ Tool {tool_name} call failed: {str(e)}")
                    
                    input("\nPress Enter to continue...")
                else:
                    print("Invalid selection, please try again")
            
            except ValueError:
                print("Please enter a valid number")

def get_random_fault_case(fault_path):
    """Randomly select a fault case"""
    # Filter all fault directories
    fault_cases = [
        d for d in os.listdir(fault_path)
        if os.path.isdir(os.path.join(fault_path, d))
    ]
    if not fault_cases:
        print(f"❌ No valid fault cases under directory {fault_path}")
        return None, None
    
    # Randomly choose one
    random_case = random.choice(fault_cases)
    case_path = os.path.join(fault_path, random_case)
    
    # Read query from metadata
    meta_path = os.path.join(case_path, "metadata.json")
    if not os.path.exists(meta_path):
        print(f"⚠️  Fault case {random_case} is missing metadata.json, using default query")
        query = "test fault query"
    else:
        with open(meta_path, 'r', encoding='utf-8') as f:
            metadata_data = json.load(f)
        query = metadata_data.get("query", "test fault query")
    
    print(f"\n🎲 Randomly selected fault case: {random_case}")
    return case_path, query

if __name__ == "__main__":
    # Root directory of fault cases
    fault_path='benchmark/scheduling'
    
    # 1. Randomly select a fault case
    case_path, query = get_random_fault_case(fault_path)
    if not case_path:
        exit(0)
    
    # 2. Initialize test tool and run (no logging or persistence)
    tester = DiagnosticTester(case_path, query)
    tester.run()
    
    print("\n✅ Test completed; no data was recorded or saved")
