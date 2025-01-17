import transformers
from transformers import BitsAndBytesConfig,GenerationConfig,AutoModelForCausalLM,AutoTokenizer
from utils.utils import jload,process_func
import torch
import json
import pandas as pd
from datasets import Dataset
import global_config
from tqdm import tqdm
import argparse
from utils.qwen_generation_utils import make_context, decode_tokens, get_stop_words_ids

def inference(instructions,temperature=0.7,top_p=0.2,max_new_tokens=512,):
    model_name=global_config.model_name
    lora_model=global_config.lora_model
    bnb_config=BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
            llm_int8_threshold=6.0,
            llm_int8_has_fp16_weight=False,
        )
    
    model = AutoModelForCausalLM.from_pretrained(model_name, trust_remote_code=True, quantization_config=bnb_config, device_map="auto").eval()

    if lora_model!="":
        model.load_adapter(lora_model)
    
    generation_config = GenerationConfig(
            temperature=temperature,
            top_p=top_p,
            do_sample=True,
            num_beams=4,
        )
    model.generation_config=generation_config
    
    tokenizer = AutoTokenizer.from_pretrained(
    global_config.model_name,
    pad_token='<|extra_0|>',
    eos_token='<|endoftext|>',
    padding_side='left',
    trust_remote_code=True
    )
    
    result_instructions = []
    index=0
    for i in tqdm(range(0,len(instructions),5)):
        start=i
        end=min(i+5,len(instructions))
        
        batch_raw_text = []
        for j in range(start,end):
            prompt="Based on content:\n"+ instructions[j]["instruction"]+"Answer Question:\n" + instructions[j]["input"]
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
        print(batch_response)
        for j in range(start,end):
            if hasattr(instructions[j],"output"):
                result_instruction = {'instruction':instructions[j]["instruction"], 'input':instructions[j]["input"], 'output':instructions[j]["output"], 'generated':batch_response[j-start]}
            else:
                result_instruction = {'instruction':instructions[j]["instruction"], 'input':instructions[j]["input"], 'output':"", 'generated':batch_response[j-start]}
            result_instructions.append(result_instruction)
            index = index + 1
            print('index', index)
    print("success inference")
    return result_instructions

if __name__ == "__main__":
    inference("")
