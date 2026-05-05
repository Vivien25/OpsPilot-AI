🚀 OpsPilot AI: Visual Operations Agent
🧩 Problem

Operational teams in industries like warehousing, field service, and insurance deal with thousands of images daily—from inventory snapshots to site inspections.

Today, this process is:

manual and time-consuming
inconsistent across teams
reactive instead of proactive

As a result, critical issues like damaged inventory, safety hazards, or defects are often missed or delayed, leading to higher costs and operational risks.

💡 Solution

OpsPilot AI is an autonomous AI agent that transforms large-scale image data into clear, prioritized operational actions.

Instead of just analyzing images, OpsPilot:

understands user goals
searches and analyzes images at scale
groups and classifies issues
validates uncertain cases
generates actionable reports

👉 From “a folder of images” → to “a list of actions”

⚙️ How It Works

OpsPilot AI is built as a multi-agent system:

Planner Agent
Interprets the user’s goal and breaks it into executable steps
Vision Executor Agent
Uses Gemini Vision to understand image content and detect issues
Retrieval Agent (RAG)
Finds relevant images and applies business rules (SOPs, past cases)
Validator Agent
Ensures accuracy and flags uncertain or risky cases
Action Agent
Generates prioritized action lists, grouped results, and reports
🔄 Example Workflow

User input:

“Find all damaged inventory images and create an action list.”

OpsPilot AI:

Searches image library using embeddings
Identifies damaged or risky items
Groups images by issue type
Removes duplicates
Applies SOP rules to determine severity
Generates a prioritized action report

Output:

categorized issue groups
high/medium priority tasks
recommended actions
🛠️ Tech Stack
Frontend: React
Backend: FastAPI
LLM / Vision: Google Gemini (Vertex AI)
Embeddings: Vertex AI Multimodal Embeddings
Vector Search: Vertex AI Vector Search
Storage: Google Cloud Storage
Database: Firestore / PostgreSQL
Deployment: Cloud Run
🌍 Impact

OpsPilot AI reduces:

hours of manual image review → minutes
human error in issue detection
delays in operational response

It enables teams to move from:

reactive inspection → proactive, AI-driven operations

🔮 Future Work
Real-time camera integration
Automated task assignment (integration with Jira / ServiceNow)
Learning from user feedback to improve accuracy
Expansion to industries like healthcare, manufacturing, and insurance