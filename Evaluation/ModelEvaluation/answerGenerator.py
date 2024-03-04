import openai
import json
from tqdm import tqdm
import time
from getData import getData
openai.api_key = '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'
prompt_qa = '''Given the Question and the Content,generate an Answer that corresponds to the Question and Content, this Answer requires an understanding of the Question based on Content facts. 

Question:When did Beyonce start becoming popular?
Content:Beyoncé Giselle Knowles-Carter (/biːˈjɒnseɪ/ bee-YON-say) (born September 4, 1981) is an American singer, songwriter, record producer and actress. Born and raised in Houston, Texas, she performed in various singing and dancing competitions as a child, and rose to fame in the late 1990s as lead singer of R&B girl-group Destiny's Child. Managed by her father, Mathew Knowles, the group became one of the world's best-selling girl groups of all time. Their hiatus saw the release of Beyoncé's debut album, Dangerously in Love (2003), which established her as a solo artist worldwide, earned five Grammy Awards and featured the Billboard Hot 100 number-one singles "Crazy in Love" and "Baby Boy"
Answer:in the late 1990s

Question:For what movie did Beyonce receive her first Golden Globe nomination?
Content:Following the disbandment of Destiny's Child in June 2005, she released her second solo album, B'Day (2006), which contained hits "Déjà Vu", "Irreplaceable", and "Beautiful Liar". Beyoncé also ventured into acting, with a Golden Globe-nominated performance in Dreamgirls (2006), and starring roles in The Pink Panther (2006) and Obsessed (2009). Her marriage to rapper Jay Z and portrayal of Etta James in Cadillac Records (2008) influenced her third album, I Am... Sasha Fierce (2008), which saw the birth of her alter-ego Sasha Fierce and earned a record-setting six Grammy Awards in 2010, including Song of the Year for "Single Ladies (Put a Ring on It)". Beyoncé took a hiatus from music in 2010 and took over management of her career; her fourth album 4 (2011) was subsequently mellower in tone, exploring 1970s funk, 1980s pop, and 1990s soul. Her critically acclaimed fifth studio album, Beyoncé (2013), was distinguished from previous releases by its experimental production and exploration of darker themes.
Answer:Dreamgirls

Question:"Charlie's Angels" featured which single from the band members?
Content:The remaining band members recorded "Independent Women Part I", which appeared on the soundtrack to the 2000 film, Charlie's Angels. It became their best-charting single, topping the U.S. Billboard Hot 100 chart for eleven consecutive weeks. In early 2001, while Destiny's Child was completing their third album, Beyoncé landed a major role in the MTV made-for-television film, Carmen: A Hip Hopera, starring alongside American actor Mekhi Phifer. Set in Philadelphia, the film is a modern interpretation of the 19th century opera Carmen by French composer Georges Bizet. When the third album Survivor was released in May 2001, Luckett and Roberson filed a lawsuit claiming that the songs were aimed at them. The album debuted at number one on the U.S. Billboard 200, with first-week sales of 663,000 copies sold. The album spawned other number-one hits, "Bootylicious" and the title track, "Survivor", the latter of which earned the group a Grammy Award for Best R&B Performance by a Duo or Group with Vocals. After releasing their holiday album 8 Days of Christmas in October 2001, the group announced a hiatus to further pursue solo careers.
Answer:Independent Women Part I

Question:'''

num_ref=100
qc=getData("Data/EveluateQuestion_Context.json")

for i in tqdm(range(0,num_ref)):
    try:
        prompt=prompt_qa+qc[i]["input"]+"\n"+"Content:"+qc[i]["instruction"]+"\n"+"Answer:"
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                    {"role": "system", "content": "You are a question answering assistant"},
                    {"role": "user", "content": prompt}
                ]
        )
        qc[i]['output']=response['choices'][0]['message']['content']
        time.sleep(6)
    except Exception as e:
        print(i)
        print(e)

filename = 'Data/eveluateData.json'

# 打开文件用于写入，'w' 表示写入模式
with open(filename, 'w') as f:
    # 使用 json.dump 方法将数据写入文件
    # indent 参数是可选的，用于美化输出，使 JSON 文件易于阅读
    json.dump(qc, f, indent=4)