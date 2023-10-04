import werobot
from werobot.replies import TextReply
import openai
import datetime
import math
import markdown
from pygments.formatters import HtmlFormatter
import threading
import sys

# 初始化你的robot
robot = werobot.WeRoBot(token='',app_id='',encoding_aes_key='')

# 初始化OpenAI
openai.api_key = ''

# 定义一个全局变量来保存用户的模型选择和角色
user_choice = {}
user_choice['prompt']="You are a helpful assistant."
user_choice['model']="gpt-3.5-turbo-16k-0613"

@robot.subscribe
def subscribe(message):
    return 'PS：感谢关注，这里是AI助手'



def md_html(markdown_file_path,html_file_path):
    with open(markdown_file_path, 'r', encoding='utf-8') as markdown_file:
        markdown_content = markdown_file.read()

    # 创建代码高亮样式
    style = HtmlFormatter().get_style_defs('.highlight')

    html = markdown.markdown(markdown_content, extensions=[
        'markdown.extensions.fenced_code',
        'markdown.extensions.codehilite'
    ])

    # 将 markdown 文本转化为html
    html = f"<style>{style}</style>\n{html}"

    type = sys.getfilesystemencoding()

    with open(html_file_path, 'w', encoding='gb2312',errors='ignore') as html_file:
        html_file.write(html)

def gpt(model,prompt,message):
    reply = openai.ChatCompletion.create(
        model=model,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": message},
        ]
    )

    # 时间戳处理
    timestamp = reply.created
    dt_object = datetime.datetime.fromtimestamp(timestamp)
    formatted_date = dt_object.strftime('%Y-%m-%d %H:%M:%S')  # 转换为 '年-月-日 时:分:秒' 的格式

    # 价格处理
    if reply.model == 'gpt-3.5-turbo-16k-0613':
        InputPrice = reply.usage.prompt_tokens / 1000 * 0.003
        OutputPrice = reply.usage.completion_tokens / 1000 * 0.004
        TaltalPrice = InputPrice + OutputPrice
        top = ('<h1>' + reply.model + '<h1><br />' + '<hr>'
            '<h4>时间：' + str(formatted_date) + '<h4><br />'
            '<h4>文本数量：' + str( reply.usage.total_tokens) + 'tokens<h4><br />'
            '<h4>成本：' + str(math.ceil(TaltalPrice * 7.3 * 10000) / 10000) + '元(由美元转换用于参考)<h4><br />'
            '<h4>Input：0.003$/1k tokens，Output：0.004$/1k tokens<h4><br />'
            '<h4>飞宇的朋友免费使用！！gpt4更强大！想要更好的回复可以使用哦！!<h4><br />'
            '<h4><b>PS：输入“开始”进行模型选择，或使用“model:，prompt:”修改相关参数</b><h4><br />'
             '<hr>'
               )
    else:
        InputPrice = reply.usage.prompt_tokens / 1000 * 0.03
        OutputPrice = reply.usage.completion_tokens / 1000 * 0.06
        TaltalPrice = InputPrice + OutputPrice
        top = ('<h1>'+reply.model+'<h1><br />'+'<hr>'
              '<h4>时间：' + str(formatted_date) + '<h4><br />'
              '<h4>文本数量：' + str(reply.usage.total_tokens) + 'tokens<h4><br />'
              '<h4>成本：' + str(math.ceil(TaltalPrice * 7.3 * 10000) / 10000) + '元(由美元转换用于参考)<h4><br />'
                '<h4>Input：0.03$/1k tokens，Output：0.06$/1k tokens<h4><br />'
              '<h4><b>PS：输入“开始”进行模型选择，或使用“model:，prompt:”修改相关参数</b><h4><br />'
               '<hr>'
              )

    file_name = "index.md"
    file = open(file_name, "w")
    file.write(top+reply.choices[0].message.content)
    file.close()

    md_html('index.md', '/var/www/html/index.html')


def str_tran(str_in):
    str_out = ''
    for char in str_in:
        inside_code = ord(char)
        if inside_code == 0x3000:
            inside_code = 0x0020
        elif 0xFF01 <= inside_code <= 0xFF5E:
            inside_code -= 0xfee0
        str_out += chr(inside_code).lower()
    str_out = str_out.replace(' ', '')
    return str_out


@robot.text
def first_choice(message):
    def f(my_string):
        my_dict = {"gpt3": "gpt-3.5-turbo-16k-0613", "gpt4": "gpt-4-0613"}
        # 遍历字典中的值
        flag = bool()
        for value in my_dict.keys():
            # 如果字符串包含字典中的值
            if value in my_string:
                flag = True
                break
            else:
                flag = False
        return flag
    #用户消息处理
    global user_choice
    dic_m = {"gpt3": "gpt-3.5-turbo-16k-0613", "gpt4": "gpt-4-0613"}
    if message.content == '开始':
        reply = TextReply(message=message, content='请选择模型类型："gpt3"or"gpt4"')
        return reply

    elif message.content in ['gpt3', 'gpt4']:
        if not f(message.content):
            reply = TextReply(message=message, content='模型选择出错，未更改，将使用默认模型（gpt3）')
            return reply
        else:
            user_choice['model'] = dic_m[message.content]
            reply = TextReply(message=message, content='选择完成，请提问！（更改prompt请发送“prompt：+内容”）')
            return reply

    elif str_tran(message.content).startswith('model:'): # 用户在对话框输入模型信息
        if not f(message.content):
            reply = TextReply(message=message, content='模型选择出错，未更改，将使用默认模型（gpt3）')
            return reply
        else:
            user_choice['model'] = dic_m[message.content[6:]]  # 更新模型信息
            reply = TextReply(message=message, content='模型已更改为：' + user_choice['model'])
            return reply

    elif str_tran(message.content).startswith('prompt:'):  # 用户在对话框输入提示词
        user_choice['prompt'] = message.content[7:]  # 更新提示词
        return '提示词已更改为： ' + user_choice['prompt']

    #正常输出ChatGPT回答
    elif str_tran(message.content).startswith('heygpt:'):
        t1 = threading.Thread(target=gpt, args=(user_choice['model'], user_choice['prompt'], message.content[7:]))
        t1.start()
        #回复内容
        reply = TextReply(message=message, content='点击此链接查看回复\n'
                                                   '请在微信右上角手动刷新页面\n'
                                                   '（若未更新请耐心等待）\n'
                                                   '通常需要5-30秒\n'
                                                   '我知道你很急但请你先别急\n'
                                                   'http://124.222.22.212:8080')
        return reply
    else:
        return '您好，请联系管理员了解使用方式'

# 开始聊天
robot.config['HOST'] = '0.0.0.0'
robot.config['PORT'] = 80
robot.run()