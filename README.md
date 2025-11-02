Offline AI Council

This repository contains the complete blueprint for building a 100% private, offline-first AI research assistant. It is designed to run on low-resource hardware (like an old laptop) and be accessible from any device (like your phone).

This project's architecture was designed around a 2017 MacBook Air (Intel i5, 8GB RAM, macOS Monterey). This hardware constraint is the reason for its specific technology choices, prioritizing an extremely low memory/CPU footprint over all else.

Core Philosophy & Features

100% Privacy: No data ever leaves your local network. No APIs, no data leaks, no subscription fees. You own your data.

Long-Term Memory (RAG): The AI learns from your documents. It uses ChromaDB as a vector database, allowing you to create a "knowledge base" from your PDFs, text files, and code.

Robust Reasoning (MCP): This is the "AI Council." Instead of trusting one answer, the backend acts as a Multi-agent Council. It concurrently queries multiple AI models with your question (plus the RAG context) and synthesizes their "opinions" into a final, more reliable answer.

Lightweight PWA Frontend: The UI is a Progressive Web App (PWA). This means you can "install" it on your phone's home screen (iOS or Android) just like a native app, but it's served from a single, simple HTML/JS/CSS codebase.

Open Source: This entire stack is open-source to provide a blueprint for anyone to run their own private, sovereign AI.

System Architecture

This project runs as a set of coordinated microservices, all orchestrated by a central backend.

┌───────────────────┐        ┌──────────────────┐
│  Phone / Browser  │        │   Your Documents │
│  (PWA Frontend)   │        │   (.pdf, .txt)   │
└─────────┬─────────┘        └────────┬─────────┘
          │ (via Wi-Fi or ngrok)      │ (One-Time)
          │                           │
          ▼                           ▼
┌───────────────────┐      ┌───────────────────┐
│ Rust API Backend  │      │ Python Ingestion  │
│(ai_council_server)├─(RAG)►│  (ai_ingestion)   │
└─────────┬─────────┘      └────────┬──────────┘
          │ (MCP)                     │
          │                           │
┌─────────▼─────────┐      ┌──────────▼────────┐
│  Ollama           │      │  ChromaDB         │
│  (tinyllama model)│      │  (Vector Database)│
└───────────────────┘      └───────────────────┘


Technology Stack

Backend: Rust (with Axum & Tokio) for its high performance and near-zero memory footprint.

Frontend: PWA (Vanilla HTML, CSS, JavaScript) for universal cross-platform access.

LLM Runner: Ollama

Vector Database: ChromaDB (running in Docker)

AI Model: tinyllama (1.1B). After testing phi3, llama2, and gemma, tinyllama was the most compatible and performant model for this specific hardware.

Automation: Python3 + AppleScript (server_manager) to start and stop all services with one command.

Secure Tunneling: ngrok (Optional) for accessing your server from outside your local network.

Project Structure (Monorepo)

/
├── ai_council_server/  # The high-performance Rust backend (Axum)
├── pwa_frontend/       # The installable PWA chat UI (HTML/JS/CSS)
├── ai_ingestion/       # Python script to add documents to memory (RAG)
└── server_manager/     # Python script to start/stop all services


Installation & Setup Guide

This guide assumes you are on macOS.

1. Install Prerequisites

You must install all of the following:

Homebrew: The macOS package manager.

Git: brew install git

Rust: curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

Python 3: macOS comes with it, but brew install python is recommended.

Docker Desktop: The latest version compatible with macOS 12 (Monterey) is 4.41.2. Do not use the newest release.

ngrok: brew install ngrok

Ollama (Manual Install):

DO NOT use the standard Ollama installer. It requires macOS 14+.

Go to the Ollama GitHub Releases.

Find an older release (e.g., v0.1.32) and download the ollama-darwin file.

Move it to your system path:

sudo mv ~/Downloads/ollama-darwin /usr/local/bin/ollama
chmod +x /usr/local/bin/ollama


2. Clone This Repository

git clone [https://github.com/invidias-codem/offline-ai-council.git](https://github.com/invidias-codem/offline-ai-council.git)
cd offline-ai-council


3. Configure the Project

The server_manager needs to know where your project folders are.

Open the server_manager/config.json file.

Update the rust_backend_path and pwa_folder_path to their full, absolute paths on your machine.

{
    "rust_backend_path": "/Users/jroot/path/to/offline-ai-council/ai_council_server",
    "pwa_folder_path": "/Users/jroot/path/to/offline-ai-council/pwa_frontend"
}


4. Phase 1: Ingest Your Documents (RAG)

Before you can chat, you must give your AI a "memory."

Start Docker: Open the Docker Desktop app.

Start ChromaDB: In a terminal, start the vector database:

docker run -d -p 8000:8000 --name chromadb chromadb/chroma


Add Documents: Place your .pdf, .txt, .md, or code files into the ai_ingestion/my_documents/ folder.

Install Python Dependencies:

cd ai_ingestion
pip3 install -r requirements.txt 
# (You will need to create a requirements.txt file for:
# pip3 install chromadb-client langchain pypdf sentence-transformers)


Run the Ingestion Script:

python3 ingest.py


This will read all your documents, chunk them, and add them to the ChromaDB. You only need to do this when you want to add new knowledge.

5. Phase 2: Run the Server Stack

We've automated this! The manager.py script will open all 6 required terminals for you.

cd into the server_manager folder.

Run the start command:

python3 manager.py start


This will open 6 new terminal windows, one for each service:

Ollama Server

ChromaDB (Docker)

Rust Backend

PWA Frontend Server

ngrok Tunnel (for Backend)

ngrok Tunnel (for Frontend)

6. How to Use Your AI

Local Access (On Your Home Wi-Fi)

On your Mac, find your Local IP (System Preferences > Network > Wi-Fi). It will be like 192.168.1.XX.

On your phone (on the same Wi-Fi), open a browser and go to http://<YOUR_LAPTOP_IP>:3000.

You must edit pwa_frontend/app.js to point to this IP. Find the fetch call (around line 55) and change it from localhost:8080 to <YOUR_LAPTOP_IP>:8080.

External Access (From Anywhere)

This is the recommended setup.

Look at your ngrok http 3000 terminal. It will give you a public URL:

https://random-string-1.ngrok-free.app

Look at your ngrok http 8080 terminal. It will give you a different public URL:

https://random-string-2.ngrok-free.app

Edit pwa_frontend/app.js one time. Change line 55 to use your Rust backend's ngrok URL:

// BEFORE
// const response = await fetch("http://localhost:8080/api/council", {

// AFTER
const response = await fetch("[https://random-string-2.ngrok-free.app/api/council](https://random-string-2.ngrok-free.app/api/council)", {


Save the file. Your Python server will auto-reload.

On your phone, open your browser and go to the frontend URL (https://random-string-1.ngrok-free.app). You can now access your home AI from anywhere in the world.

The "Kill Switch"

When you are done, run the stop command from your server_manager folder. This will find and kill all 6 processes.

python3 manager.py stop


License

This project is licensed under the MIT License.
