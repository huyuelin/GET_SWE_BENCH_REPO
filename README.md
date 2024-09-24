# SWE-Bench Prompt Generation Script
该项目旨在通过分析 GitHub 仓库的项目结构和问题描述，生成用于修复问题的文件路径和函数位置的 prompts。

## 安装依赖
环境参考requirements.txt

```bash
pip install -r requirements.txt  
```

## 参数解析
### 必要参数

--instance_id (str): 输入你想要生成 prompt 的实例 ID
--only_file_names: 仅生成需要编辑的文件名列表。
--function_without_signature: 生成文件名及其相应的函数名列表。
--function_with_signature: 生成文件名、函数名及其数据依赖列表。
--full_text: 基于完整的仓库结构生成更详细的 prompts，包括类名、函数名和精确的行号。

### 输出文件

--output_folder (str): 指定保存生成 prompt 的文件夹路径。
--output_file (str): 指定保存生成 prompt 的文件名。


## 目前使用的instances_id

我现在使用的instances_id如下所示：
SWE-Bench_Lite:
[
    "astropy__astropy-12907",
    "django__django-11001",
    "matplotlib__matplotlib-22711",
]


SWE-Bench_Verified:
[
    "astropy__astropy-12907",
    "django__django-10097",
    "matplotlib__matplotlib-13989",
    "mwaskom__seaborn-3069",
    "pallets__flask-5014",
    
    "pydata__xarray-2905",
    
    "pytest-dev__pytest-10051",
    "scikit-learn__scikit-learn-10297",
    
    "sympy__sympy-11618",
]

"psf__requests-1142" "pylint-dev__pylint-4551" "sphinx-doc__sphinx-10323"暂时加不了data dependencies

## 使用示例
假设你想要为 astropy__astropy-12907 生成只包含文件名的 prompt，且输出保存在 created_prompts/astropy__astropy-12907/only_file_name/only_file_name.jsonl 中，你可以运行以下命令：

```bash
python main.py --instance_id astropy_astropy-12907 --output_folder only_file_name --output_file only_file_name.json --only_file_names
```


可以查看.vscode/launch.json以获知具体使用参数和方法。



## GROUND TRUTH LOCALIZATION
位于ground_truth_localization_Lite.txt和ground_truth_localization_Verified.txt