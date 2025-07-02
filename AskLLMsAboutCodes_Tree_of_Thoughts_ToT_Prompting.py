
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
To help develop such a technique, we kindly ask you to categorize a C function into priority groups based on security risks, complexity, and maintainability using a Tree-of-Thoughts (ToT) reasoning framework.
The priority groups (from a security perspective) are:
    • Critical (P5): The source code is hard to understand and likely to be faulty or vulnerable.
    • High (P4): The source code has some complexity, but it can be understood after reading it a couple of times.
    • Medium (P3): The source code can be understood well, but it would benefit from some refactoring.
    • Low (P2): The source code is easy to understand.
    • Lowest (P1): The source code does not need any maintenance change.

Step 1: Tree-Based Multi-Perspective Analysis
ToT follows a tree-based decision-making process, where we evaluate the function from three different perspectives (security, complexity, maintainability) independently before merging results for a final decision.
Each branch expands into sub-branches for deeper analysis:

Branch 1: Security Risk Analysis (SSS)
    1. Does the function handle user input? 
        ◦ Yes → Check for input validation flaws.
        ◦ No → Move to memory safety analysis.
    2. Does the function manipulate memory directly (e.g., pointers, buffers, malloc/free)? 
        ◦ Yes → Check for potential leaks or overflows.
        ◦ No → Assign low security risk.
    3. Does the function perform critical operations (e.g., authentication, encryption)? 
        ◦ Yes → Prioritize high scrutiny.
        ◦ No → Lower risk category.

Branch 2: Code Complexity Analysis (CCC)
    1. Is the function deeply nested or recursive? 
        ◦ Yes → Higher complexity.
        ◦ No → Proceed to loop structure evaluation.
    2. Are there multiple conditional statements affecting readability? 
        ◦ Yes → Higher complexity.
        ◦ No → Proceed to function length evaluation.
    3. Is the function longer than 30 lines? 
        ◦ Yes → Likely harder to maintain.
        ◦ No → Assign lower complexity.

Branch 3: Maintainability Analysis (MMM)
    1. Are variable names and comments clear? 
        ◦ Yes → Assign good maintainability.
        ◦ No → Increase maintainability concerns.
    2. Does the function contain redundant logic? 
        ◦ Yes → Assign medium or high maintainability concerns.
        ◦ No → Proceed to modularity check.
    3. Is the function modular (reusable components, minimal side effects)? 
        ◦ Yes → Lower maintainability risk.
        ◦ No → Higher maintainability risk.

Step 2: Merging Thought Paths for Final Ranking
Once the analysis tree is constructed, we aggregate the results to compute the function's priority score:

P = ((S*0.5) + (C*0.3) + (M*0.2)) / 3

where:
    • Security Risk (S) contributes 50% to the final ranking.
    • Complexity (C) contributes 30%.
    • Maintainability (M) contributes 20%.
The priority classification is determined as follows:
P ≥ 2.5  ​⇒ P5 (Critical)
2.0 ≤ P < 2.5  ⇒ P4 (High)
1.5 ≤ P < 2.0   ⇒ P3 (Medium)
1.0 ≤ P < 1.5   ⇒ P2 (Low)
P < 1.0 ⇒ P1 (Lowest)

Step 3: Example Evaluations Using ToT
Example 1:
void processData(char *input) {
    char buffer[50];
    strcpy(buffer, input);  // Potential buffer overflow
    printf("Processed: %s\n", buffer);
}
Branch 1: Security Analysis
✅ Uses direct memory operations (buffer) → High Risk (S = 3)
✅ No input validation → Very High Risk
Branch 2: Complexity Analysis
✅ Simple logic → Low Complexity (C = 1)
Branch 3: Maintainability Analysis
✅ Needs refactoring due to unsafe practices → High Maintainability Concern (M = 3)
Final Score Calculation:

P = ((3*0.5) + (1*0.3) + (3*0.2)) /3 = 2.4

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
Branch 1: Security Analysis
✅ No risky operations → Low Risk (S = 1)
Branch 2: Complexity Analysis
✅ Nested conditionals → Moderate Complexity (C = 2)
Branch 3: Maintainability Analysis
✅ Could be refactored → Moderate Maintainability Concern (M = 2)
Final Score Calculation:

P = ((1*0.5) + (2*0.3) + (2*0.2)) / 3 = 1.5

Conclusion: P3 (Medium Priority)

Step 4: Apply ToT to a New Function
Here is the function under analysis:

        """  
        
    prompt2 = """
    
Tree-Based Evaluation:
    • Branch 1 (Security Risk S) → (Analyze function)
    • Branch 2 (Complexity C) → (Analyze function)
    • Branch 3 (Maintainability M) → (Analyze function)

P = ((S*0.5) + (C*0.3) + (M*0.2)) / 3

Classification: The function falls into [Final Priority Group].
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
            baseFolderName = "Results/AskLLMsAboutCodes_Tree_of_Thoughts_ToT_Prompting/"
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