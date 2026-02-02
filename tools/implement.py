import shlex
import os
import json
import subprocess
from typing import Optional

# boutique 服务列表
BOUTIQUE=['adservice','cartservice','checkoutservice','currencyservice','emailservice','frontend','paymentservice','productcatalogservice','recommendationservice','redis-cart','shippingservice']


RESOURCE_ALIASES_DB = {
    "pod": "pods", "pods": "pods", "po": "pods",
    "service": "services", "services": "services", "svc": "services",
    "deployment": "deployments", "deployments": "deployments", "deploy": "deployments",
    "statefulset": "statefulsets", "statefulsets": "statefulsets", "sts": "statefulsets",
    "daemonset": "daemonsets", "daemonsets": "daemonsets", "ds": "daemonsets",
    "configmap": "configmaps", "configmaps": "configmaps", "cm": "configmaps",
    "secret": "secrets", "secrets": "secrets",
    "persistentvolumeclaim": "persistentvolumeclaims", "persistentvolumeclaims": "persistentvolumeclaims", "pvc": "persistentvolumeclaims",
    "replicaset": "replicasets", "replicasets": "replicasets", "rs": "replicasets",
    "ingress": "ingresses", "ingresses": "ingresses", "ing": "ingresses",
    "networkpolicy": "networkpolicies", "networkpolicies": "networkpolicies", "netpol": "networkpolicies",
    "serviceaccount": "serviceaccounts", "serviceaccounts": "serviceaccounts", "sa": "serviceaccounts",
    "job": "jobs", "jobs": "jobs",
    "endpoint": "endpoints", "endpoints": "endpoints", "ep": "endpoints",
    "persistentvolume": "persistentvolumes", "persistentvolumes": "persistentvolumes", "pv": "persistentvolumes",
    "namespace": "namespaces", "namespaces": "namespaces", "ns": "namespaces",
    "node": "nodes", "nodes": "nodes", "no": "nodes",
    "storageclass": "storageclasses", "storageclasses": "storageclasses", "sc": "storageclasses",
    "event": "events", "events": "events",
    "resourcequota": "resourcequota","resourcequotas":"resourcequota"
}

def normalize_resource_type(resource_type):
    if not resource_type:
        return None
    key = resource_type.lower()
    return RESOURCE_ALIASES_DB.get(key)


class KubernetesTools:
    def __init__(self,case_path):
        
        tool_cache_path=os.path.join(case_path, "tool_cache.json")
        raw_log_path=os.path.join(case_path,"raw_data", "logs.json")
        with open(tool_cache_path, 'r', encoding='utf-8') as f:
            self.tool_cache = json.load(f)
        with open(raw_log_path, 'r', encoding='utf-8') as f:
            self.raw_logs = json.load(f)

   
    def GetResources(
        self,
        resource_type: str,
        namespace: str,
        name: str = None,
        show_labels: bool = False,
        output_wide: bool = False,
        label_selector: str = None
    ) -> str:
        if not namespace:
            raise ValueError("Error: 'GetResources' command requires a specific 'namespace'.")
        resource_type_norm=normalize_resource_type(resource_type)
        if not resource_type_norm:
          
            return f"Error: Unknown resource type '{resource_type}'"
        
        params = {
            "resource_type": resource_type_norm,
            "name": name if name is not None else "",
            "namespace": namespace
        }
        if output_wide:
            params["output_wide"] = True
        if show_labels:
            params["show_labels"] = True
        if label_selector and label_selector.strip() != "":
            params["label_selector"] = label_selector

        command_key = f"GetResources:{json.dumps(params, ensure_ascii=False,separators=(',', ':'))}"

        active_modes = sum([show_labels, output_wide, (label_selector is not None)])
        if active_modes > 1:
            raise ValueError(
                "Error: Only one of '--show-labels', '-o wide', or '-l <selector>' can be specified at a time for kubectl get."
            )
        
        try:
            return self.tool_cache[command_key]
        except KeyError:

            if name:
                return f"Error from server (NotFound): {resource_type_norm} \"{name}\" not found in namespace \"{namespace}\""
            else:
                return f"No resources found in {namespace} namespace."
        except Exception as e:
            return f"An unexpected error occurred during snapshot lookup for '{command_key}': {e}"
    
 
    def DescribeResource(
        self,
        resource_type: str,
        name: str,
        namespace: str
    ) -> str:
        if not resource_type:
            raise ValueError("Error: 'DescribeResource' command requires a specific 'resource_type'.")
        if not name:
            raise ValueError("Error: 'DescribeResource' command requires a specific 'name'.")
        if not namespace:
            raise ValueError("Error: 'DescribeResource' command requires a specific 'namespace'.")
        
        resource_type_norm=normalize_resource_type(resource_type)
        if not resource_type_norm:
            return f"Error: Unknown resource type '{resource_type}'"
        if resource_type in ["namespaces","namespace","ns"]:
            return "Error: Describing namespaces is not supported. Instead, use `GetResources` to check `resourcequota`."
        params = {
            "resource_type": resource_type_norm,
            "name": name,
            "namespace": namespace
        }

        command_key = f"DescribeResource:{json.dumps(params, ensure_ascii=False,separators=(',', ':'))}"
        print(command_key)
        try:
            return self.tool_cache[command_key]
        except KeyError:
            if name:
                return f"Error from server (NotFound): {resource_type} \"{name}\" not found in namespace \"{namespace}\""
            else:
                return "Error: resource name is required for 'describe' command."
        except Exception as e:
            return f"An unexpected error occurred during snapshot lookup for '{command_key}': {e}"
    
 
    def GetAppYAML(
        self, app_name: str,
        ) -> str:
        if not app_name:
            raise ValueError("Error: 'GetAppYAML' command requires a specific 'app_name'.")

        if app_name not in BOUTIQUE:
            raise ValueError(f"Error: Resource '{app_name}' is not in the allowed list of boutique services. Allowed: {BOUTIQUE}")
        
        params = {"app_name": app_name}
        command_key = f"GetAppYAML:{json.dumps(params,separators=(',', ':'))}"
        print(command_key)
      
        try:
            return self.tool_cache[command_key]
        except KeyError:
            
            error_msg = f"Error: YAML configuration for '{app_name}' is not recorded."
            return error_msg
        except Exception as e:
            return f"An unexpected error occurred during snapshot lookup for '{command_key}': {e}"
    

    def GetServiceDependencies(
        self, service_name: str
    ) -> str:
        if not service_name:
            raise ValueError("Error: 'GetServiceDependencies' command requires a specific 'service_name'.")
  
        if service_name not in BOUTIQUE:
            raise ValueError(f"Error: Resource '{service_name}' is not in the allowed list of boutique services. Allowed: {BOUTIQUE}")
        
        params = {"service_name": service_name}
        command_key = f"GetServiceDependencies:{json.dumps(params,separators=(',', ':'))}"
        print(command_key)
        try:
            return self.tool_cache[command_key]
        except KeyError:
            error_msg = f" Error: Dependencies for '{service_name}' not recorded in trace data."
            return error_msg
        except Exception as e:
            return f"An unexpected error occurred during snapshot lookup for '{command_key}': {e}"


    def GetRecentLogs(
        self,
        namespace: str,
        service_name: str,
        lines: int = 50
    ) -> str:
        if not service_name:
            raise ValueError("Error: GetRecentLogs requires a specific 'service_name'.")
        if not namespace:
            raise ValueError("Error: GetRecentLogs requires a specific 'namespace'.")
        if namespace != "boutique":
            return ""
        
        try:
            return self.raw_logs[service_name][-lines:]
        except KeyError:
            error_msg = f" Error: The query result of GetRecentLogs was not found in records. Please check whether the parameters are correct (such as whether the resource type, name, namespace exist or are misspelled) to avoid invalid function calls."
            return error_msg
        except Exception as e:
            return f"An unexpected error occurred during snapshot lookup for GetRecentLogs:{service_name}: {e}"

    
    def CheckServiceConnectivity(
        self,
        service_name: str,
        port: int,
        namespace: str
    ) -> str:
        if not service_name:
            raise ValueError("Error: 'service_name' is required for connectivity check.")
        if port is None:
            raise ValueError("Error: 'port' is required for connectivity check.")
        if not namespace:
            raise ValueError("Error: 'namespace' is required for connectivity check.")

        try:
            port = int(port)
        except (ValueError, TypeError):
            raise ValueError(f"Error: 'port' must be an integer, got {type(port).__name__}")
        
        params = {
            "namespace": namespace,
            "service_name": service_name,
            "port": port
        }
        command_key = f"CheckServiceConnectivity:{json.dumps(params,separators=(',', ':'))}"
        print(command_key)

        try:
            return self.tool_cache[command_key]
        except KeyError:
            return f"Connection failed"
        except Exception as e:
            return f"An unexpected error occurred during snapshot lookup for '{command_key}': {e}"

    def GetClusterConfiguration(self) -> str:
   
        command_key = "GetClusterConfiguration:{}"
        print(command_key)
        try:
            return self.tool_cache[command_key]
        except KeyError:
            error_msg = f"Error: Cluster configuration snapshot is not available in the dataset."
            return error_msg
        except Exception as e:
            return f"An unexpected error occurred during snapshot lookup for '{command_key}': {e}"
        

    def GetAlerts(self) -> str:
        command_key = "GetAlerts:{}"

        print(command_key)
        try:
            return self.tool_cache[command_key]
        except KeyError:
            error_msg = f"Error: Cluster alerts is not available in the dataset."
            return error_msg
        except Exception as e:
            return f"An unexpected error occurred during snapshot lookup for '{command_key}': {e}"

    def GetErrorLogs(
            self,
            namespace: str,
            service_name: str
        )-> str:
        if not service_name:
            raise ValueError("Error: 'service_name' is required.")
        if not namespace:
            raise ValueError("Error: 'namespace' is required.")
        params = {
            "namespace": namespace,
            "service_name": service_name
            }
        command_key = f"GetErrorLogs:{json.dumps(params,separators=(',', ':'))}"
        print(command_key)
        try:
            log_summary_data = self.tool_cache[command_key]

            return json.dumps(log_summary_data, indent=2, ensure_ascii=False)
        except KeyError:
            error_msg = f"Error: Error logs for the specified service are not available."
            return error_msg
        except Exception as e:
            return f"An unexpected error occurred during snapshot lookup for '{command_key}': {e}"

    def CheckNodeServiceStatus(self, node_name: str, service_name: str) -> str:

        if not node_name:
            raise ValueError("Error: 'node_name' is required for checking node service status.")
        if not service_name:
            raise ValueError("Error: 'service_name' is required for checking node service status.")
        
     
        params = {
            "node_name": node_name,
            "service_name": service_name
        }
        command_key = f"CheckNodeServiceStatus:{json.dumps(params,separators=(',', ':'))}"
        print(command_key)

        try:
            return self.tool_cache[command_key]
        except KeyError:

            error_msg = f"Error: Status information for cluster control plane components is not available in the dataset"
            return error_msg
        except Exception as e:
            return f"An unexpected error occurred during snapshot lookup for '{command_key}': {e}"
        
