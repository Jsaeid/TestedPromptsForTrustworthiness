
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
To help develop such a technique, we kindly ask you to rank a given C function into priority groups based on security, complexity, maintainability, and performance considerations using a System 2 Attention (S2A) reasoning framework.
The priority groups (from a security perspective) are:
    • Critical (P5): The source code is hard to understand and likely to be faulty or vulnerable.
    • High (P4): The source code has some complexity, but it can be understood after reading it a couple of times.
    • Medium (P3): The source code can be understood well, but it would benefit from some refactoring.
    • Low (P2): The source code is easy to understand.
    • Lowest (P1): The source code does not need any maintenance change.

Step 1: Focused Attention on Key Evaluation Criteria
Before making a decision, carefully analyze the function based on four fundamental dimensions:
1️⃣ Security Risk (S)
    • Does the function involve unsafe operations (e.g., raw pointers, buffer manipulation, memory allocation)?
    • Does it handle user input securely (e.g., input validation, buffer overflow risks)?
    • Does it involve authentication or cryptographic operations that may be vulnerable?
2️⃣ Code Complexity (C)
    • Does the function contain deeply nested logic, loops, or recursion?
    • Are the data structures used efficient and understandable?
    • Is the function long and difficult to follow?
3️⃣ Maintainability (M)
    • Are variable names, comments, and structure clear and self-explanatory?
    • Could the function benefit from modularization or refactoring?
    • Does it have hardcoded values or magic numbers that reduce maintainability?
4️⃣ Performance Efficiency (P)
    • Is the function optimally designed for speed and memory usage?
    • Does it have redundant operations or inefficient loops?
    • Are there unnecessary function calls that increase execution time?

Step 2: Thoughtful Step-by-Step Evaluation (System 2 Thinking)
Step 2.1: Carefully examine the function. Identify potential security risks, complexity issues, maintainability concerns, and performance trade-offs.
Step 2.2: Reflect on how these factors interact. Consider trade-offs (e.g., high security might increase complexity, good maintainability might reduce performance).
Step 2.3: Assign a quantitative score (1 to 5) for each criterion, ensuring deliberate reasoning.
S=Security Risk Score (1-5)
C=Code Complexity Score (1-5)
M=Maintainability Score (1-5)
P=Performance Efficiency Score (1-5)
 
Step 2.4: Compute an overall priority score based on weighted importance. Security and complexity should have more influence than performance and maintainability:

P = ((S*0.4) + (C*0.3) + (M*0.2) + (P*0.1)) / 4

Step 2.5: Reflect on the final ranking and verify consistency. If the ranking seems incorrect, go back and refine the reasoning process.

Step 3: Apply S2A to Example Functions
Example 1: High-Risk Function
void processData(char *input) {
    char buffer[50];
    strcpy(buffer, input);  // Potential buffer overflow
    printf("Processed: %s\n", buffer);
}
Step-by-Step S2A Analysis
    • Security Risk (S = 5/5) → Uses strcpy without bounds checking → high buffer overflow risk.
    • Code Complexity (C = 1/5) → Simple function.
    • Maintainability (M = 4/5) → Requires urgent fixing (should use strncpy or safer alternatives).
    • Performance (P = 2/5) → No significant impact on performance.
Final Score Calculation 

P = ((5*0.4) + (1*0.3) + (4*0.2) + (4*0.1)) / 4 = 3.2

CConclusion: P5 (Critical Priority)

Example 2: Maintainable, Medium Complexity Function
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
Step-by-Step S2A Analysis
    • Security Risk (S = 1/5) → No user input, no memory operations.
    • Code Complexity (C = 3/5) → Nested conditionals add some complexity.
    • Maintainability (M = 3/5) → Could be refactored but is understandable.
    • Performance (P = 3/5) → Simple computations, no inefficiencies.
Final Score Calculation

P = ((1*0.4) + (3*0.3) + (3*0.2) + (3*0.1)) / 4 = 2.2

Conclusion: P3 (Medium Priority)

Step 4: Apply S2A to a New Function
Here is the function under analysis:

    """
        
    prompt2 = """
    
Analyze the function using the same S2A reasoning process and derive a final ranking.
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
            baseFolderName = "Results/AskLLMsAboutCodes_System2Attention_S2A_Prompting/"
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