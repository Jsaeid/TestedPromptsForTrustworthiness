import asyncio
from ollama import AsyncClient
import time
import requests
import re
import os
from pathlib import Path

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
        raise Exception(f"Failed to fetch file: {response.status_code}")
    
    # Split the file into lines and extract the required range
    content = response.text
    lines = content.splitlines()
    extracted_lines = lines[start_line - 1:end_line]  # Adjust for zero-based index
    
    return "\n".join(extracted_lines)


async def chat():  
    prompt1 = """
        Task: Function Ranking in Priority Groups

Context:
Software vulnerabilities are often discovered in production software, requiring development teams to modify the source code. These vulnerabilities typically reside in code units that are lengthy and complex. To proactively address potential issues, it is crucial to rank code units in priority groups during early development phases. This allows development teams to focus on the most problematic code units for analysis and improvement.

Objective:
Map the provided C function into one of the following priority groups based on its complexity and security risks:

Critical: The source code is hard to understand and highly likely to be faulty or vulnerable.
High: The source code has some complexity but can be understood after careful review.
Medium: The source code is understandable but could benefit from refactoring.
Low: The source code is easy to understand.
Lowest: The source code requires no maintenance changes.


Input:
this C function:
        
        """  
        
    prompt2 = """
    
Output Requirement:
Return only the priority group the function belongs to. Do not include any additional comments or explanations
    """
    
    message = {
        "role": "user",
        "content": "",
    }
    
    funcsArray = [
        "65. https://github.com/torvalds/linux/blob/946e51f2bf37f1656916eb75bd0742ba33983c28/fs/dcache.c,lines(1021-1124)",
        "66. https://github.com/torvalds/linux/blob/15fab63e1e57be9fdb5eec1bbc5916e9825e9acb/fs/splice.c,lines(1512-1626)",
        "67. https://github.com/torvalds/linux/blob/15fab63e1e57be9fdb5eec1bbc5916e9825e9acb/fs/fuse/dev.c,lines(2006-2088)",
        "68. https://github.com/torvalds/linux/blob/088aaf17aa79300cab14dbee2569c58cfafd7d6e/fs/cifs/smb2pdu.c,lines(3421-3494)",
        "69. https://github.com/torvalds/linux/blob/946e51f2bf37f1656916eb75bd0742ba33983c28/fs/dcache.c,lines(2483-2543)",
        "70. https://github.com/torvalds/linux/blob/946e51f2bf37f1656916eb75bd0742ba33983c28/fs/dcache.c,lines(1406-1463)",
        "71. https://github.com/torvalds/linux/blob/946e51f2bf37f1656916eb75bd0742ba33983c28/fs/dcache.c,lines(1762-1816)",
        "72. https://github.com/torvalds/linux/blob/6a3eb3360667170988f8a6477f6686242061488a/fs/cifs/smb2pdu.c,lines(3716-3792)",
        "73. https://github.com/torvalds/linux/blob/15fab63e1e57be9fdb5eec1bbc5916e9825e9acb/fs/splice.c,lines(1631-1708)",
        "10. https://github.com/torvalds/linux/blob/946e51f2bf37f1656916eb75bd0742ba33983c28/fs/dcache.c,lines(473-524)",
        "11. https://github.com/torvalds/linux/blob/088aaf17aa79300cab14dbee2569c58cfafd7d6e/fs/cifs/smb2pdu.c,lines(719-923)",
        "12. https://github.com/torvalds/linux/blob/daac07156b330b18eb5071aec4b3ddca1c377f2c/sound/usb/mixer.c,lines(1820-1987)",
        "13. https://github.com/torvalds/linux/blob/5369a762c882c0b6e9599e4ebbb3a9ba9eee7e2d/fs/ext4/xattr.c,lines(2309-2455)",
        "14. https://github.com/torvalds/linux/blob/088aaf17aa79300cab14dbee2569c58cfafd7d6e/fs/cifs/smb2pdu.c,lines(1576-1711)",
        "15. https://github.com/torvalds/linux/blob/36ae3c0a36b7456432fedce38ae2f7bd3e01a563/arch/x86/kvm/vmx.c,lines(3323-3450)",
        "16. https://github.com/torvalds/linux/blob/b3eaa9fc5cd0a4d74b18f6b8dc617aeaf1873270/kernel/futex.c,lines(746-863)",
        "17. https://github.com/torvalds/linux/blob/daac07156b330b18eb5071aec4b3ddca1c377f2c/sound/usb/mixer.c,lines(1028-1138)",
        "18. https://github.com/torvalds/linux/blob/088aaf17aa79300cab14dbee2569c58cfafd7d6e/fs/cifs/smb2pdu.c,lines(2572-2671)",
        "19. https://github.com/torvalds/linux/blob/9a47e9cff994f37f7f0dbd9ae23740d0f64f9fe6/sound/core/timer.c,lines(233-304)",
        "20. https://github.com/torvalds/linux/blob/cec8f96e49d9be372fdb0c3836dcf31ec71e457e/sound/core/timer.c,lines(309-369)",
        "21. https://github.com/torvalds/linux/blob/77260807d1170a8cf35dbb06e07461a655f67eee/fs/ext4/super.c,lines(2480-2620)",
        "22. https://github.com/torvalds/linux/blob/8605330aac5a5785630aec8f64378a54891937cc/net/core/skbuff.c,lines(2657-2773)",
        "23. https://github.com/torvalds/linux/blob/95d78c28b5a85bacbc29b8dba7c04babb9b0d467/block/bio.c,lines(1322-1443)",
        "24. https://github.com/torvalds/linux/blob/0f2ff82e11c86c05d051cae32b58226392d33bbf/drivers/gpu/drm/vc4/vc4_gem.c,lines(581-691)",
        "25. https://github.com/torvalds/linux/blob/a5ec6ae161d72f01411169a938fa5f8baea16e8f/kernel/bpf/verifier.c,lines(4297-4404)",
        "26. https://github.com/torvalds/linux/blob/77260807d1170a8cf35dbb06e07461a655f67eee/fs/ext4/super.c,lines(2344-2461)",
        "27. https://github.com/torvalds/linux/blob/15fab63e1e57be9fdb5eec1bbc5916e9825e9acb/mm/gup.c,lines(899-991)",
        "28. https://github.com/torvalds/linux/blob/36ae3c0a36b7456432fedce38ae2f7bd3e01a563/arch/x86/kvm/vmx.c,lines(9508-9599)",
        "29. https://github.com/torvalds/linux/blob/a5ec6ae161d72f01411169a938fa5f8baea16e8f/kernel/bpf/verifier.c,lines(2257-2344)",
        "30. https://github.com/torvalds/linux/blob/5ecb01cfdf96c5f465192bdb2a4fd4a61a24c6cc/kernel/futex.c,lines(507-594)",
        "31. https://github.com/torvalds/linux/blob/088aaf17aa79300cab14dbee2569c58cfafd7d6e/fs/cifs/smb2pdu.c,lines(3268-3349)",
        "32. https://github.com/torvalds/linux/blob/15fab63e1e57be9fdb5eec1bbc5916e9825e9acb/kernel/trace/trace.c,lines(7839-7917)",
        "33. https://github.com/torvalds/linux/blob/36ae3c0a36b7456432fedce38ae2f7bd3e01a563/arch/x86/kvm/vmx.c,lines(3150-3227)",
        "34. https://github.com/torvalds/linux/blob/36ae3c0a36b7456432fedce38ae2f7bd3e01a563/arch/x86/kvm/vmx.c,lines(6063-6139)",
        "35. https://github.com/torvalds/linux/blob/36ae3c0a36b7456432fedce38ae2f7bd3e01a563/arch/x86/kvm/vmx.c,lines(11692-11757)",
        "36. https://github.com/torvalds/linux/blob/15fab63e1e57be9fdb5eec1bbc5916e9825e9acb/kernel/trace/trace.c,lines(7919-7975)",
        "37. https://github.com/torvalds/linux/blob/95d78c28b5a85bacbc29b8dba7c04babb9b0d467/block/bio.c,lines(72-126)",
        "38. https://github.com/torvalds/linux/blob/e09463f220ca9a1a1ecfda84fcda658f99a1f12a/fs/ext4/xattr.c,lines(800-852)",
        "39. https://github.com/torvalds/linux/blob/677e806da4d916052585301785d847c3b3e6186a/net/xfrm/xfrm_user.c,lines(1003-1054)",
        "40. https://github.com/torvalds/linux/blob/15fab63e1e57be9fdb5eec1bbc5916e9825e9acb/fs/fuse/dev.c,lines(1420-1469)",
        "41. https://github.com/torvalds/linux/blob/6a3eb3360667170988f8a6477f6686242061488a/fs/cifs/smb2pdu.c,lines(3576-3708)",
        "42. https://github.com/torvalds/linux/blob/36ae3c0a36b7456432fedce38ae2f7bd3e01a563/arch/x86/kvm/vmx.c,lines(11089-11193)",
        "43. https://github.com/torvalds/linux/blob/6a3eb3360667170988f8a6477f6686242061488a/fs/cifs/smb2pdu.c,lines(3171-3266)",
        "44. https://github.com/torvalds/linux/blob/15fab63e1e57be9fdb5eec1bbc5916e9825e9acb/kernel/trace/trace.c,lines(5362-5457)",
        "45. https://github.com/torvalds/linux/blob/f070ef2ac66716357066b683fb0baf55f8191a2e/net/ipv4/tcp_output.c,lines(454-549)",
        "46. https://github.com/torvalds/linux/blob/8605330aac5a5785630aec8f64378a54891937cc/net/core/skbuff.c,lines(4839-4918)",
        "47. https://github.com/torvalds/linux/blob/daac07156b330b18eb5071aec4b3ddca1c377f2c/sound/usb/mixer.c,lines(3430-3504)",
        "48. https://github.com/torvalds/linux/blob/b3eaa9fc5cd0a4d74b18f6b8dc617aeaf1873270/kernel/futex.c,lines(2109-2181)",
        "49. https://github.com/torvalds/linux/blob/946e51f2bf37f1656916eb75bd0742ba33983c28/fs/dcache.c,lines(2007-2082)",
        "50. https://github.com/torvalds/linux/blob/f070ef2ac66716357066b683fb0baf55f8191a2e/net/ipv4/tcp_output.c,lines(587-654)",
        "51. https://github.com/torvalds/linux/blob/95d78c28b5a85bacbc29b8dba7c04babb9b0d467/block/bio.c,lines(652-717)",
        "52. https://github.com/torvalds/linux/blob/36ae3c0a36b7456432fedce38ae2f7bd3e01a563/arch/x86/kvm/vmx.c,lines(6397-6460)",
        "53. https://github.com/torvalds/linux/blob/daac07156b330b18eb5071aec4b3ddca1c377f2c/sound/usb/mixer.c,lines(330-393)",
        "54. https://github.com/torvalds/linux/blob/36ae3c0a36b7456432fedce38ae2f7bd3e01a563/arch/x86/kvm/vmx.c,lines(6141-6203)",
        "55. https://github.com/torvalds/linux/blob/77260807d1170a8cf35dbb06e07461a655f67eee/fs/ext4/super.c,lines(2805-2867)",
        "56. https://github.com/torvalds/linux/blob/15fab63e1e57be9fdb5eec1bbc5916e9825e9acb/mm/hugetlb.c,lines(1862-1921)",
        "57. https://github.com/torvalds/linux/blob/daac07156b330b18eb5071aec4b3ddca1c377f2c/sound/usb/mixer.c,lines(3239-3298)",
        "58. https://github.com/torvalds/linux/blob/946e51f2bf37f1656916eb75bd0742ba33983c28/fs/dcache.c,lines(871-927)",
        "59. https://github.com/torvalds/linux/blob/15fab63e1e57be9fdb5eec1bbc5916e9825e9acb/mm/gup.c,lines(523-579)",
        "60. https://github.com/torvalds/linux/blob/e09463f220ca9a1a1ecfda84fcda658f99a1f12a/fs/ext4/xattr.c,lines(1101-1155)",
        "61. https://github.com/torvalds/linux/blob/cec8f96e49d9be372fdb0c3836dcf31ec71e457e/sound/core/timer.c,lines(1574-1628)",
        "62. https://github.com/torvalds/linux/blob/36ae3c0a36b7456432fedce38ae2f7bd3e01a563/arch/x86/kvm/vmx.c,lines(10746-10798)",
        "63. https://github.com/torvalds/linux/blob/36ae3c0a36b7456432fedce38ae2f7bd3e01a563/arch/x86/kvm/vmx.c,lines(11017-11067)",
        "64. https://github.com/torvalds/linux/blob/36ae3c0a36b7456432fedce38ae2f7bd3e01a563/arch/x86/kvm/vmx.c,lines(3097-3147)",
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
        for funcUrl in reversed(funcsArray): 
            baseFolderName = "Results/AskLLMsAboutCodesWithWholeFunction/"
            # Check if the folder exists
            if not os.path.exists(baseFolderName + modelNames[i].replace(':', '_')):
                os.mkdir(baseFolderName + modelNames[i].replace(':', '_'))  # Create the folder   
            my_file = Path(baseFolderName + modelNames[i].replace(':', '_') + "/output_" + funcUrl[:2] + ".txt")
            if not my_file.is_file():
                (url, stLn, endLn) = (parse_github_link(funcUrl[4:]))            
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

                    f = open(baseFolderName + modelNames[i].replace(':', '_') + "/output_" + funcUrl[:2] + ".txt", "w")
                    res = response['message']['content']
                    print(res)
                    f.write(res)            
                    f.write("\n\n\n--- %s seconds ---" % (time.time() - start_time))   
                    f.flush()
                    f.close()    
                except Exception as ex:
                    print(ex)
                    f = open(baseFolderName + modelNames[i].replace(':', '_') + "/output_" + fuuncUrl[:2] + ".txt", "w")
                    f.write(f"{ex}\n")            
                    f.write("\n\n\n--- %s seconds ---" % (time.time() - start_time))   
                    f.flush()
                    f.close() 

asyncio.run(chat())
