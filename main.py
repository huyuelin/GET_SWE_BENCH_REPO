import argparse
import concurrent.futures
import json
import os

from datasets import load_dataset
from tqdm import tqdm


from FL import LLMFL

from preprocess_data import (
    filter_none_python,
    filter_none_python_dependencies,
    filter_out_test_files,
    get_full_file_paths_and_classes_and_functions,
    show_project_structure,
    show_project_structure_dependencies_without_signature,
    show_project_structure_dependencies_with_signature,
    get_repo_files_dependencies,
)

from utils import (
    load_existing_instance_ids,
    load_json,
    load_jsonl,
    setup_logger,
)

from get_repo_structure import (
    clone_repo,
    get_project_structure_from_scratch,
    get_project_structure_from_scratch_dependencies
)

get_swe_bench_repo_prompt_only_file_names = """

Please look through the following GitHub problem description and Repository structure and provide a list of files that one would need to edit to fix the problem.

### GitHub Problem Description ###
{problem_statement}

###

### Repository Structure ###
{structure}

###

Please only provide the full path and return at most 5 files.
The returned files should be separated by new lines ordered by most to least important and wrapped with ```
For example:
```
file1.py
file2.py
```


"""



get_swe_bench_repo_prompt_function_without_signature = """

Please look through the following GitHub problem description and Repository structure with function names of each file and provide a list of files that one would need to edit to fix the problem.

### GitHub Problem Description ###
{problem_statement}

###

### Repository Structure ###
{structure}

###

Please provide the complete set of locations as either a class name, a function name, or a variable name.
Note that if you include a class, you do not need to list its specific methods.
You can include either the entire class or don't include the class name and instead include specific methods in the class.
### Examples:
```
full_path1/file1.py
function: my_function_1
class: MyClass1
function: MyClass2.my_method

full_path2/file2.py
variable: my_var
function: MyClass3.my_method

full_path3/file3.py
function: my_function_2
function: my_function_3
function: MyClass4.my_method_1
class: MyClass5
```

Return just the locations.


"""


get_swe_bench_repo_prompt_function_with_signature = """

Please look through the following GitHub problem description and Repository structure with function names and data dependencies of each file and provide a list of files that one would need to edit to fix the problem.

### GitHub Problem Description ###
{problem_statement}

###

### Repository Structure ###
{structure}

###

Please provide the complete set of locations as either a class name, a function name, or a variable name.
Note that if you include a class, you do not need to list its specific methods.
You can include either the entire class or don't include the class name and instead include specific methods in the class.
### Examples:
```
full_path1/file1.py
function: my_function_1
class: MyClass1
function: MyClass2.my_method

full_path2/file2.py
variable: my_var
function: MyClass3.my_method

full_path3/file3.py
function: my_function_2
function: my_function_3
function: MyClass4.my_method_1
class: MyClass5
```

Return just the locations.


"""


get_swe_bench_repo_prompt_full_text= """
Please look through the following GitHub problem description and Full Repository and provide a list of files that one would need to edit to fix the problem.

### GitHub Problem Description ###
{problem_statement}

###

### Full Repository ###
{structure}

###


Please provide the class name, function or method name, or the exact line numbers that need to be edited.
### Examples:
```
full_path1/file1.py
line: 10
class: MyClass1
line: 51

full_path2/file2.py
function: MyClass2.my_method
line: 12

full_path3/file3.py
function: my_function
line: 24
line: 156
```

Return just the location(s)

"""

import tiktoken
def num_tokens_from_messages(message, model="gpt-3.5-turbo-0301"):
    """Returns the number of tokens used by a list of messages."""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")
    if isinstance(message, list):
        # use last message.
        num_tokens = len(encoding.encode(message[0]["content"]))
    else:
        num_tokens = len(encoding.encode(message))
    return num_tokens




def localize(args):
    #swe_bench_data = load_dataset("princeton-nlp/SWE-bench_Lite", split="test")
    swe_bench_data = load_dataset("princeton-nlp/SWE-bench_Verified", split="test")
    

    count_for_instance = 0
    for bug in swe_bench_data:
        count_for_instance += 1
         
        instance_id = bug["instance_id"]
        
        if instance_id != args.instance_id:
            continue
        
        if args.only_file_names:
            d = get_project_structure_from_scratch(
                bug["repo"], bug["base_commit"], bug["instance_id"], "playground"
            )
            bench_data = [x for x in swe_bench_data if x["instance_id"] == instance_id][0]
            problem_statement = bench_data["problem_statement"]
            structure = d["structure"]
            filter_none_python(structure)  # some basic filtering steps
            
            # filter out test files (unless its pytest)
            if not d["instance_id"].startswith("pytest"):
                filter_out_test_files(structure)
                
        
            message = get_swe_bench_repo_prompt_only_file_names.format(
                problem_statement=problem_statement,
                structure=show_project_structure(structure).strip(),
            ).strip()
            
            token_count = num_tokens_from_messages(message, "gpt-4o-2024-05-13")
            print(f"num_tokens of the message: {token_count}")
            
            with open(args.output_file, "a") as f:
                f.write(
                    json.dumps(
                        {
                            "instance_id": d["instance_id"],
                            "num_tokens of the message" : token_count,
                            "message": message,
                            
                        }
                    )
                    + "\n"
                )
        
        if args.function_without_signature:
            
            d = get_project_structure_from_scratch_dependencies(
                bug["repo"], bug["base_commit"], bug["instance_id"], "playground"
            )
            
            bench_data = [x for x in swe_bench_data if x["instance_id"] == instance_id][0]# 获取当前实例的基准数据
            problem_statement = bench_data["problem_statement"]# 获取问题描述
            structure_dependencies = d["structure_dependencies"]# 获取项目结构
            filter_none_python_dependencies(structure_dependencies)# 过滤掉非 Python 文件
            if not d["instance_id"].startswith("pytest"):
                filter_out_test_files(structure_dependencies)
                
            message = get_swe_bench_repo_prompt_function_without_signature.format(
                problem_statement=problem_statement,
                structure=show_project_structure_dependencies_without_signature(structure_dependencies).strip(),
            ).strip()
            
            token_count = num_tokens_from_messages(message, "gpt-4o-2024-05-13")
            print(f"num_tokens of the message: {token_count}")
            
            with open(args.output_file, "a") as f:
                f.write(
                    json.dumps(
                        {
                            "instance_id": d["instance_id"],
                            "num_tokens of the message" : token_count,
                            "message": message,
                            
                        }
                    )
                    + "\n"
                )
                
        if args.function_with_signature:
            
            d = get_project_structure_from_scratch_dependencies(
                bug["repo"], bug["base_commit"], bug["instance_id"], "playground"
            )
            
            bench_data = [x for x in swe_bench_data if x["instance_id"] == instance_id][0]# 获取当前实例的基准数据
            problem_statement = bench_data["problem_statement"]# 获取问题描述
            structure_dependencies = d["structure_dependencies"]# 获取项目结构
            filter_none_python_dependencies(structure_dependencies)# 过滤掉非 Python 文件
            if not d["instance_id"].startswith("pytest"):
                filter_out_test_files(structure_dependencies)
                
            message = get_swe_bench_repo_prompt_function_with_signature.format(
                problem_statement=problem_statement,
                structure=show_project_structure_dependencies_with_signature(structure_dependencies).strip(),
            ).strip()
            
            token_count = num_tokens_from_messages(message, "gpt-4o-2024-05-13")
            print(f"num_tokens of the message: {token_count}")
            
            with open(args.output_file, "a") as f:
                f.write(
                    json.dumps(
                        {
                            "instance_id": d["instance_id"],
                            "num_tokens of the message" : token_count,
                            "message": message,
                            
                        }
                    )
                    + "\n"
                )
                
        if args.full_text:
            d = get_project_structure_from_scratch(
                bug["repo"], bug["base_commit"], bug["instance_id"], "playground"
            )
            bench_data = [x for x in swe_bench_data if x["instance_id"] == instance_id][0]
            problem_statement = bench_data["problem_statement"]
            structure = d["structure"]
            filter_none_python(structure)  # some basic filtering steps
            
            # filter out test files (unless its pytest)
            if not d["instance_id"].startswith("pytest"):
                filter_out_test_files(structure)
                
        
            message = get_swe_bench_repo_prompt_full_text.format(
                problem_statement=problem_statement,
                structure=structure,
            ).strip()
            
            token_count = num_tokens_from_messages(message, "gpt-4o-2024-05-13")
            print(f"num_tokens of the message: {token_count}")
            
            with open(args.output_file, "a") as f:
                f.write(
                    json.dumps(
                        {
                            "instance_id": d["instance_id"],
                            "num_tokens of the message" : token_count,
                            "message": message,
                            
                        }
                    )
                    + "\n"
                )
                    
        
            

def main():
    parser = argparse.ArgumentParser()
    
    parser.add_argument("--instance_id", type=str, required=True)
    parser.add_argument("--output_folder", type=str, required=True)
    parser.add_argument("--output_file", type=str, required=True)
    parser.add_argument("--full_text", action="store_true")
    parser.add_argument("--function_with_signature", action="store_true")
    parser.add_argument("--function_without_signature", action="store_true")
    parser.add_argument("--only_file_names", action="store_true")
    
    args = parser.parse_args()
    args.output_folder = os.path.join(args.instance_id, args.output_folder)
    args.output_folder = os.path.join("created_prompts_Verified", args.output_folder)
    
    args.output_file = os.path.join(args.output_folder, args.output_file)
    
    os.makedirs(args.output_folder, exist_ok=True)
    localize(args)


if __name__ == "__main__":
    main()
