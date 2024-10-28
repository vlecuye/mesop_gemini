import time
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


model = GenerativeModel("gemini-1.5-flash",system_instruction=["You are a farmer"])
chat = model.start_chat()
@me.stateclass
class State:
  input: str
  output: str
  in_progress: bool
  file: me.UploadedFile
  files: list[object]

@me.page(path="/")
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
      chat()
      upload()
  footer()

def chat():
   mel.chat(transform, title="Discuss!", bot_user="Name")

def transform():
  return None

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
      "Synthetic Personas Demo",
      style=me.Style(
        font_size=36,
        font_weight=700,
        background="linear-gradient(90deg, #4285F4, #AA5CDB, #DB4437) text",
        color="transparent",
      ),
    )


EXAMPLES = [
  "How to tie a shoe",
  "Make a brownie recipe",
  "Write an email asking for a sick day off",
]


def example_row():
  state = me.state(State)
  is_mobile = me.viewport_size().width < 640
  with me.box(
    style=me.Style(
      display="flex",
      flex_direction="column" if is_mobile else "row",
      gap=24,
      margin=me.Margin(bottom=36),
    )
  ):
    for example in state.files:
      example_box(example, is_mobile)


def example_box(example: object, is_mobile: bool):
  with me.box(
    style=me.Style(
      width="100%" if is_mobile else 200,
      height=140,
      background="#F0F4F9",
      padding=me.Padding.all(16),
      font_weight=500,
      line_height="1.5",
      border_radius=16,
      cursor="pointer",
      margin=me.Margin.all(16)
    ),
    on_click=click_example_box,
  ):
    me.image(src=_convert_contents_data_url(example),style=me.Style(height="100px"))
    me.text(example.name)


def click_example_box(e: me.ClickEvent):
  state = me.state(State)
  state.input = e.key


def chat_input():
  state = me.state(State)
  with me.box(
    style=me.Style(
      padding=me.Padding.all(8),
      background="white",
      display="flex",
      width="100%",
      border=me.Border.all(
        me.BorderSide(width=0, style="solid", color="black")
      ),
      border_radius=12,
      box_shadow="0 10px 20px #0000000a, 0 2px 6px #0000000a, 0 0 1px #0000000a",
    )
  ):
    with me.box(
      style=me.Style(
        flex_grow=1,
      )
    ):
      me.native_textarea(
        value=state.input,
        autosize=True,
        min_rows=4,
        placeholder="Enter your prompt",
        style=me.Style(
          padding=me.Padding(top=16, left=16),
          background="white",
          outline="none",
          width="100%",
          overflow_y="auto",
          border=me.Border.all(
            me.BorderSide(style="none"),
          ),
        ),
        on_blur=textarea_on_blur,
      )
    with me.content_button(type="icon", on_click=click_send):
      me.icon("send")


def textarea_on_blur(e: me.InputBlurEvent):
  state = me.state(State)
  state.input = e.value


def click_send(e: me.ClickEvent):
  state = me.state(State)
  if not state.input:
    return
  state.in_progress = True
  input = state.input
  state.input = ""
  yield

  for chunk in call_api(input):
    state.output += chunk
    yield
  state.in_progress = False
  yield


def call_api(input):
  responses = chat.send_message(
        input,
        stream=True
    )
  for r in responses:
    if r.text :
      for word in r.text.split():
        yield word + " "
        time.sleep(0.05)


def output():
  state = me.state(State)
  if state.output or state.in_progress:
    with me.box(
      style=me.Style(
        background="#F0F4F9",
        padding=me.Padding.all(16),
        border_radius=16,
        margin=me.Margin(top=36),
      )
    ):
      if state.output:
        me.markdown(state.output)
      if state.in_progress:
        with me.box(style=me.Style(margin=me.Margin(top=16))):
          me.progress_spinner()


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
  state = me.state(State)
  state.file = event.file
  currentFiles = state.files.copy()
  currentFiles.append(event.file)
  state.files = currentFiles
  print(state.file)
  print(state.files)


def _convert_contents_data_url(file: me.UploadedFile) -> str:
  return (
    f"data:{file.mime_type};base64,{base64.b64encode(file.getvalue()).decode()}"
  )