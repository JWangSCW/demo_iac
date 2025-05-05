from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import logging
import json

from langchain_agent import run_agent

app = FastAPI()
templates = Jinja2Templates(directory="templates")

logging.basicConfig(level=logging.INFO)

@app.get("/")
def root():
    return RedirectResponse(url="/ui")


@app.get("/ui")
def show_form(request: Request):
    return templates.TemplateResponse("ui.html", {"request": request, "iac_code": "", "prompt": ""})


@app.post("/ui")
def process_form(request: Request, prompt: str = Form(...)):
    logging.info(f"🟡 Received prompt: {prompt}")
    try:
        result = run_agent(prompt)
        logging.info(f"✅ Agent result: {result}")
        iac_code = result if isinstance(result, str) else json.dumps(result, indent=2)
    except Exception as e:
        logging.error(f"❌ Agent error: {e}")
        iac_code = f"Error: {str(e)}"

    return templates.TemplateResponse("ui.html", {"request": request, "prompt": prompt, "iac_code": iac_code})


@app.post("/agent", response_class=JSONResponse)
def agent_api(request: Request):
    body = request.json()
    prompt = body.get("prompt")
    if not prompt:
        return {"error": "Missing prompt"}
    try:
        result = run_agent(prompt)
        return {"result": result}
    except Exception as e:
        return {"error": str(e)}