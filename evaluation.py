
import os
import re
import json
from util import extract_completed_info_to_result,batch_extract_traces,process_llm_traj_to_evaluation,count_llm_output_abnormal,calculate_redundancy_rate
import shutil
from pathlib import Path


def calculate_in_order_match(expert_seq, llm_seq):
    if not expert_seq:
        return 1.0
    expert_idx = 0
    for action in llm_seq:
        if action == expert_seq[expert_idx]:
            expert_idx += 1
            if expert_idx == len(expert_seq):
                return 1.0
    return 0.0

def process_eval(ground_truth_file, llm_trace_file):
    try:
        with open(ground_truth_file, 'r', encoding='utf-8') as f:
            ground_truth_data = json.load(f)["process"]
        with open(llm_trace_file, 'r', encoding='utf-8') as f:
            llm_data = json.load(f)
    except FileNotFoundError as e:
        print(f"❌ file not found: {e}")
        return 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0
    except Exception as e:
        print(f"❌ reading file error: {e}")
        return 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0

    llm_seq = llm_data.get("step", [])
    llm_actions = set(llm_seq)
    llm_seq_len = len(llm_seq)

    if not llm_actions:
        return 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, llm_seq_len

    best_f1 = -1.0
    best_precision = 0.0
    best_recall = 0.0
    best_order_match = 0.0
    best_exact_match = 0.0
    best_any_order_match = 0.0

    # 2 expert
    for expert_id, trace in ground_truth_data.items():
        expert_seq = trace
        expert_actions = set(expert_seq)
        if not expert_actions:
            continue

  
        intersection = len(llm_actions & expert_actions)
        p = intersection / len(llm_actions)
        r = intersection / len(expert_actions)
        f1 = 2 * (p * r) / (p + r) if (p + r) > 0 else 0.0
        

        current_order_match = calculate_in_order_match(expert_seq, llm_seq)
        current_exact_match = 1.0 if expert_seq == llm_seq else 0.0
        current_any_order_match = 1.0 if expert_actions.issubset(llm_actions) else 0.0

        if f1 > best_f1:
            best_f1 = f1
            best_precision = p
            best_recall = r
            best_order_match = current_order_match
            best_exact_match = current_exact_match
            best_any_order_match = current_any_order_match
        

        elif f1 == best_f1:
            if current_order_match > best_order_match:
                best_order_match = current_order_match
                best_precision = p
                best_recall = r
                best_exact_match = current_exact_match
                best_any_order_match = current_any_order_match
            
    if best_f1 == -1.0:
        return 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, llm_seq_len

    return best_recall, best_precision, best_f1, best_order_match, best_exact_match, best_any_order_match, llm_seq_len

def evaluation(a_root_dir, b_root_dir):
    """
    :param a_root_dir: groundtruth
    :param b_root_dir: LLM
    :return: metrics
    """
  
    total_cases = 0          
    rank1_correct = 0        
    rank3_correct = 0   
    partial_rank1_correct = 0  
    partial_rank3_correct = 0       
    empty_predictions_files = []
    missing_a_case_files = []
    missing_metadata_files = []
    missing_result_files = []
    invalid_format_files = []  
    trace_recall=[]
    trace_precision=[]
    trace_f1=[]
    trace_exact=[]
    trace_anyorder=[]
    trace_len=[]
    trace_inorder=[]
    trace_invalid_action=[]
    trace_latency=[]
    trace_redundancy=[]
    valid_trace_count = 0
    result_exist_count = 0


    if not os.path.isdir(a_root_dir):
        print(f"❌ error {a_root_dir} not exist")
        return None
    if not os.path.isdir(b_root_dir):
        print(f"❌ error: {b_root_dir} not exist")
        return None

    b_fault_cases = [
        d for d in os.listdir(b_root_dir)
        if os.path.isdir(os.path.join(b_root_dir, d))
    ]
    

    error_cases = []
    
    for fault_case_name in b_fault_cases:
        total_cases += 1
     
        a_case_path = os.path.join(a_root_dir, fault_case_name)
        a_metadata_path = os.path.join(a_case_path, "metadata.json")
        b_case_path = os.path.join(b_root_dir, fault_case_name)
        b_result_path = os.path.join(b_case_path, "result.json")
        b_trace_path=os.path.join(b_case_path, "llm_trace_evaluation.json")
        b_trace_detail=os.path.join(b_case_path, "llm_traj.json")
        b_raw_trace=os.path.join(b_case_path, "trace.json")
        
        
        rank1_flag = False
        rank3_flag = False
        partial_rank1_flag = False
        partial_rank3_flag = False
        error_tool_use_count = 0
        redundancy = 0.0
        valid_trace = []
        
        if os.path.exists(b_result_path):
            result_exist_count += 1

        if not os.path.isdir(a_case_path):
            missing_a_case_files.append(fault_case_name)
            continue

        try:
            if not os.path.exists(a_metadata_path):
                missing_metadata_files.append(fault_case_name)
                continue

            with open(a_metadata_path, 'r', encoding='utf-8') as f:
                a_metadata = json.load(f)
            a_result = a_metadata.get("result", {})
            a_taxonomy = a_result.get("fault_taxonomy", "")
            a_object = a_result.get("fault_object", "")
            a_root_cause = a_result.get("root_cause", "")

            

        except Exception as e:
            invalid_format_files.append(fault_case_name)
            continue

 
        error_tool_use_count = count_llm_output_abnormal(b_trace_detail)
    
        if os.path.exists(b_trace_path):
            redundancy = calculate_redundancy_rate(b_trace_path)
        trace_redundancy.append(redundancy)

        latency_value = 0.0
        
   
        if os.path.exists(b_raw_trace):
            with open(b_raw_trace, "r", encoding="utf-8") as f:
                raw_trace = json.load(f)
            latency_value = raw_trace.get("latency", 0.0)
        trace_latency.append(latency_value)


        b_predictions = []
        try:
            if not os.path.exists(b_result_path):
                missing_result_files.append(fault_case_name)
            else:
                with open(b_result_path, 'r', encoding='utf-8') as f:
                    b_result = json.load(f)
                b_predictions = b_result.get("top_3_predictions", [])

            
            error_detail = ""
            if not b_predictions:
                empty_predictions_files.append(fault_case_name)
                error_tool_use_count += 1
                error_detail = f"【{fault_case_name}】- top_3_predictions is null | groundtruth：taxonomy={a_taxonomy}, object={a_object}, root_cause={a_root_cause},invalid action={error_tool_use_count}"
                error_cases.append(error_detail)
            else:
                for idx, pred in enumerate(b_predictions[:3]):
                    p_taxonomy = pred.get("fault_taxonomy", "").lower()
                    p_object = pred.get("fault_object", "").lower()
                    p_root_cause = pred.get("root_cause", "").lower()

                    full_match = (p_taxonomy == a_taxonomy.lower() and 
                                p_object == a_object.lower() and 
                                p_root_cause == a_root_cause.lower())
                    partial_match = (p_object == a_object.lower() and p_root_cause == a_root_cause.lower())

                    if full_match:
                        if idx == 0:
                            rank1_flag = True
                        rank3_flag = True
                    if partial_match:
                        if idx == 0:
                            partial_rank1_flag = True
                        partial_rank3_flag = True

                # incorrect details
                if not rank1_flag or not rank3_flag:
                    error_detail = f"【{fault_case_name}】\n"
                    error_detail += f"  ground truth: taxonomy={a_taxonomy}, object={a_object}, root_cause={a_root_cause}\n"
                    error_detail += f"  rank1 result: "
                    rank1_pred = b_predictions[0] if len(b_predictions) > 0 else {}
                    r1_tax = rank1_pred.get("fault_taxonomy", "null")
                    r1_obj = rank1_pred.get("fault_object", "null")
                    r1_root = rank1_pred.get("root_cause", "null")
                    error_detail += f"taxonomy={r1_tax}, object={r1_obj}, root_cause={r1_root} (匹配：{rank1_flag})\n"
                    error_detail += f" rank3 result:{rank3_flag}）\n"
                    error_cases.append(error_detail)

       
            if rank1_flag:
                rank1_correct += 1
            if rank3_flag:
                rank3_correct += 1
            if partial_rank1_flag:
                partial_rank1_correct += 1
            if partial_rank3_flag:
                partial_rank3_correct += 1

        except Exception as e:
            invalid_format_files.append(fault_case_name)
            error_detail = f"【{fault_case_name}】- reading result.json error：{str(e)}"
            error_cases.append(error_detail)

        
        recall, precision, f1, in_order_match,exact_match,any_order_match, llm_step = process_eval(a_metadata_path, b_trace_path)
        trace_precision.append(precision)
        trace_recall.append(recall)
        trace_f1.append(f1)
        trace_inorder.append(in_order_match)
        trace_exact.append(exact_match)
        trace_anyorder.append(any_order_match)
        trace_len.append(llm_step)
        trace_invalid_action.append(error_tool_use_count)
        
        if llm_step > 0:
            valid_trace_count += 1

    print("\n❌ Error case")
    print("-" * 120)
    if error_cases:
        for idx, error in enumerate(error_cases, 1):
            print(f"{idx}. {error}")
    
    print("-" * 60)


    missing_a_case = len(missing_a_case_files)
    missing_metadata = len(missing_metadata_files)
    missing_result = len(missing_result_files)
    invalid_format = len(invalid_format_files)
    empty_predictions = len(empty_predictions_files)
    
    valid_cases = total_cases - missing_a_case - missing_metadata - missing_result - invalid_format
    rank1_accuracy = round(rank1_correct / total_cases , 3) if total_cases > 0 else 0.0
    rank3_accuracy = round(rank3_correct / total_cases , 3) if total_cases > 0 else 0.0
    parti_rank1_accuracy = round(partial_rank1_correct / total_cases , 3) if total_cases > 0 else 0.0
    parti_rank3_accuracy = round(partial_rank3_correct / total_cases ,3) if total_cases > 0 else 0.0
    
    tool_precision_avg = round(sum(trace_precision) / total_cases , 3) if total_cases > 0 else 0.0
    tool_recall_avg = round(sum(trace_recall) / total_cases ,3) if total_cases > 0 else 0.0
    tool_f1_avg = round(sum(trace_f1) / total_cases, 3) if total_cases > 0 else 0.0
    latency_avg = round(sum(trace_latency) / (result_exist_count - empty_predictions), 3) if total_cases > 0 else 0.0
    tool_inorder_avg = round(sum(trace_inorder) / total_cases, 3) if total_cases > 0 else 0.0
    tool_exact_avg = round(sum(trace_exact) / total_cases, 3) if total_cases > 0 else 0.0
    tool_anyorder_avg = round(sum(trace_anyorder) / total_cases, 3) if total_cases > 0 else 0.0
    tool_len_avg = round(sum(trace_len) / total_cases, 2) if total_cases > 0 else 0.0
    tool_invalid_avg = round(sum(trace_invalid_action) / total_cases, 2) if total_cases > 0 else 0.0
    
    redundancy_avg = round(sum(trace_redundancy) / valid_trace_count, 3) if valid_trace_count > 0 else 0.0
    
    
    task_complete_rate=round((result_exist_count - empty_predictions) / total_cases, 2) if total_cases > 0 else 0.0
    no_tool_use= round(1-(valid_trace_count/ total_cases), 2) if total_cases > 0 else 0.0
   
  
    print(f"【Basic Statistics】")
    print(f"Total fault cases of LLM diagnose: {len(b_fault_cases)}")
    print(f"Valid comparison cases (accuracy calculable): {valid_cases}")
    print(f"Number of existing result.json files: {result_exist_count} (Total cases: {total_cases})")
    print(f"Valid LLM step count (trace length > 0): {valid_trace_count} (Total cases: {total_cases})")

    print(f"  - missing LLM diagnosis results: {missing_result} → {', '.join(missing_result_files) if missing_result_files else 'None'}")
    print(f"  - Missing fields/format errors: {invalid_format} → {', '.join(invalid_format_files) if invalid_format_files else 'None'}")
    print(f"  - {empty_predictions} empty results → {', '.join(empty_predictions_files) if empty_predictions_files else 'None'}")
    print("-" * 60)
    print(f"【Outcome-based Metrics】")
    print(f"Task Completion Rate (TCR):{task_complete_rate}")
    print(f"Top-1 Accuracy Rate:{rank1_correct}/{total_cases} = {rank1_accuracy}")
    print(f"Top-3 Accuracy Rate:{rank3_correct}/{total_cases} = {rank3_accuracy}")
    print(f"Part-1 Accuracy Rate:{partial_rank1_correct}/{total_cases} = {parti_rank1_accuracy}")
    print(f"Part-3 Accuracy Rate:{partial_rank3_correct}/{total_cases} = {parti_rank3_accuracy}")
    print("=" * 60)
    print(f"【Process-based Metrics】")
    print(f"Exact Match:{tool_exact_avg}")
    print(f"In-Order Match:{tool_inorder_avg}")
    print(f"Any-Order Match:{tool_anyorder_avg}")
    print(f"Tool Relevance:{tool_precision_avg}")
    print(f"Tool Coverage:{tool_recall_avg}")
    print(f"Tool F1:{tool_f1_avg}")
    print(f"Avg Steps:{tool_len_avg}")
    print(f"Invalid Action Count (IAC):{tool_invalid_avg}")
    print(f"MIIT:{latency_avg}")
    print(f"Redundant Action Rate (RAR):{redundancy_avg}")
    print(f"Zero-Tool Diagnosis Rate (ZTDR):{no_tool_use}")
  
    
    return {
        "total_cases": total_cases,
        "valid_cases": valid_cases,
        "rank1_accuracy": rank1_accuracy,
        "rank3_accuracy": rank3_accuracy,
        "partial_rank1_accuracy": parti_rank1_accuracy,
        "partial_rank3_accuracy": parti_rank3_accuracy,
        "result_exist_count": result_exist_count,
        "valid_trace_count": valid_trace_count,
        "redundancy_avg": redundancy_avg,
        "tool_precision_avg": tool_precision_avg,
        "tool_recall_avg": tool_recall_avg,
        "tool_f1_avg": tool_f1_avg,
        "task_complete_rate": task_complete_rate
    }



if __name__ == "__main__":
    fault_category='startup'
    model='qwen3-14b'
    method='icl'
    A_ROOT_DIRECTORY = f"/root/k8srca/Cloud-OpsBench/benchmark/{fault_category}" # groundtruth path
    B_ROOT_DIRECTORY = f"/root/k8srca/Cloud-OpsBench/qwen3-14b_icl/{fault_category}"  # diagnose result path

    extract_completed_info_to_result(B_ROOT_DIRECTORY) # for root
    batch_extract_traces(B_ROOT_DIRECTORY)  # extract trace
    process_llm_traj_to_evaluation(B_ROOT_DIRECTORY) # pure trace
    # find_empty_trace_json_non_recursive(B_ROOT_DIRECTORY)
    print("\n===== calculating result metric =====")
    stats = evaluation(A_ROOT_DIRECTORY, B_ROOT_DIRECTORY)
