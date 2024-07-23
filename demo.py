import requests
import os
import gradio as gr
import base64
from pathlib import Path
import tempfile
from PIL import Image
from io import BytesIO



import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--server_name', type=str, default='0.0.0.0', help='服务IP地址')
parser.add_argument('--server_port', type=int, default=7860, help='端口号')
args = parser.parse_args()

css = "style.css"
script_path = "scripts"
_gradio_template_response_orig = gr.routes.templates.TemplateResponse

current_url = ""
current_model_type = ""
current_model = ""
current_option = ["", "", "", ""]
current_search = ""

def reload_javascript():
    # 刷新界面清除history
    if current_url:
        requests.get(url=current_url+'clear')
    
    scripts_list = [os.path.join(script_path, i) for i in os.listdir(script_path) if i.endswith(".js")]
    javascript = ""
    
    for path in scripts_list:
        with open(path, "r", encoding="utf8") as js_file:
            javascript += f"\n<script>{js_file.read()}</script>"

    def template_response(*args, **kwargs):
        res = _gradio_template_response_orig(*args, **kwargs)
        res.body = res.body.replace(
            b'</head>', f'{javascript}</head>'.encode("utf8"))
        res.init_headers()
        return res

    gr.routes.templates.TemplateResponse = template_response

def select_model_cr():
    result = []
    for p in range(len(current_model_list)):
        flag1 = (current_option[0]=="" or current_model_list[p]["modelType"]==current_option[0])
        
        flag2 = None
        if current_option[1]=="其他":
            flag2 = (current_option[1]=="" or current_model_list[p]["manufacturers"] not in ["智谱AI","百川智能","阿里云"])
        else:
            flag2 = (current_option[1]=="" or current_model_list[p]["manufacturers"]==current_option[1])
        flag3 = (current_option[2]=="" or current_model_list[p]["contextLength"]==current_option[2])
        flag4 = (current_option[3]=="" or current_model_list[p]["paramsNumber"]==current_option[3])
        flag5 = (current_search=="" or current_search in current_model_list[p]["modelName"])
        if flag1 and flag2 and flag3 and flag4 and flag5:
            result.append(gr.update(visible=True))
        else:
            result.append(gr.update(visible=False))

    return result
        

# 编辑模型
def edit_model(index):
    print("编辑了")
    
    return gr.update(value=index), gr.update(visible=True), gr.update(visible=True), current_model_list[index]["modelType"], current_model_list[index]["manufacturers"], current_model_list[index]["context"], current_model_list[index]["params"]

# 确认编辑
def edit_model_do(edit_index, text2, text3, text4, text5):
    str_ = """
            <p style="margin-top:10px">模型类别：{}</p>
            <p style="margin-top:10px">厂商：{}</p>
            <p style="margin-top:10px">上下文长度：{}</p>
            <p style="margin-top:10px">模型参数：{}</p>
        """.format(text2, text3, text4, text5)
    global current_model_list
    current_model_list[edit_index]["modelType"] = text2
    current_model_list[edit_index]["manufacturers"] = text3
    current_model_list[edit_index]["context"] = text4
    current_model_list[edit_index]["params"] = text5
    # html_list[edit_index] = gr.update(value=str_)
    return gr.update(visible=False), gr.update(visible=False), gr.update(value=str_)

# 取消编辑
def edit_model_undo():
    return gr.update(visible=False), gr.update(visible=False)

# 删除模型
def delete_model(index):
    print("删除了")
    
    return gr.update(visible=False)
    
# 体验模型
def infer_model(id, modelType, modelName):
    global current_model_type, current_model, current_url
    current_model_type = modelType
    current_model = modelName
    for item in current_model_list:
        if item["modelName"]==current_model:
            current_url = item["website"]
            break
    return gr.Tabs(selected=id), gr.update(value=modelType), gr.update(value=modelName), gr.update(value=change_HTML_1(modelName)), gr.update(value=change_HTML_2(modelName))
    
# 条件筛选1
def select_model_1(value):
    print("条件1筛选了")
    global current_option
    current_option[0] = value
    return select_model_cr()
    
    
# 条件筛选2
def select_model_2(value):
    print("条件2筛选了")
    global current_option
    current_option[1] = value
    return select_model_cr()
    

# 条件筛选3
def select_model_3(value):
    print("条件3筛选了")
    global current_option
    current_option[2] = value
    return select_model_cr()
    

# 条件筛选4
def select_model_4(value):
    print("条件4筛选了")
    global current_option
    current_option[3] = value
    return select_model_cr()
    

# 搜索筛选
def search_model(value):
    print("搜索筛选了")
    global current_search
    current_search = value
    return select_model_cr()
    

# 切换模型列表、隐藏展示上传图片按钮
def update_modelName(first_value):
    if first_value=="文本生成":
        return gr.update(choices=["ChatGLM-3", "MOSS", "internLM", "codeshell", "deepseek", "Baichuan2", "Qwen1.5", "GLM-4", "XVERSE-13B"]), gr.update(visible=False)
    elif first_value=="图像理解":
        return gr.update(choices=["CogVLM", "MiniCPM", "Qwen-VL"]), gr.update(visible=True)
# 选择模型
def select_modelName(second_dropDown, _chat_bot, _app_cfg, task_history):
    if second_dropDown=="请先选择模型类别":
        raise gr.Error("请先选择模型类别")
    
    global current_model, current_url
    current_model = second_dropDown
    for item in current_model_list:
        if item["modelName"]==current_model:
            current_url = item["website"]
            break
    
    # 改变模型清除历史对话
    _chat_bot, _app_cfg = clear_history(_chat_bot, _app_cfg, task_history)
    
    return second_dropDown, gr.update(value=change_HTML_1(current_model)), gr.update(value=change_HTML_2(current_model)), _chat_bot, _app_cfg 

# 修改HTML_1
def change_HTML_1(current_model):
    return """
        <h2 style="line-height:54px;text-align:center;">{}</h2>
        """.format(current_model)

# 修改HTML_2
def change_HTML_2(current_model):
    str_ = ""
    for item in current_model_list:
        if item["modelName"]==current_model:
            with open(item["html"], "r") as file:
                str_ = file.read()
            break
    return str_

def upload_image(image, _chatbot, _app_session, task_history):
    
    # 上传新的图像需要清空历史
    _chatbot, _app_session = clear_history(_chatbot, _app_session, task_history)

    name = image.name
    image_PIL = Image.open(image)

    _app_session['sts']=None
    _app_session['ctx']=[]
    _app_session['img']=image_PIL 

    # # 上传新的图像需要清空历史
    # clear_history(_chat_bot, _app_cfg, task_history)

    task_history = task_history + [((name, ), '图片上传成功，请问有什么可以帮助你的吗？')]
    _chatbot = _chatbot + [((name, ), '图片上传成功，请问有什么可以帮助你的吗？')]
    
    return _chatbot, _app_session, task_history

def submit(_question, _chat_bot, _app_cfg, task_history, max_length, top_p, temperature):
    print("发送")
    # 向算法接口发送post请求
    if _app_cfg['img']:
        # 将img转换为base64格式传输
        # 后端需要base64
        image_PIL = _app_cfg['img']
        byte_stream = BytesIO()
        image_PIL.save(byte_stream, format="PNG")
        byte_stream.seek(0)
        base64_img = base64.b64encode(byte_stream.getvalue()).decode("utf-8")

        data = {
            "image": base64_img,
            "query": _question,
            "max_length": max_length,
            "top_p": top_p,
            "temperature": temperature,
            "file_name": task_history[-1],
        }
    else:
        data = {
            "image": "",
            "query": _question,
            "max_length": max_length,
            "top_p": top_p,
            "temperature": temperature,
            "file_name": [],
        }
    
    response = requests.post(url=current_url+'predict', json=data)
    _answer = response.text
    if _app_cfg['ctx']:
        _context = _app_cfg['ctx'].copy()
    else:
        _context = []
    if _context:
        _context.append({"role": "user", "content": _question})
    else:
        _context = [{"role": "user", "content": _question}] 
    _context.append({"role": "assistant", "content": _answer}) 
    _app_cfg['ctx']=_context

    _chat_bot.append((_question, _answer))
    task_history.append((_question, _answer))

    return '', _chat_bot, _app_cfg

def revoke(_chat_bot, _app_cfg, task_history, max_length, top_p, temperature):
    print("重新生成")
    if not task_history:
        raise gr.Error("历史对话为空！！！！")
    
    else:
        item = task_history.pop(-1)
        _chat_bot.pop(-1)
        
        _app_cfg['ctx'] = _app_cfg['ctx'][:-2]
        
        
        requests.get(url=current_url+'regenerate')
        return submit(item[0], _chat_bot, _app_cfg, task_history, max_length, top_p, temperature)

# 清空历史对话
def clear_history(_chat_bot, _app_cfg, task_history):
    print("清空历史对话")
     
    requests.get(url=current_url+'clear')
    task_history.clear()
    return [], {'sts':None,'ctx':None,'img':None}

# 读取图片base64码
def get_base64_image(image_path):
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode()
        return encoded_string

first_options = ["文本生成", "图像理解"]

model_list = [{
              "id": "001",
              "modelType": "文本生成",
              "modelName": "ChatGLM-3",
              "manufacturers": "智谱AI",
              "context": "32K",
              "contextLength": "16K以上",
              "params": "6B",
              "paramsNumber": "10B以下",
              "website": "",
              "html": "html/chatglm3.html",
            }, {
              "id": "002",
              "modelType": "文本生成",
              "modelName": "MOSS",
              "manufacturers": "复旦大学团队",
              "context": "8K",
              "contextLength": "4K-16K",
              "params": "16B",
              "paramsNumber": "10B-100B",
              "website": "",
              "html": "html/moss.html",
            }, {
              "id": "003",
              "modelType": "文本生成",
              "modelName": "internLM",
              "manufacturers": "上海人工智能实验室",
              "context": "8K",
              "contextLength": "4K-16K",
              "params": "20B",
              "paramsNumber": "10B-100B",
              "website": "",
              "html": "html/internLM.html",
            }, {
              "id": "004",
              "modelType": "文本生成",
              "modelName": "codeshell",
              "manufacturers": "北京大学知识计算实验室",
              "context": "8K",
              "contextLength": "4K-16K",
              "params": "7B",
              "paramsNumber": "10B以下",
              "website": "",
              "html": "html/codeshell.html",
            }, {
              "id": "005",
              "modelType": "图像理解",
              "modelName": "MiniCPM",
              "manufacturers": "面壁智能",
              "context": "8K",
              "contextLength": "4K-16K",
              "params": "2B",
              "paramsNumber": "10B以下",
              "website": "",
              "html": "html/MiniCPM.html",
            }, {
              "id": "006",
              "modelType": "文本生成",
              "modelName": "deepseek",
              "manufacturers": "杭州深度求索",
              "context": "16K",
              "contextLength": "16K以上",
              "params": "7B",
              "paramsNumber": "10B以下",
              "website": "",
              "html": "html/deepseek.html",
            }, {
              "id": "007",
              "modelType": "文本生成",
              "modelName": "Baichuan2",
              "manufacturers": "百川智能",
              "context": "8K",
              "contextLength": "4K-16K",
              "params": "13B",
              "paramsNumber": "10B-100B",
              "website": "",
              "html": "html/baichuan.html",
            }, {
              "id": "008",
              "modelType": "文本生成",
              "modelName": "Qwen1.5",
              "manufacturers": "阿里云",
              "context": "32K",
              "contextLength": "16K以上",
              "params": "32B",
              "paramsNumber": "10B-100B",
              "website": "",
              "html": "html/qwen.html",
            }, {
              "id": "009",
              "modelType": "图像理解",
              "modelName": "CogVLM",
              "manufacturers": "智谱AI",
              "context": "32K",
              "contextLength": "16K以上",
              "params": "17B",
              "paramsNumber": "10B-100B",
              "website": "",
              "html": "html/CogVLM.html",
            }, {
              "id": "010",
              "modelType": "图像理解",
              "modelName": "Qwen-VL",
              "manufacturers": "阿里云",
              "context": "32K",
              "contextLength": "16K以上",
              "params": "32B",
              "paramsNumber": "10B-100B",
              "website": "",
              "html": "html/Qwen_VL.html",
            }, {
              "id": "011",
              "modelType": "文本生成",
              "modelName": "GLM-4",
              "manufacturers": "智谱AI",
              "context": "32K",
              "contextLength": "16K以上",
              "params": "9B",
              "paramsNumber": "10B以下",
              "website": "",
              "html": "html/GLM4.html",
            }, {
              "id": "012",
              "modelType": "文本生成",
              "modelName": "XVERSE-13B",
              "manufacturers": "元象科技",
              "context": "8K",
              "contextLength": "4K-16K",
              "params": "13B",
              "paramsNumber": "10B-100B",
              "website": "",
              "html": "html/xverse.html",
            },]

current_model_list = model_list


uploaded_file_dir = os.environ.get("GRADIO_TEMP_DIR") or str(
    Path(tempfile.gettempdir()) / "gradio"
)

with gr.Blocks(css=css, analytics_enabled=False) as demo:
    edit_index = gr.Number(-1, visible=False)
    with gr.Row(elem_id="edit-row", visible=False) as edit_row:
        
        with gr.Group(elem_id="edit-box", visible=False) as edit_box:
            
            # text1 = gr.Textbox(label="模型名称", container=False)
            text2 = gr.Textbox(label="模型类别", show_label=True, interactive=True)
            text3 = gr.Textbox(label="厂商", show_label=True, interactive=True)
            text4 = gr.Textbox(label="上下文长度", show_label=True, interactive=True)
            text5 = gr.Textbox(label="模型参数", show_label=True, interactive=True)
            with gr.Row(elem_id="edit-box-btn-group"):
                btn_btn_1 = gr.Button("确认", elem_id="edit-btn-true")
                btn_btn_2 = gr.Button("取消", elem_id="edit-btn-false")
        
        
        btn_btn_2.click(edit_model_undo, inputs=None, outputs=[edit_row, edit_box])

    with gr.Tabs(elem_id="tabs") as tabs:
    
        with gr.TabItem("模型库", id=0, elem_id="tab_" + "home") as home_tab:
            # 页面1
            with gr.Blocks(css=css, analytics_enabled=False) as home_interface:
                with gr.Row():
                    with gr.Column(variant="panel", scale=3):
                        type_Radio = gr.Radio(["文本生成", "图像生成", "图像理解"], label="模型类别")
                        manufacturers_Radio = gr.Radio(["智谱AI", "百川智能", "阿里云", "其他"], label="厂商")
                        
                    with gr.Column(variant="panel", scale=3):
                        contextLength_Radio = gr.Radio(["4K以下", "4K-16K", "16K以上"], label="上下文长度")
                        paramsNumber_Radio = gr.Radio(["10B以下", "10B-100B", "100B以上"], label="模型参数")
                        
                    with gr.Column(variant="panel", scale=4):
                        with gr.Row():
                            search_input = gr.Textbox(placeholder="请输入模型名称", show_label=False, container=False)
                            search_btn = gr.Button("搜索", elem_id="search-btn")

                with gr.Row(elem_id="model-box-row"): 
                    # 按钮组
                    edit_btn_list = []
                    del_model_btn_list = []
                    infer_btn_list = []
                    # 盒子,信息组
                    box_list = []
                    html_list = []

                    for num in range(len(current_model_list)):
                        with gr.Group(elem_id="model-box") as box:
                            
                            box_list.append(box)
                            with gr.Row():
                                gr.HTML(
                                """
                                <h4 style="text-align:center;">
                                    {}
                                </h4>
                                """.format(current_model_list[num]["modelName"])
                                )
                            with gr.Row(elem_id="image-row"):
                                gr.Image(value="./images/bot.png", show_label=False, elem_id="model-image", show_download_button=False)
                                html_list.append(gr.HTML(
                                """
                                <p style="margin-top:10px">模型类别：{}</p>
                                <p style="margin-top:10px">厂商：{}</p>
                                <p style="margin-top:10px">上下文长度：{}</p>
                                <p style="margin-top:10px">模型参数：{}</p>
                                """.format(current_model_list[num]["modelType"],current_model_list[num]["manufacturers"],current_model_list[num]["context"],current_model_list[num]["params"])
                                , elem_id="model-message"))
                            with gr.Row(elem_id="button-row"):
                                
                                edit_btn_list.append(gr.Button("编辑", elem_classes="edit-button-group", elem_id="edit-btn-{}".format(num)))
                                del_model_btn_list.append(gr.Button("删除", elem_classes="del-button-group", elem_id="del-model-{}".format(num)))
                                infer_btn_list.append(gr.Button("体验", elem_classes="infer-button-group", elem_id="infer-btn-{}".format(num)))


                type_Radio.change(select_model_1,inputs=[type_Radio],outputs=box_list)
                manufacturers_Radio.change(select_model_2,inputs=[manufacturers_Radio],outputs=box_list)
                contextLength_Radio.change(select_model_3,inputs=[contextLength_Radio],outputs=box_list)
                paramsNumber_Radio.change(select_model_4,inputs=[paramsNumber_Radio],outputs=box_list)
                search_btn.click(search_model,inputs=[search_input],outputs=box_list)
        
        with gr.TabItem("推理界面", id=1, elem_id="tab_" + "model") as model_tab:
            # 页面2
            
            with gr.Blocks(css=css, analytics_enabled=False) as model_interface:  
                
                with gr.Row():
                    html_1 = gr.HTML(value="")

                with gr.Row(elem_id="mar-10"):
                    # 参数列
                    with gr.Column(variant="panel", scale=3):
                        with gr.Row():
                            first_dropDown = gr.Dropdown(choices=first_options, label='模型类别')
                            second_dropDown = gr.Dropdown(choices=[], label='模型名称')
                        with gr.Row():
                            max_length = gr.Slider(minimum=4, maximum=4096, step=4, label='输入序列的最大长度(max_length)', value=2048, interactive=True)
                        with gr.Row():
                            top_p = gr.Slider(minimum=0.01, maximum=1.0, step=0.01, label='核采样(top_p)', value=0.7, interactive=True)
                        with gr.Row():
                            temperature = gr.Slider(minimum=0.01, maximum=1.0, step=0.01, label='随机性(temperature)', value=0.95, interactive=True)
                        with gr.Row():
                            html_2 = gr.HTML(value="")
                    # 对话列
                    with gr.Column(variant="panel", scale=7):
                        chatbot = gr.Chatbot(elem_id="chat-box", show_label=False, height=630)
                        task_history = gr.State([])
                        app_session = gr.State({'sts':None,'ctx':None,'img':None})
                        with gr.Row():
                            input_message = gr.Textbox(placeholder="输入你的内容...(按 Enter 发送)", show_label=False, lines=4, elem_id="chat-input", container=False)
                            clear_input = gr.Button("删除", elem_id="del-btn")
                            addfile_btn = gr.UploadButton("上传图片",elem_id="upload-button", visible=True, file_types=["image"])
                            
                            
                            

                        with gr.Row():
                            submit_btn = gr.Button("发送", elem_id="c_generate")
                            revoke_btn = gr.Button("重新生成",elem_id="revoke-button")
                            clear_history_btn = gr.Button("清空历史对话",elem_id="clear-button")
                            

                first_dropDown.change(update_modelName, inputs=[first_dropDown], outputs=[second_dropDown, addfile_btn])
                second_dropDown.change(select_modelName, inputs=[second_dropDown, chatbot, app_session, task_history], outputs=[second_dropDown, html_1, html_2, chatbot, app_session])
                clear_input.click(lambda x: "", inputs=[input_message], outputs=[input_message])

                
                addfile_btn.upload(upload_image, inputs=[addfile_btn,chatbot,app_session, task_history], outputs=[chatbot,app_session, task_history], show_progress=True)
                
                submit_btn.click(
                    submit,
                    [input_message, chatbot, app_session, task_history, max_length,top_p,temperature], 
                    [input_message, chatbot, app_session],
                    show_progress=True
                )
                
                revoke_btn.click(
                    revoke,
                    [chatbot, app_session, task_history, max_length,top_p,temperature], 
                    [input_message, chatbot, app_session],
                    show_progress=True
                )
                
                clear_history_btn.click(clear_history, inputs=[chatbot, app_session, task_history], outputs=[chatbot, app_session], show_progress=True)
                

            
    # 按钮组的逻辑
    for p in range(len(current_model_list)):
        edit_btn_list[p].click(edit_model,inputs=[gr.Number(p,visible=False)],outputs=[edit_index, edit_row, edit_box, text2, text3, text4, text5])
        del_model_btn_list[p].click(delete_model,inputs=[gr.Number(p,visible=False)],outputs=[box_list[p]])
        infer_btn_list[p].click(infer_model,inputs=[gr.Number(1,visible=False), gr.State(current_model_list[p]["modelType"]),gr.State(current_model_list[p]["modelName"])],outputs=[tabs, first_dropDown, second_dropDown, html_1, html_2])
    # 编辑确认按钮的逻辑
    btn_btn_1.click(edit_model_do, inputs=[edit_index, text2, text3, text4, text5], outputs=[edit_row, edit_box, html_list[edit_index.value]])

if __name__ == "__main__":
    reload_javascript()
    demo.launch(server_name=args.server_name, server_port=args.server_port)
