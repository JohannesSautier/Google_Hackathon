Immigration Timeline Management Backend
This project is a comprehensive, AI-powered backend designed to help users manage and track their immigration process timelines. It's built on Google Cloud Functions (Python) and Firebase, leveraging Vertex AI (Gemini) for intelligent timeline generation and various external APIs for real-time data enrichment.

The system is event-driven and asynchronous. Users create a "journey," upload relevant documents, and the backend orchestrates a pipeline to parse these documents, generate a feasible timeline, and then continuously monitor for external events (like news or emails) that might affect that timeline.

🚀 Core Features
Dynamic Timeline Generation: Automatically creates a step-by-step timeline after analyzing user-uploaded documents.

Document Intelligence: Integrates with an external API to parse PDFs and extracts structured data like key dates and process types.

Proactive Agents: Uses scheduled cron jobs to run agents that monitor external sources (email, news) for events that could impact the user's journey.

Event-Driven Architecture: Built around Firestore triggers and Pub/Sub messages, making the system scalable and resilient.

Secure & Scalable: Leverages the robust infrastructure of Firebase and Google Cloud for authentication, storage, and serverless compute.

⚙️ System Architecture
The backend consists of several key components:

Firebase Firestore: The central NoSQL database used to store all state, including user journeys, parsed documents, and event logs.

Firebase Cloud Storage: Used to store user-uploaded documents securely.

Google Cloud Functions: Hosts all the serverless Python code for API endpoints and background processing.

Vertex AI (Gemini 1.5 Flash): The generative AI model used to create the initial timeline from parsed document data.

Google Cloud Scheduler & Pub/Sub: Used to trigger the proactive news and mail agents on a configurable schedule.

External APIs: The system is designed to call out to your hosted APIs for document parsing, email analysis, and news crawling.

Setup and Installation
Follow these steps precisely to set up your local environment and deploy the backend.

1. Prerequisites
Google Cloud Account: You need a GCP project with billing enabled.

Node.js: Required for the Firebase CLI. Install Node.js.

Python: Python 3.9 or newer is required.

gcloud CLI: The Google Cloud Command-Line Interface. Install gcloud CLI.

Firebase CLI: The command-line tool for Firebase. Install it by running:

npm install -g firebase-tools

2. Initial gcloud & Firebase Login
First, authenticate your local machine with Google Cloud and Firebase.

# Log in to your Google Cloud account
gcloud auth login

# Set up Application Default Credentials for local testing
gcloud auth application-default login

# Log in to your Firebase account
firebase login

3. Firebase Project Setup
Create a Firebase Project: Go to the Firebase Console and create a new project. Link it to your existing Google Cloud project.

Initialize Local Project: In your terminal, navigate to your project's root folder and run:

firebase init

When prompted, use the arrow keys and spacebar to select Firestore, Functions, and Storage.

Choose "Use an existing project" and select your project.

Accept the default names for the rules and index files.

When asked about Functions, select Python, and decline to install dependencies with pip if you're managing it manually. Say No (n) to overwriting any existing Python files.

Set Default GCP Location: This is a critical one-time step.

Go to your Firebase Project Settings (gear icon ⚙️).

On the "General" tab, find Default GCP resource location and set it to a region of your choice (e.g., eur3 to be near europe-west1).

4. Configure Python Environment
Navigate into the functions directory created by the init command. It's highly recommended to use a virtual environment.

# Navigate into the functions directory
cd functions

# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate

# Install all required dependencies from your requirements file
pip install -r requirements.txt

5. Configure Cloud Services
Enable Firestore: Go to the Firestore Database section in the Firebase Console and create a new database in Native mode.

Enable Storage: Go to the Storage section and click "Get started" to enable it.

Enable APIs: Go to the Google Cloud Console and ensure the following APIs are enabled for your project:

Cloud Functions API

Cloud Build API

Artifact Registry API

Cloud Run API

Cloud Scheduler API

Cloud Pub/Sub API

Vertex AI API

Create Pub/Sub Topic:

Go to the Pub/Sub page in the Google Cloud Console.

Create a new topic with the ID agent-triggers.

Set IAM Permissions:

Go to the IAM page in the Google Cloud Console.

Find the Cloud Storage service agent (service-PROJECT_NUMBER@...) and ensure it has the Cloud Run Invoker role. You may need to check "Include Google-provided role grants" to see it.

Deployment
Deploying the backend is done via the Firebase CLI from your project's root directory.

To Deploy All Functions at Once
This is the standard command for a full deployment.

firebase deploy --only functions

To Deploy a Single Function
This is much faster and is recommended during development when you are only changing one piece of logic.

# Example for the journey creation endpoint
firebase deploy --only functions:create_journey

# Example for the cron job runner
firebase deploy --only functions:run_scheduled_agent

⚙️ API Endpoints
All HTTP endpoints are configured with a CORS policy to allow requests from any origin (*). For a production environment, you should restrict this to your frontend's specific domain.

POST /create_journey
Creates a new journey for a user. The created document will include a journeyId field that matches its unique document ID.

Body (JSON):

{
    "userId": "some_user_id",
    "originCountry": "IN",
    "destinationCountry": "DE",
    "nationality": "IN",
    "purpose": "EDUCATION"
}

Success Response (201): Journey created successfully with ID: <new_journey_id>

GET /get_journey
Retrieves the full data for a single journey.

Query Parameters: id=<journey_id>

Example: GET /get_journey?id=Abc123xyz

Success Response (200): A JSON object containing the full journey document.

GET /get_all_journeys
Retrieves a list of all journey documents in the database.

Success Response (200): A JSON array of journey objects.

POST /upload_document
Uploads a document for a specific journey.

Type: multipart/form-data

Fields:

journeyId: The ID of the journey this document belongs to.

document: The file itself (e.g., a PDF).

GET /get_data_points
Retrieves historical data points for a journey, with an optional filter.

Query Parameters:

journeyId=<journey_id> (required)

sourceType=<source_type> (optional, e.g., NEWS_API)

Success Response (200): A JSON array of data point objects.