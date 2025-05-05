import os
import subprocess
import json
import logging

# Ensure logs are visible
logging.basicConfig(level=logging.INFO)


def run_cli(command: list[str]) -> str:
    logging.info(f"⚙️ Running CLI: {' '.join(command)}")

    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        stdout = result.stdout.strip()
        stderr = result.stderr.strip()

        logging.info(f"📤 CLI stdout: {stdout}")
        logging.info(f"📥 CLI stderr: {stderr}")
        return stdout if stdout else stderr
    except subprocess.CalledProcessError as e:
        logging.error(f"🔥 CLI error: {e.stderr or e.stdout}")
        return f"CLI Error: {e.stderr.strip() or e.stdout.strip()}"


def validate_vpc(params: dict) -> dict:
    cidr = params.get("cidr")
    region = params.get("region", "fr-par")

    if not cidr:
        return {"error": "Missing 'cidr' parameter for VPC validation."}

    command = [
        "scw", "vpc", "vpc", "list",
        f"project-id={os.getenv('SCW_DEFAULT_PROJECT_ID')}",
        "--output", "json"
    ]

    output = run_cli(command)

    if output.startswith("CLI Error"):
        return {"error": output}

    try:
        networks = json.loads(output)
        for net in networks:
            for subnet in net.get("subnets", []):
                if subnet.get("cidr") == cidr:
                    return {
                        "valid": False,
                        "reason": f"CIDR {cidr} already used in private network '{net['name']}'"
                    }
        return {"valid": True}
    except Exception as e:
        return {"error": f"JSON parsing error: {str(e)}"}


def validate_object_storage(params: dict) -> dict:
    name = params.get("name")
    region = params.get("region", "fr-par")

    if not name:
        return {"error": "Missing 'name' parameter for bucket validation."}

    command = [
        "scw", "object", "bucket", "list",
        "region", region,
        "--output", "json"
    ]
    output = run_cli(command)

    if output.startswith("CLI Error"):
        return {"error": output}

    try:
        buckets = json.loads(output)
        for bucket in buckets:
            if bucket.get("name") == name:
                return {
                    "valid": False,
                    "reason": f"Bucket '{name}' already exists in region {region}"
                }
        return {"valid": True}
    except Exception as e:
        return {"error": f"JSON parsing error: {str(e)}"}


def validate_resource(resource_type: str, parameters: dict) -> dict:
    if resource_type == "vpc":
        return validate_vpc(parameters)
    elif resource_type == "bucket":
        return validate_object_storage(parameters)
    else:
        return {
            "error": f"Validation for resource type '{resource_type}' not implemented."
        }
