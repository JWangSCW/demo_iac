import os
import requests
import json
from typing import List, Optional

from langchain.agents import AgentType, initialize_agent
from langchain.tools import Tool
from langchain.llms.base import LLM

from tools.scaleway_cli import validate_resource, run_cli


# === Custom LLM wrapper for DeepSeek ===
class DeepSeekLLM(LLM):
    model: str
    endpoint: str
    api_key: str
    temperature: float = 0.3
    max_tokens: int = 512

    def _call(self, prompt: str, stop: Optional[List[str]] = None) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        system_prompt = (
            "You are an infrastructure automation agent for Scaleway.\n"
            "Always reason using tools.\n"
            "Use this structure:\n"
            "Thought: what to do\n"
            "Action: name of the tool\n"
            "Action Input: the JSON input\n"
            "Observation: result\n"
            "Final Answer: the summary or output."
        )

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }

        print("🧠 Payload:", json.dumps(payload, indent=2))
        response = requests.post(self.endpoint, headers=headers, json=payload)
        response.raise_for_status()

        response_json = response.json()
        print("📬 DeepSeek response:", json.dumps(response_json, indent=2))
        return response_json["choices"][0]["message"]["content"]

    @property
    def _llm_type(self) -> str:
        return "deepseek-llm"


# === Tools ===
def list_resources(resource_type: str, region: str = "fr-par") -> dict:
    project_id = os.getenv("SCW_DEFAULT_PROJECT_ID")

    if resource_type == "vpc":
        command = ["scw", "vpc", "vpc", "list", f"project-id={project_id}", f"region={region}", "--output", "json"]
    elif resource_type == "bucket":
        command = ["scw", "object", "bucket", "list", f"region={region}", f"project-id={project_id}", "--output", "json"]
    else:
        return {"error": f"Unsupported resource type: {resource_type}"}

    try:
        output = run_cli(command)
        return {"items": output}
    except Exception as e:
        return {"error": str(e)}


def generate_terraform_code(prompt: str) -> str:
    llm = DeepSeekLLM(
        model=os.getenv("MODEL_NAME"),
        endpoint=os.getenv("INFERENCE_ENDPOINT"),
        api_key=os.getenv("SCW_SECRET_KEY")
    )
    instruction = (
        "Respond ONLY with valid Terraform code — no explanation, no Markdown, no commentary.\n"
        "Only output clean provider/resource blocks."
    )
    full_prompt = f"{instruction}\n\n{prompt}"
    return llm(full_prompt)


# === Define LangChain Tools ===
tools = [
    Tool.from_function(
        func=validate_resource,
        name="validate_resource",
        description="Validate resources like VPCs or buckets in Scaleway. Takes resource_type and parameters."
    ),
    Tool.from_function(
        func=list_resources,
        name="list_resources",
        description="List existing resources in Scaleway, e.g. VPCs or buckets. Takes resource_type and region."
    ),
    Tool.from_function(
        func=generate_terraform_code,
        name="generate_terraform",
        description="Generate Terraform code from a user prompt."
    )
]


# === Lazy Agent Initialization ===
_agent = None

def get_agent():
    global _agent
    if _agent is None:
        llm = DeepSeekLLM(
            model=os.getenv("MODEL_NAME"),
            endpoint=os.getenv("INFERENCE_ENDPOINT"),
            api_key=os.getenv("SCW_SECRET_KEY")
        )
        _agent = initialize_agent(
            tools=tools,
            llm=llm,
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            agent_kwargs={
                "prefix": "You are an automation agent for managing Scaleway infrastructure. Always decide what to do using the available tools. NEVER explain your thinking. Only take actions.",
                "format_instructions": (
                    "Use the following format:\n\n"
                    "Thought: what you need to do\n"
                    "Action: the action to take, must be one of [validate_resource, list_resources, generate_terraform]\n"
                    "Action Input: the JSON input to the action\n"
                    "Observation: the result of the action\n"
                    "... (you can repeat Thought/Action/Observation)\n"
                    "Final Answer: the answer to the user"
                )
            },
            handle_parsing_errors=True,
            verbose=True,
            max_iterations=3
        )
    return _agent


def run_agent(prompt: str):
    agent = get_agent()
    return agent.run(prompt)
