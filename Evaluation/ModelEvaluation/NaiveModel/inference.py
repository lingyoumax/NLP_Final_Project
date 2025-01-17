import sys
from pathlib import Path

# 获取当前文件的路径
current_file_path = Path(__file__).parent.absolute()

# 将当前文件的路径添加到 sys.path 中
if str(current_file_path) not in sys.path:
    sys.path.append(str(current_file_path))

from transformers import BitsAndBytesConfig,GenerationConfig,AutoModelForCausalLM,AutoTokenizer
import torch
from tqdm import tqdm
from utils.qwen_generation_utils import make_context, decode_tokens, get_stop_words_ids
import random
import gc

def inference(instructions,model_name="qwen/Qwen-7B-Chat",adapter=None,response_num=1,batch_size=4,
              temperature=None,top_p=None,repetition_penalty=1.1,top_k=None,
              max_new_tokens=128,):
    bnb_config=BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
            llm_int8_threshold=6.0,
            llm_int8_has_fp16_weight=False,
        )
    print("SFT inference, inferecnt {} samples".format(len(instructions)))
    
    tokenizer= AutoTokenizer.from_pretrained(
            model_name,
            pad_token='<|extra_0|>',
            eos_token='<|endoftext|>',
            padding_side='left',
            trust_remote_code=True
            )
    model = AutoModelForCausalLM.from_pretrained(model_name, pad_token_id=tokenizer.pad_token_id,trust_remote_code=True, quantization_config=bnb_config, device_map="auto").eval()
    model.generation_config = GenerationConfig.from_pretrained(model_name, pad_token_id=tokenizer.pad_token_id)
    model.generation_config.max_new_tokens=max_new_tokens
    model.generation_config.repetition_penalty=repetition_penalty
    print("initial model")
    if adapter is not None:
        model.load_adapter(adapter)
        print("initial adapter")
    
    result_instructions=[]
    for index in tqdm(range(0,len(instructions),batch_size)):
        start=index
        end=min(index+batch_size,len(instructions))

        batch_raw_text = []
        for j in range(start,end):
            prompt="Based on content:\n"+ instructions[j]["instruction"]+"\n"+"Answer Question:\n" + instructions[j]["input"]
            raw_text, _ = make_context(
            tokenizer,
            prompt,
            system="Now you are a question answering assistant.",
            max_window_size=model.generation_config.max_window_size,
            chat_format=model.generation_config.chat_format,
            )
            batch_raw_text.append(raw_text)
        
        batch_input_ids = tokenizer(batch_raw_text, padding='longest')
        batch_input_ids = torch.LongTensor(batch_input_ids['input_ids']).to(model.device)
        for i in range(response_num):
            if top_p is None:
                if i==0:
                    model.generation_config.top_p=0.2
                else:
                    model.generation_config.top_p=random.uniform(0.1,0.7)
            else:
                model.generation_config.top_p=top_p
            if temperature is None:
                if i==0:
                    model.generation_config.temperature=0.7
                else:
                    model.generation_config.temperature=random.uniform(0.2,0.95)
            else:
                model.generation_config.temperature=temperature
            if top_k is None:
                if i==0:
                    model.generation_config.top_k=0
                else:
                    model.generation_config.top_k=random.randint(0,4)
            else:
                model.generation_config.top_k=top_k
            print(model.generation_config)
            with torch.no_grad():
                batch_out_ids = model.generate(
                    batch_input_ids,
                    return_dict_in_generate=False,
                    generation_config=model.generation_config,
                    max_new_tokens=max_new_tokens,
                    output_scores=True
                )
            padding_lens = [batch_input_ids[i].eq(tokenizer.pad_token_id).sum().item() for i in range(batch_input_ids.size(0))]
            batch_response = [
                decode_tokens(
                    batch_out_ids[i][padding_lens[i]:],
                    tokenizer,
                    raw_text_len=len(batch_raw_text[i]),
                    context_length=(batch_input_ids[i].size(0)-padding_lens[i]),
                    chat_format="chatml",
                    verbose=False,
                    errors='replace'
                ) for i in range(len(batch_raw_text))
                ]
            for j in range(start,end):
                result_instruction = {'index':j,'instruction':instructions[j]["instruction"], 'input':instructions[j]["input"],'output':batch_response[j-start]}
                result_instructions.append(result_instruction)
    print("successful generated!")
    del model
    torch.cuda.empty_cache()
    gc.collect()
    return result_instructions