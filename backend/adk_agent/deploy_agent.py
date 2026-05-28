import argparse
import os

import vertexai

from .agent import DEFAULT_API_BASE, root_agent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Deploy the OpsPilot ADK agent to Vertex AI Agent Engine.")
    parser.add_argument("--project", required=True, help="Google Cloud project ID.")
    parser.add_argument("--location", default="us-central1", help="Vertex AI region.")
    parser.add_argument("--api-base", default=DEFAULT_API_BASE, help="OpsPilot backend base URL.")
    parser.add_argument("--staging-bucket", required=True, help="GCS bucket URI for Agent Engine staging, such as gs://opspilot-ai-agent-staging.")
    parser.add_argument("--display-name", default="OpsPilot AI Warehouse Operations Agent")
    parser.add_argument(
        "--description",
        default="ADK agent that calls OpsPilot Cloud Run tools for shipment validation, warehouse maps, and product recognition.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    client = vertexai.Client(project=args.project, location=args.location)

    remote_agent = client.agent_engines.create(
        agent=root_agent,
        config={
            "display_name": args.display_name,
            "description": args.description,
            "staging_bucket": args.staging_bucket,
            "requirements": [
                "google-adk",
                "google-cloud-aiplatform[agent_engines,adk]",
                "cloudpickle",
                "pydantic",
            ],
            "extra_packages": [
                "backend/__init__.py",
                "backend/adk_agent",
            ],
            "env_vars": {
                "OPSPILOT_API_BASE": args.api_base,
                "OPSPILOT_ADK_MODEL": os.getenv("OPSPILOT_ADK_MODEL", "gemini-2.5-flash"),
            },
            "agent_framework": "google-adk",
        },
    )

    print("Deployed OpsPilot ADK agent:")
    print(remote_agent.api_resource.name)


if __name__ == "__main__":
    main()
