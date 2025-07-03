
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
To help develop such a technique, we kindly ask you to categorize a C function into priority groups based on its security and complexity. The priority groups (from a security perspective) are the following:
    • Critical: The source code is hard to understand and likely to be faulty or vulnerable.
    • High: The source code has some complexity, but it can be understood after reading it a couple of times.
    • Medium: The source code can be understood well, but it would benefit from some refactoring.
    • Low: The source code is easy to understand.
    • Lowest: The source code does not need any maintenance change.

Step 1: Generate Multiple Independent Reasoning Paths
For each function, evaluate it multiple times using different reasoning paths, and cross-check the consistency of the conclusions.

Example Function:
void processData(char *input) {
    char buffer[50];
    strcpy(buffer, input);  // Potential buffer overflow
    printf("Processed: %s\n", buffer);
}

Reasoning Path 1 (Security-Centric Approach):
    • Uses strcpy without bounds checking → Buffer Overflow Risk
    • If exploited, could lead to arbitrary code execution
    • Conclusion: Critical

Reasoning Path 2 (Complexity-Based Approach):
    • Function is short and simple, easy to read
    • No nested conditionals or loops, straightforward logic
    • Conclusion: Low or Medium

Reasoning Path 3 (Maintainability Perspective):
    • Easy to read but unsafe and requires modification
    • Should use strncpy or input validation to fix vulnerability
    • Conclusion: Critical or High
    
Final Decision Using Self-Consistency:
    • Most paths agree that the function has critical security risks, even though it's simple.
    • Since security risks outweigh readability, the most consistent conclusion is: Critical.

Step 2: Apply Self-Consistency to a New Function
Now, analyze the following function by evaluating multiple independent reasoning paths:

        """  
        
    prompt2 = """
    
Reasoning Path 1 (Security):
(Analyze security risks)
Reasoning Path 2 (Complexity):
(Analyze function structure and readability)
Reasoning Path 3 (Maintainability):
(Evaluate whether the function needs refactoring)
Final Decision (Majority-Based Conclusion):
The most consistent ranking across different reasoning paths is: [Final Priority Group].
    """
    
    message = {
        "role": "user",
        "content": "",
    }
    
    funcsArray = [
        "A. https://github.com/torvalds/linux/blob/327eaf738ff97d19491362e30497954105d60414/fs/ext4/xattr.c, lines(1558-1795)",
        "B. https://github.com/torvalds/linux/blob/618d919cae2fcaadc752f27ddac8b939da8b441a/fs/cifs/smb2pdu.c, lines(3717-3792)",
        "C. https://github.com/torvalds/linux/blob/242658ff99ab9d87e704475ef78c3102ead344cf/sound/core/timer.c, lines(1660-1760)",
        "D. https://github.com/torvalds/linux/blob/8fde12ca79aff9b5ba951fce1a2641901b8d8e64/fs/fuse/dev.c, lines(2006-2088)",
        "E. https://github.com/torvalds/linux/blob/8fde12ca79aff9b5ba951fce1a2641901b8d8e64/fs/splice.c, lines(1512-1622)",
        "F. https://github.com/torvalds/linux/blob/5369a762c882c0b6e9599e4ebbb3a9ba9eee7e2d/fs/ext4/xattr.c, lines(2309-2455)",
        "G. https://github.com/torvalds/linux/blob/8605330aac5a5785630aec8f64378a54891937cc/net/core/skbuff.c, lines(3597-3687)",
        "H. https://github.com/torvalds/linux/blob/946e51f2bf37f1656916eb75bd0742ba33983c28/fs/dcache.c, lines(871-927)",
        "I. https://github.com/torvalds/linux/blob/daac07156b330b18eb5071aec4b3ddca1c377f2c/sound/usb/mixer.c, lines(1820-1987)",
        "J. https://github.com/torvalds/linux/blob/daac07156b330b18eb5071aec4b3ddca1c377f2c/sound/usb/mixer.c, lines(1028-1138)"
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
            baseFolderName = "Results/AskLLMsAboutCodes_Self_Consistency_Prompting/"
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
