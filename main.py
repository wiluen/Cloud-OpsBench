import os
from crewai import Agent, Task, Crew, Process
from crewai.llm import LLM
from typing import Any, Dict, List, Optional
import json
import time
import yaml
from RCA_candidate import expected_output,agent_prompt
from langfuse import Langfuse, get_client
from k8s_tools_crewai import create_k8s_tools
from openinference.instrumentation.crewai import CrewAIInstrumentor


MODEL_NAME='model'
myllm = LLM(
    model=MODEL_NAME,
    api_base="",
    api_key=""
)
os.environ["LANGFUSE_PUBLIC_KEY"] = "" 
os.environ["LANGFUSE_SECRET_KEY"] = ""
os.environ["LANGFUSE_BASE_URL"] = "http://localhost:3000"

langfuse = get_client()
try:
    if langfuse.auth_check():
        print("Langfuse client is authenticated and ready!")
    else:
        print("Authentication failed. Please check your credentials and host.")
except Exception as e:
    print(f"Error：{e}")

CrewAIInstrumentor().instrument(skip_dep_check=True)


fault_category='schedule'
diag_path=f'/root/k8srca/{MODEL_NAME}_test/{fault_category}'
fault_path=f'/root/k8srca/k8s_dataset/{fault_category}'
dir_contents = os.listdir(fault_path)
print(dir_contents)
for fault_case in dir_contents:
    path = os.path.join(fault_path, fault_case)
    meta_path = os.path.join(path, "metadata.json")
    if not os.path.exists(meta_path):
        print(f"metadata file not exist: {meta_path}")
        continue
    else:
        tools_list = create_k8s_tools(path)
        diag_case_path=os.path.join(diag_path,fault_case)
        os.makedirs(diag_case_path,exist_ok=True)
        trace_path=os.path.join(diag_case_path, "trace.json")
        if os.path.exists(trace_path): 
            continue
        else:
            trace_errir_path=os.path.join(diag_case_path, "trace_error.json")
            with open(meta_path, 'r', encoding='utf-8') as f:
                metadata_data = json.load(f)
            query=metadata_data.get("query", "")
            ns=metadata_data.get("namespace", "")
            k8s_diagnoser_agent = Agent(
                role="Kubernetes Troubleshooting Expert",
                goal="Identify the root cause of Kubernetes microservice failures using a systematic diagnostic methodology",
                backstory=agent_prompt,
                tools=tools_list,
                llm=myllm,
                max_iter=15,
                allow_delegation=False,
                verbose=True
            )
            
            diagnostic_task = Task(
                description = f"""
                    The Kubernetes environment in namespace `{ns}` is experiencing a fault. A high-level symptom has been reported: '{query}'
                    **Mission Objective:** Find the root cause of this problem.
                    **Diagnostic Process:** This is an iterative, multi-step diagnosis. You must actively gather evidence by systematically calling your tools. Use the output (Observation) from one tool to decide your next action. Investigate systematically until you have enough evidence to determine the single root cause.
                    You must **independently decide** when, in what order, and how to use these tools to solve the problem.
                    """,
                expected_output =expected_output,
                agent=k8s_diagnoser_agent
            )

            k8s_crew = Crew(
                agents=[k8s_diagnoser_agent],
                tasks=[diagnostic_task],
                process=Process.sequential,
                verbose=True
            )

            print(f"=== Start Kubernetes Diagnosis Crew , Fault Case: {path} ===")

            try:
                with langfuse.start_as_current_span(name="k8s_diag") as span:
                    crewResult = k8s_crew.kickoff()
                    trace_id = span.trace_id
                    print(f"[Langfuse] Trace created with ID: {trace_id}")
            except Exception as span_error:
                print(f"[Langfuse] Failed to create span: {span_error}")
                crewResult = k8s_crew.kickoff()
            print(crewResult)
            langfuse.flush()

            if trace_id:
                max_retries = 5
                retry_delay = 2

                for attempt in range(max_retries):
                    try:
                        langfuse_client = get_client()
                        trace = langfuse_client.api.trace.get(trace_id)

                        if trace:
                            with open(trace_path, "w") as f:
                                json.dump(trace.dict() if hasattr(trace, "dict") else trace,f, indent=2, default=str)
                            break
                    except Exception as e:
                        if attempt < max_retries - 1:
                            time.sleep(retry_delay)
                        else:
                            with open(trace_errir_path, "w") as f:
                                f.write(f"Failed to retrieve trace: {e}")

     
