# Creative Storyteller - CLEAN START GUIDE
# Follow these steps EXACTLY in order

## What Went Wrong Before

The previous plan had a complex folder structure with subfolders (agents/, tools/, config.py)
and relative imports (from ..config import ...). This is fine for large Python projects but
BREAKS with how ADK loads agents. ADK expects the SIMPLEST possible structure:

    parent_folder/          <-- you run "adk web" from HERE
      creative_storyteller/ <-- this is your "agent app"
        __init__.py         <-- contains: from . import agent
        agent.py            <-- contains: root_agent = Agent(...)
        .env                <-- contains: GOOGLE_CLOUD_PROJECT=...

That's it. Three files. No subfolders. No relative imports.
Everything (tools, config, agent) lives in agent.py.

## Step-by-Step Instructions

### STEP 1: Delete Your Old Project
Delete the entire creative-storyteller folder. We're starting clean.

### STEP 2: Create the Clean Project
Open PowerShell and run:

    mkdir C:\Users\Omkar\Downloads\clean-project
    cd C:\Users\Omkar\Downloads\clean-project
    mkdir creative_storyteller

### STEP 3: Copy the Three Files
Copy these files into C:\Users\Omkar\Downloads\clean-project\creative_storyteller\
  - __init__.py  (the one that says "from . import agent")
  - agent.py     (the big file with root_agent and tools)
  - .env         (edit this with YOUR actual project ID)

Also copy requirements.txt to C:\Users\Omkar\Downloads\clean-project\

### STEP 4: Edit .env With YOUR Project ID
Open creative_storyteller\.env and replace "your-actual-project-id" with your real GCP project ID.
To find your project ID, run:

    gcloud projects list

Copy the PROJECT_ID column value (it looks like: hailmarycreativestoryteller or similar).

### STEP 5: Install Dependencies

    cd C:\Users\Omkar\Downloads\clean-project
    pip install -r requirements.txt

### STEP 6: Authenticate With Google Cloud

    gcloud auth application-default login

This opens a browser. Sign in with your Google account.

### STEP 7: Run the Agent Locally

    cd C:\Users\Omkar\Downloads\clean-project
    python -c "from google.adk.cli import main; main()" web creative_storyteller

NOTE: Run from clean-project folder, NOT from inside creative_storyteller.
NOTE on Windows: If you get NotImplementedError, try:
    python -c "from google.adk.cli import main; main()" web --no-reload creative_storyteller

### STEP 8: Test in Browser
1. Open http://127.0.0.1:8000
2. In the dropdown (top-left), select "creative_storyteller"
3. Type: "Create a short storybook about a brave fox in a moonlit forest"
4. Wait 30-60 seconds for the response with text and images

### STEP 9: Deploy to Cloud Run

    cd C:\Users\Omkar\Downloads\clean-project
    python -c "from google.adk.cli import main; main()" deploy cloud_run --project=YOUR_PROJECT_ID --region=us-central1 --service_name=creative-storyteller --with_ui

Replace YOUR_PROJECT_ID with your actual project ID.

If that doesn't work, use gcloud directly:

    cd C:\Users\Omkar\Downloads\clean-project
    gcloud run deploy creative-storyteller --source . --region us-central1 --allow-unauthenticated --memory=2Gi --timeout=300

## Google Tech Stack Confirmation

Here's what we're using from the photos you shared:

From Image 8 (Vertex AI Platform):
  [x] Gemini models (gemini-2.5-flash for orchestration)
  [x] Vertex AI (via GOOGLE_GENAI_USE_VERTEXAI=TRUE)
  [x] Google GenAI SDK (google-genai package)

From Image 6 (Google AI Stack):
  [x] Gemini CLI / ADK (google-adk package)
  [x] Agent Skills pattern (our tools are "skills" the agent can call)

From Image 1 (Agentic AI Solution):
  [x] LLM Model (Gemini 2.5 Flash)
  [x] Prompt Engineering (detailed system instruction)
  [x] Context Management (Story Bible pattern)
  [x] Application Logic (tool functions)
  [x] Data Stores (Cloud Storage for images)
  [x] API Integrations (Gemini API via GenAI SDK)

From Image 2 (Solution Building Blocks):
  [x] Foundation Models (Gemini text, image, audio)
  [x] Workflow Management (ADK agent orchestration)
  [x] DataStores (Cloud Storage)

From Image 3 (Technical Deep-Dive):
  [x] ReAct Engine (ADK's plan-execute-observe loop)
  [x] MCP (Model Context Protocol - ADK supports this)
  [x] Context Management (ADK session state)

From Image 7 (SDLC):
  [x] Architecture Design (agent + tools pattern)
  [x] API Code Development (FastAPI via ADK)
  [x] Automated Build (Cloud Run from source)

Not yet used but can add:
  [ ] Firebase Hosting (for frontend)
  [ ] Firestore (for persistence)
  [ ] Cloud Trace (for monitoring)
  [ ] Firebase Auth (for user login)
  These are Phase 3+ items. Get the agent working first.
