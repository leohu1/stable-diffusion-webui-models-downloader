import gradio as gr
import json
from modules import scripts
from modules import script_callbacks
from modules import sd_models, paths
import wget

from tqdm import tqdm
import os

import requests, warnings
from requests.packages import urllib3
urllib3.disable_warnings()
warnings.filterwarnings("ignore", module="requests")
warnings.filterwarnings("ignore", module="requests.packages.urllib3")

extension_dir = scripts.basedir()
base_dir = paths.script_path
available_models:dict[str, sd_models.CheckpointInfo] = []
use_wget=False

def get_sd_models():
    sd_models.list_models()
    sd_list = sd_models.checkpoints_list
    names = []
    for key in sd_list:
        names.append(os.path.basename(sd_list[key].filename))
    return names

def get_jinja2_template():
    import jinja2
    templates_path = os.path.join(extension_dir, "templates")
    fileSystemLoader = jinja2.FileSystemLoader(searchpath=templates_path)
    env = jinja2.Environment(loader=fileSystemLoader)
    template = env.get_template('models.html')
    return template


def proccess_models(models:list):
    models_checked_downloaded = models.copy()
    for i, model in enumerate(models_checked_downloaded):
        existed = True
        for file in model["files"]:
            existed = existed and os.path.exists(os.path.join(base_dir, file["path"]))
        model["is_downloaded"] = existed
        model["idx"] = i
    return models_checked_downloaded


def resolve_file_url(url):
    if url.startswith("https://github.com/"):
        url = url.replace("/blob/", "/raw/")
    elif url.startswith("https://huggingface.co/"):
        url = url.replace("/blob/", "/resolve/")
    return url


def update_models_json(url):
    global available_models
    available_models = proccess_models(requests.get(url, verify=False).json()["model"])


def reproccess_models_json():
    global available_models
    available_models = proccess_models(available_models)


tags = [
    "stable_diffusion",
    "vae", 
    "textual_inversion_embedding",
    "hypernetwork", 
]

def create_html():
    template = get_jinja2_template()
    rendered = template.render(models=available_models)
    return rendered

def download_file(url, file_path)->bool:
    if use_wget:
        wget.download(url=url, out=file_path)
        print()
        return True
    else:
        response = requests.get(url, stream=True, allow_redirects=True, verify=False)
    
        total_size_in_bytes= int(response.headers.get('content-length', 0))
        block_size = 1024 #1 Kibibyte
        progress_bar = tqdm(total=total_size_in_bytes, unit='iB', unit_scale=True)
        with open(file_path, 'wb') as file:
            for data in response.iter_content(block_size):
                progress_bar.update(len(data))
                file.write(data)
        progress_bar.close()
        return total_size_in_bytes != 0 and progress_bar.n == total_size_in_bytes


def download_model_button_click(idx):
    model_files = available_models[int(idx)]["files"]
    state = True
    print("Downloading model...")
    for model_file in model_files:
        print(f"Downloading from {model_file['url']}")
        file_state = download_file(resolve_file_url(model_file["url"]), os.path.join(base_dir, model_file["path"]))
        state = state and file_state
    if state:
        reproccess_models_json()
    else:
        print("ERROR, something went wrong")

    html = create_html()
    return [html]

def load_html(url):
    update_models_json(url)
    html = create_html()
    return [html]

def create_downloader_tab():
    html = ""
    with gr.Column():
        load_url_textbox = gr.Textbox(
            value="https://raw.githubusercontent.com/leohu1/stable-diffusion-webui-models-downloader/main/models.json", 
            elem_id="load_url_textbox", label="Models JSON Url")
        load_model_json_button = gr.Button(value="Load", elem_id="Load_model_button")
    with gr.Column(visible=False):
        download_model_button = gr.Button(elem_id="download_model_button")
        download_idx_number = gr.Number(elem_id="download_idx_number")
    download_html = gr.HTML(html, elem_id="download_html")

    load_model_json_button.click(
        fn=load_html,
        inputs=[load_url_textbox],
        outputs=[download_html]
    )

    download_model_button.click(
        fn=download_model_button_click,
        inputs=[download_idx_number],
        outputs=[download_html],
    )


def on_ui_tabs():
    with gr.Blocks(analytics_enabled=False) as models_downloader:
        with gr.Tabs(elem_id="models_downloader_tab"):
            create_downloader_tab()
    return [(models_downloader, "Downloader", "models_downloader")]


script_callbacks.on_ui_tabs(on_ui_tabs)
