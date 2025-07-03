
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
        Task: Function Ranking in Priority Groups

Context:
Software vulnerabilities are often discovered in production software, requiring development teams to modify the source code.
These vulnerabilities typically reside in code units that are lengthy and complex. 
To proactively address potential issues, it is crucial to rank code units in priority groups during early development phases. 
This allows development teams to focus on the most problematic code units for analysis and improvement.
The main Software Metrics are:
1. Complexity: indicate how complex the code unit is, e.g. cyclomatic complexity
2. Volume: characterize the size of the code unit, e.g. lines of code
3. Coupling: indicate how coupled or not the code unit is with other units, e.g. coupling between objects
4. Cohesion: characterize how cohesive or not the code unit is, e.g. lack of cohesion

Objective:
Based on the Software Metrics, Map the provided C function into one of the following priority groups based on its complexity and security risks:
1. Critical: the source code is hard to understand and likely to be faulty or vulnerable.
2. High: the source code has some complexity, but it can be understood after reading it a couple of times.
3. Medium: the source code can be understood well, but it would benefit from some refactoring.
4. Low: the source code is easy to understand.
5. Lowest: the source code does not need any maintenance change.

Input:
this C function:
        
        """  
        
    prompt2 = """
    
Output Requirement:
Return only the priority group the function belongs to. Do not include any additional comments or explanations in xml format or json
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
        "J. https://github.com/joseadp/linux/blob/daac07156b330b18eb5071aec4b3ddca1c377f2c/sound/usb/mixer.c, lines(1028-1138)"
        ]
    
    modelNames = [    
        "deepseek-coder-v2",    
        "deepseek-r1:32b",    
        "falcon3:10b",
        "granite3.1-dense",
        "marco-o1",
        "qwen2.5-coder:32b",                    
        "phi4",               
        "codellama:34b",    
        "gemma2:27b",                   
        "granite-code:34b",              
        "codegeex4",                  
        "codestral",                              
        "mixtral:8x7b",    
        "command-r",                   
        "starcoder:15b",    
        "qwq",               
        "starcoder2:15b",     
    ]  

    for i in range(len(modelNames)):  
        for funcUrl in reversed(funcsArray): 
            baseFolderName = "Results/AskLLMsAboutCodesWithAddedInfo/"
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
                    response = await AsyncClient().chat(model=modelNames[i], messages=[message], options={"temperature":0.0, "num_ctx":4096}) 

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