from google.api_core.client_options import ClientOptions
from google.cloud import discoveryengine_v1 as discoveryengine
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
from vertexai.preview.generative_models import grounding

tools = [
    Tool.from_retrieval(
        retrieval=grounding.Retrieval(
            source=grounding.VertexAISearch(datastore="projects/prj-iaii-l-underwriting/locations/global/collections/default_collection/dataStores/encyclopedia-datastore_1733772535160"),
        )
    ),
]
generation_config = {
    "temperature": 0,
    "top_p": 0.95,
}
project_id = "prj-iaii-l-underwriting"
location = "global"          # Values: "global", "us", "eu"
engine_id = "underwriting-encyclopedia3_1734624200615"

def search_sample(
    project_id: str,
    location: str,
    engine_id: str,
    search_query: str,
) -> discoveryengine.services.search_service.pagers.SearchPager:
    #  For more information, refer to:
    # https://cloud.google.com/generative-ai-app-builder/docs/locations#specify_a_multi-region_for_your_data_store
    client_options = (
        ClientOptions(api_endpoint=f"{location}-discoveryengine.googleapis.com")
        if location != "global"
        else None
    )

    # Create a client
    client = discoveryengine.SearchServiceClient(client_options=client_options)

    # The full resource name of the search app serving config
    serving_config = f"projects/{project_id}/locations/{location}/collections/default_collection/engines/{engine_id}/servingConfigs/default_config"

    # Optional - only supported for unstructured data: Configuration options for search.
    # Refer to the `ContentSearchSpec` reference for all supported fields:
    # https://cloud.google.com/python/docs/reference/discoveryengine/latest/google.cloud.discoveryengine_v1.types.SearchRequest.ContentSearchSpec
    content_search_spec = discoveryengine.SearchRequest.ContentSearchSpec(
        # For information about snippets, refer to:
        # https://cloud.google.com/generative-ai-app-builder/docs/snippets
        #snippet_spec=discoveryengine.SearchRequest.ContentSearchSpec.SnippetSpec(
        #    return_snippet=True
        #),
        # For information about search summaries, refer to:
        # https://cloud.google.com/generative-ai-app-builder/docs/get-search-summaries
        #summary_spec=discoveryengine.SearchRequest.ContentSearchSpec.SummarySpec(
        #    summary_result_count=5,
        #    include_citations=True,
        #    ignore_adversarial_query=True,
        #    ignore_non_summary_seeking_query=True,
        #    model_prompt_spec=discoveryengine.SearchRequest.ContentSearchSpec.SummarySpec.ModelPromptSpec(
        #        preamble="Send me the best result"
        #    ),
        #    model_spec=discoveryengine.SearchRequest.ContentSearchSpec.SummarySpec.ModelSpec(
        #        version="stable",
        #    ),
        #),
    )

    # Refer to the `SearchRequest` reference for all supported fields:
    # https://cloud.google.com/python/docs/reference/discoveryengine/latest/google.cloud.discoveryengine_v1.types.SearchRequest
    request = discoveryengine.SearchRequest(
        serving_config=serving_config,
        query=search_query,
        page_size=2,
        content_search_spec=content_search_spec,
        query_expansion_spec=discoveryengine.SearchRequest.QueryExpansionSpec(
            condition=discoveryengine.SearchRequest.QueryExpansionSpec.Condition.AUTO,
        ),
        spell_correction_spec=discoveryengine.SearchRequest.SpellCorrectionSpec(
            mode=discoveryengine.SearchRequest.SpellCorrectionSpec.Mode.AUTO
        ),
        # Optional: Use fine-tuned model for this request
        # custom_fine_tuning_spec=discoveryengine.CustomFineTuningSpec(
        #     enable_search_adaptor=True
        # ),
    )
    print("STARTING")
    page_result = client.search(request)

    # Handle the response
    i = 0
    documents = []
    for response in page_result:
        from google.protobuf.json_format import MessageToDict
        response_json = MessageToDict(response._pb)
        print(response_json['document']['derivedStructData']['link'])
        part = Part.from_uri(uri=response_json['document']['derivedStructData']['link'],
    mime_type="text/html",
)
        documents.append(part)
        i = i + 1
        if i >= 3:
            break
    return documents


model = GenerativeModel("gemini-2.0-flash-exp",generation_config=generation_config,system_instruction=["You are an underwriting specialist that has intricate knowledge of all things insurance. You do not decide the rating but only read information from the tables provided. Your goal is to give a rating to the request and explain your rationale in a brief manner.  This rating is calculated by adding up the ratings of the different risk factors. YOU MUST ALWAYS use the information from the documentation and explain the specific section you took the information from. Check your numbers twice, especially when it comes to ranges. NEVER assume numbers and ask clarifying questions if needed to get the full detail. Also note that 'TO X' includes the number written. Assume the client is standard if nothing says otherwise. Never use your own inforamtion to determine a rating, only do it based on the information provided n the documents. NEVER answer with a table"])
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
  #responses = bot.call_graph(prompt)
  search = search_sample(project_id,location,engine_id,prompt)
  search.append(prompt)
  responses = chat.send_message(search,stream=True)
  for r in responses:
    #words = r[1][0].content.split()
    if r.text:
      words = r.text
      for word in words:
        yield word
        time.sleep(0.01)

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
