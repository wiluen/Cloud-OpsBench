import os
from crewai import Agent, Task, Crew, Process
from crewai.llm import LLM
from typing import Any, Dict, List, Optional
import json
import time
import yaml
from RCA_candidate import expected_output,agent_prompt
from langfuse import Langfuse, get_client
from tools.definition import create_k8s_tools
from openinference.instrumentation.crewai import CrewAIInstrumentor
from config_utils import load_config, init_langfuse_env
from prompt_optimization import get_cot_prompt,get_icl_prompt,get_rag_prompt
# -----configuration----
config = load_config()
init_langfuse_env(config)
llm_conf = config.llm
diag_conf = config.diagnosis
MODEL_NAME = llm_conf['model']
myllm = LLM(
    model=llm_conf['model'],
    api_base=llm_conf['api_base'],
    api_key=llm_conf['api_key'],
    temperature=llm_conf['temperature'],
    max_tokens=llm_conf['max_tokens'],
    timeout=llm_conf['timeout'],
    extra_body={"enable_thinking": False},
    stream=True
)

workspace_path=diag_conf["workspace_path"]
fault_category = diag_conf['fault_category']
fault_path = f'{workspace_path}/benchmark/{fault_category}' # benchmark path
prompt_eng=diag_conf['prompt_strategy']
diag_path = f'{workspace_path}/{MODEL_NAME}_{prompt_eng}/{fault_category}' # model result path

max_iterations = diag_conf['max_iterations']

print("✅ Configuration loading completed, with the following parameters")
print(f"Model：{MODEL_NAME} | Fault type：{fault_category} | Max iter：{max_iterations}")
print(f"workspace path：{workspace_path} | output path：{diag_path}")



langfuse = get_client()
try:
    if langfuse.auth_check():
        print("Langfuse client is authenticated and ready!")
    else:
        print("Authentication failed. Please check your credentials and host.")
except Exception as e:
    print(f"Error：{e}")

CrewAIInstrumentor().instrument(skip_dep_check=True)


dir_contents = os.listdir(fault_path)
print(dir_contents)
for fault_case in dir_contents:
    path = os.path.join(fault_path, fault_case)
    meta_path = os.path.join(path, "metadata.json")

    if prompt_eng=='base':prompt=agent_prompt
    elif prompt_eng=='cot':prompt=get_cot_prompt()
    elif prompt_eng=='rag':prompt=get_rag_prompt()
    elif prompt_eng=='icl':
        demo_path=f'{workspace_path}/expert-trajectory/{fault_category}'
        prompt=get_icl_prompt(demo_path,fault_path)
    else:
        print('choose correct prompt_strategy')
    print(prompt)
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
            backstory=prompt,
            tools=tools_list,
            llm=myllm,
            max_iter=max_iterations,
            allow_delegation=False,
            verbose=True
        )
        
        diagnostic_task = Task(
            description = f"""
                The Kubernetes environment in namespace `{ns}` is experiencing a fault. A high-level symptom has been reported: '{query}'
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

    
