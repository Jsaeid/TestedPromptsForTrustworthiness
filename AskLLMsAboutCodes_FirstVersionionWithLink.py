import asyncio
from ollama import AsyncClient
import time
import os
from pathlib import Path

async def chat():  
    prompt1 = """
        Function Ranking in Priority Groups.
        
        Some software codes are prone to probable attacks.
                
        These are the priority groups (from a security perspective):
        1. Critical: the source code is hard to understand and likely to be faulty or vulnerable.
        2. High: the source code has some complexity, but it can be understood after reading it a couple of times.
        3. Medium: the source code can be understood well, but it would benefit from some refactoring.
        4. Low: the source code is easy to understand.
        5. Lowest: the source code does not need any maintenance change.
                
        I want you to map the following function to one of the above priority groups. This is the function:
        
        """  
        
    prompt2 = """
        your answer should be just one word (the name of the priority group that the function belongs to)
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
        "deepseek-coder-v2",    
        "starcoder2:15b",     
    ]
    
    for i in range(len(modelNames)):  
        for funcUrl in reversed(funcsArray): 
            baseFolderName = "Results/AskLLMsAboutCodes_FirstVersionionWithLink/"
            # Check if the folder exists
            if not os.path.exists(baseFolderName + modelNames[i].replace(':', '_')):
                os.mkdir(baseFolderName + modelNames[i].replace(':', '_'))  # Create the folder   
            my_file = Path(baseFolderName + modelNames[i].replace(':', '_') + "/output_" + funcUrl[0] + ".txt")
            if not my_file.is_file():          
                message["content"] = prompt1     
                message["content"] = message["content"] + funcUrl[3:]  + "\n"
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