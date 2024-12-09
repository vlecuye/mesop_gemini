
import time
import bot
import base64
import mesop as me
import mesop.labs as mel
from vertexai.generative_models import (
    GenerationConfig,
    GenerativeModel,
    HarmBlockThreshold,
    FunctionDeclaration,
    HarmCategory,
    Part,
    Tool,
    Content,
    grounding,
    ChatSession
)


model = GenerativeModel("gemini-1.5-flash",system_instruction=[""])
chat = model.start_chat()
@me.stateclass
class State:
  input: str
  output: str
  in_progress: bool
  file: me.UploadedFile
  files: list[object]
  selected: list[int]

@me.page(path="/",security_policy=me.SecurityPolicy(dangerously_disable_trusted_types=True))
def page():
  
  with me.box(
    style=me.Style(
      background="#fff",
      min_height="calc(100% - 48px)",
      padding=me.Padding(bottom=16),
    )
  ):
    with me.box(
      style=me.Style(
        width="min(720px, 100%)",
        margin=me.Margin.symmetric(horizontal="auto"),
        padding=me.Padding.symmetric(
          horizontal=16,
        ),
      )
    ):
      header_text()
      example_row()
      chat_box()
      upload()
  footer()

def chat_box():
   mel.chat(transform, title="Discuss!", bot_user="Name")

def transform(prompt:str, history:list):
  length = 0
  responses = bot.call_graph()
  for r in responses:
    print("New MESSAGE!")
    
    if len(r[1][0].content) != length:
      print(r[1][0])
      for word in r[1][0].content.split():
        yield word + " "
        time.sleep(0.05)
    length = len(r[1][0].content)

def header_text():
  with me.box(
    style=me.Style(
      padding=me.Padding(
        top=64,
        bottom=36,
      ),
    )
  ):
    me.text(
      "Underwriting Proof Of Concept",
      style=me.Style(
        font_size=36,
        font_weight=700,
        background="linear-gradient(90deg, #4285F4, #AA5CDB, #DB4437) text",
        color="transparent",
      ),
    )

def example_row():
  state = me.state(State)
  if len(state.files) > 0 :
    me.text("Files used:",style=me.Style(font_size=24,font_weight=600))
  is_mobile = me.viewport_size().width < 640
  with me.box(
    style=me.Style(
      display="flex",
      flex_direction="column" if is_mobile else "row",
      gap=24,
      margin=me.Margin(bottom=36),
    )
  ):
    for i,example in enumerate(state.files):
      example_box(example, i)


def example_box(example: object, index: int):
  with me.box(
    style=me.Style(
      width="33%",
      height=200,
      background="#F0F4F9",
      padding=me.Padding.all(16),
      font_weight=500,
      line_height="1.5",
      border_radius=16,
      cursor="pointer",
    ),
  ):
    me.image(src=_convert_contents_data_url(example),style=me.Style(height="auto",width="100%"))
    me.text(example.name)

def footer():
  with me.box(
    style=me.Style(
      position="sticky",
      bottom=0,
      padding=me.Padding.symmetric(vertical=16, horizontal=16),
      width="100%",
      background="#F0F4F9",
      font_size=14,
    )
  ):
    me.html(
      "Made with <a href='https://google.github.io/mesop/'>Mesop</a>",
    )

def upload():
  state = me.state(State)
  with me.box(style=me.Style(padding=me.Padding.all(15))):
      me.uploader(
        label="Upload Image",
        accepted_file_types=["image/jpeg", "image/png"],
        on_upload=handle_upload,
        type="flat",
        color="primary",
        style=me.Style(font_weight="bold"),
      )

      if state.file.size:
        with me.box(style=me.Style(margin=me.Margin.all(10))):
          me.text(f"File name: {state.file.name}")
          me.text(f"File size: {state.file.size}")
          me.text(f"File type: {state.file.mime_type}")


def handle_upload(event: me.UploadEvent):
  bot.call_graph()
  state = me.state(State)
  state.file = event.file
  currentFiles = state.files.copy()
  currentFiles.append(event.file)
  state.files = currentFiles
  return None


def _convert_contents_data_url(file: me.UploadedFile) -> str:
  return (
    f"data:{file.mime_type};base64,{base64.b64encode(file.getvalue()).decode()}"
  )