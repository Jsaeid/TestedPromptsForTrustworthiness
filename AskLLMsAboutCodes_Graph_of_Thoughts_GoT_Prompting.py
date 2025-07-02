
import asyncio
from ollama import AsyncClient # type: ignore
import time
import requests
import re
import os
from pathlib import Path

# from ollama import chat
# from ollama import ChatResponse

# from ollama import Client

def parse_github_link(input_string):
    # Regular expression to extract URL and line numbers
    pattern = r"(https://github\.com/[^\s,]+),\s*lines\((\d+)-(\d+)\)"
    match = re.match(pattern, input_string)
    if not match:
        raise ValueError("Invalid input format")
    
    url = match.group(1)
    start_line = int(match.group(2))
    end_line = int(match.group(3))
    
    return url, start_line, end_line


def get_code_from_github(url, start_line, end_line):
    # Extract the raw URL for the file content
    parts = url.split("/blob/")
    if len(parts) != 2:
        raise ValueError("Invalid GitHub URL format")
    
    raw_url = parts[0].replace("https://github.com", "https://raw.githubusercontent.com") + "/" + parts[1].replace("/blob", "")
    print(raw_url) 
    # Fetch the file content
    response = requests.get(raw_url)
    
    if response.status_code != 200:
        response = requests.get(raw_url)    
        if response.status_code != 200:
            response = requests.get(raw_url)    
            if response.status_code != 200:
                response = requests.get(raw_url)
    
    # Split the file into lines and extract the required range
    content = response.text
    lines = content.splitlines()
    extracted_lines = lines[start_line - 1:end_line]  # Adjust for zero-based index
    
    return "\n".join(extracted_lines)


async def chat():  
    prompt1 = """
Function Ranking in Priority Groups
Software vulnerabilities are frequently identified in software that is already in production. Consequently, software development teams must make changes in the source code to fix those vulnerabilities, which are usually present in code units that are lengthy and complex.
Therefore, we need more than just vulnerability detection to identify the most (potentially) problematic code units in the early phases of development so that the software development team can analyze them.
To help develop such a technique, we kindly ask you to categorize a C function into priority groups based on security risks, complexity, maintainability, and performance trade-offs using a Graph-of-Thoughts (GoT) reasoning framework.
The priority groups (from a security perspective) are:
    • Critical (P5): The source code is hard to understand and likely to be faulty or vulnerable.
    • High (P4): The source code has some complexity, but it can be understood after reading it a couple of times.
    • Medium (P3): The source code can be understood well, but it would benefit from some refactoring.
    • Low (P2): The source code is easy to understand.
    • Lowest (P1): The source code does not need any maintenance change.

Step 1: Building the Thought Graph
Instead of analyzing each aspect independently, we create a graph where reasoning nodes are interconnected, forming dependencies between different factors.
Graph Structure & Thought Nodes
    • Security Risk (S)
        ◦ Does the function handle user input?
        ◦ Does it perform memory operations (pointers, buffers)?
        ◦ Does it involve authentication or encryption?
    • Code Complexity (C)
        ◦ How many nested loops or conditions does it have?
        ◦ Does it use recursion?
        ◦ How lengthy is the function?
    • Maintainability (M)
        ◦ Are variable names and comments clear?
        ◦ Is there redundant logic?
        ◦ Is the function modular and reusable?
    • Performance Efficiency (P)
        ◦ Does the function have high time complexity?
        ◦ Does it use excessive memory?
        ◦ Is there unnecessary computation?
Graph-Based Dependencies
    • Security risk (S) influences maintainability (M) 
        ◦ If a function has high security risk, it may require frequent updates → Higher maintainability burden.
    • Code complexity (C) affects security risk (S) 
        ◦ If a function is highly complex, it increases the chance of vulnerabilities.
    • Performance efficiency (P) affects maintainability (M) 
        ◦ If a function is optimized for speed but difficult to understand, it may reduce maintainability.

Step 2: Graph Reasoning for Function Evaluation
For each function, construct a graph traversal process where each factor influences the others.
Graph Traversal Algorithm
    1. Initialize graph nodes S, C, M, P.
    2. Evaluate each node independently using logical steps.
    3. Propagate effects to dependent nodes (e.g., if complexity is high, adjust security risk score).
    4. Aggregate final score using weighted dependencies:

P = ((S*0.4) + (C*0.3) + (M*0.2) + (P*0.1)) / 4

where:
    • Security risk (S) contributes 40%.
    • Complexity (C) contributes 30%.
    • Maintainability (M) contributes 20%.
    • Performance (P) contributes 10%.
Priority Assignment:
P ≥ 2.5  ​⇒ P5 (Critical)
2.0 ≤ P < 2.5  ⇒ P4 (High)
1.5 ≤ P < 2.0   ⇒ P3 (Medium)
1.0 ≤ P < 1.5   ⇒ P2 (Low)
P < 1.0  ⇒ P1 (Lowest) 
Step 3: Example Evaluations Using GoT

Example 1:
void processData(char *input) {
    char buffer[50];
    strcpy(buffer, input);  // Potential buffer overflow
    printf("Processed: %s\n", buffer);
}
Graph Evaluation
    • Security Risk (S = 3) → Uses buffer, lacks validation.
    • Complexity (C = 1) → Simple function.
    • Maintainability (M = 3) → Unsafe practice requires refactoring.
    • Performance (P = 2) → Simple, but could be optimized with safer alternatives.
Final Score Calculation:

P = ((3*0.4) + (1*0.3) + (3*0.2) + (2*0.1)) / 4 = 2.3

Conclusion: P4 (High Priority)

Example 2:
int compute(int a, int b) {
    if (a > 10) {
        if (b > 20) {
            return a * b;
        } else {
            return a + b;
        }
    } else {
        return a - b;
    }
}
Graph Evaluation
    • Security Risk (S = 1) → No risky operations.
    • Complexity (C = 2) → Nested conditionals, moderate complexity.
    • Maintainability (M = 2) → Could be refactored.
    • Performance (P = 3) → Simple but can be optimized.
Final Score Calculation:

P = ((1*0.4) + (2*0.3) + (2*0.2) + (3*0.1)) / 4 = 1.7

Conclusion: P3 (Medium Priority)

Step 4: Apply GoT to a New Function
Here is the function under analysis:

    """
        
    prompt2 = """
    
Graph-Based Evaluation:
    • Security Risk (S) → (Analyze function)
    • Code Complexity (C) → (Analyze function)
    • Maintainability (M) → (Analyze function)
    • Performance Efficiency (P) → (Analyze function)
    
P = ((S*0.4) + (C*0.3) + (M*0.2) + (P*0.1)) / 4

Conclusion: The function falls into [Final Priority Group].
    """


    message = {
        "role": "user",
        "content": "",
    }
    
    funcsArray = [
        "A. https://github.com/joseadp/linux/blob/327eaf738ff97d19491362e30497954105d60414/fs/ext4/xattr.c, lines(1558-1795)",
        "B. https://github.com/joseadp/linux/blob/618d919cae2fcaadc752f27ddac8b939da8b441a/fs/cifs/smb2pdu.c, lines(3717-3792)",
        "C. https://github.com/joseadp/linux/blob/242658ff99ab9d87e704475ef78c3102ead344cf/sound/core/timer.c, lines(1660-1760)",
        "D. https://github.com/joseadp/linux/blob/8fde12ca79aff9b5ba951fce1a2641901b8d8e64/fs/fuse/dev.c, lines(2006-2088)",
        "E. https://github.com/joseadp/linux/blob/8fde12ca79aff9b5ba951fce1a2641901b8d8e64/fs/splice.c, lines(1512-1622)",
        "F. https://github.com/joseadp/linux/blob/5369a762c882c0b6e9599e4ebbb3a9ba9eee7e2d/fs/ext4/xattr.c, lines(2309-2455)",
        "G. https://github.com/joseadp/linux/blob/8605330aac5a5785630aec8f64378a54891937cc/net/core/skbuff.c, lines(3597-3687)",
        "H. https://github.com/joseadp/linux/blob/946e51f2bf37f1656916eb75bd0742ba33983c28/fs/dcache.c, lines(871-927)",
        "I. https://github.com/joseadp/linux/blob/daac07156b330b18eb5071aec4b3ddca1c377f2c/sound/usb/mixer.c, lines(1820-1987)",
        "J. https://github.com/joseadp/linux/blob/daac07156b330b18eb5071aec4b3ddca1c377f2c/sound/usb/mixer.c, lines(1028-1138)",
        "K. https://github.com/joseadp/linux/blob/36ae3c0a36b7456432fedce38ae2f7bd3e01a563/arch/x86/kvm/vmx.c, lines(6063-6139)",
        "L. https://github.com/joseadp/linux/blob/088aaf17aa79300cab14dbee2569c58cfafd7d6e/fs/cifs/smb2pdu.c, lines(3268-3349)",
        "M. https://github.com/joseadp/linux/blob/946e51f2bf37f1656916eb75bd0742ba33983c28/fs/dcache.c, lines(1021-1124)",
        "N. https://github.com/joseadp/linux/blob/15fab63e1e57be9fdb5eec1bbc5916e9825e9acb/mm/hugetlb.c, lines(1862-1921)",
        "O. https://github.com/joseadp/linux/blob/daac07156b330b18eb5071aec4b3ddca1c377f2c/sound/usb/mixer.c, lines(330-393)",
        "P. https://github.com/joseadp/linux/blob/15fab63e1e57be9fdb5eec1bbc5916e9825e9acb/fs/fuse/dev.c, lines(2006-2088)",
        "Q. https://github.com/joseadp/linux/blob/946e51f2bf37f1656916eb75bd0742ba33983c28/fs/dcache.c, lines(1406-1463)",
        "R. https://github.com/joseadp/linux/blob/cec8f96e49d9be372fdb0c3836dcf31ec71e457e/sound/core/timer.c, lines(1574-1628)",
        "S. https://github.com/joseadp/linux/blob/b3eaa9fc5cd0a4d74b18f6b8dc617aeaf1873270/kernel/futex.c, lines(2109-2181)",
        "T. https://github.com/joseadp/linux/blob/36ae3c0a36b7456432fedce38ae2f7bd3e01a563/arch/x86/kvm/vmx.c, lines(11692-11757)",
        "U. https://github.com/joseadp/linux/blob/0f2ff82e11c86c05d051cae32b58226392d33bbf/drivers/gpu/drm/vc4/vc4_gem.c, lines(581-691)",
        "V. https://github.com/joseadp/linux/blob/36ae3c0a36b7456432fedce38ae2f7bd3e01a563/arch/x86/kvm/vmx.c, lines(3323-3450)",
        "W. https://github.com/joseadp/linux/blob/946e51f2bf37f1656916eb75bd0742ba33983c28/fs/dcache.c, lines(473-524)",
        "X. https://github.com/joseadp/linux/blob/15fab63e1e57be9fdb5eec1bbc5916e9825e9acb/kernel/trace/trace.c, lines(7919-7975)",
        "Y. https://github.com/joseadp/linux/blob/15fab63e1e57be9fdb5eec1bbc5916e9825e9acb/kernel/trace/trace.c, lines(5362-5457)",
        "Z. https://github.com/joseadp/linux/blob/15fab63e1e57be9fdb5eec1bbc5916e9825e9acb/fs/splice.c, lines(1631-1708)",
        ] 
    
    modelNames = [    
        "granite3.1-dense",
        "qwen2.5-coder:32b",  
        "gemma2:27b",  
        "deepseek-r1:32b",                 
        "codegeex4",                   
        "codestral",                      
        "mixtral:8x7b",  
        # "deepseek-coder-v2",               
        # "granite-code:34b",                  
        # "phi4",            
        # "qwq",       
    ]    

    for i in range(len(modelNames)):  
        for funcUrl in funcsArray: 
            baseFolderName = "Results/AskLLMsAboutCodes_Graph_of_Thoughts_GoT_Prompting/"
            # Check if the folder exists
            if not os.path.exists(baseFolderName + modelNames[i].replace(':', '_')):
                os.mkdir(baseFolderName + modelNames[i].replace(':', '_'))  # Create the folder   
            my_file = Path(baseFolderName + modelNames[i].replace(':', '_') + "/output_" + funcUrl[0] + ".txt")
            if not my_file.is_file():
                (url, stLn, endLn) = (parse_github_link(funcUrl[3:]))            
                message["content"] = prompt1     
                message["content"] = message["content"] + get_code_from_github(url, stLn, endLn)  + "\n"
                # message["content"] = message["content"] + funcUrl[3:]  + "\n"
                # message["content"] = message["content"] + funcUrl[0] + "\n"
                message["content"] = message["content"] + prompt2 
                # print (message["content"])

                print(baseFolderName)
                print(modelNames[i])
                print(funcUrl)

                start_time = time.time()    

                try:    
                    response = await AsyncClient().chat(model=modelNames[i], messages=[message], options={"temperature":0.0, "num_ctx":6154}) 

                    f = open(baseFolderName + modelNames[i].replace(':', '_') + "/output_" + funcUrl[0] + ".txt", "w")
                    res = response['message']['content']
                    print(res)
                    f.write(res)            
                    f.write("\n\n\n--- %s seconds ---" % (time.time() - start_time))   
                    f.flush()
                    f.close()   
                except Exception as ex:
                    print(ex)
                    f = open(baseFolderName + modelNames[i].replace(':', '_') + "/output_" + funcUrl[0] + ".txt", "w")
                    f.write(f"{ex}\n")            
                    f.write("\n\n\n--- %s seconds ---" % (time.time() - start_time))   
                    f.flush()
                    f.close() 


asyncio.run(chat())