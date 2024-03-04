from getData import getData
from Methods.LanguageModel.getRedundancy import getRedundancy
from config import GLOBAL_CONFIG
from tqdm import tqdm
import json

models=GLOBAL_CONFIG['models']
score={}
for modelname in tqdm(models):
    data=getData(f"Data/data_{modelname}.json")
    redundancy=0
    for qa in data:
        redundancy=redundancy+getRedundancy(qa['output'])
    redundancy=redundancy/len(data)
    score[modelname]=redundancy

filename = 'Data/evaluateResults_redundancy.json'

# 打开文件用于写入，'w' 表示写入模式
with open(filename, 'w') as f:
    # 使用 json.dump 方法将数据写入文件
    # indent 参数是可选的，用于美化输出，使 JSON 文件易于阅读
    json.dump(score, f, indent=4)