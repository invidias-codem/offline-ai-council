use axum::{
    http::StatusCode, 
    Json,
    routing::post, 
    Router
};
use futures::future::join_all;
use reqwest::Client;
use serde::{Deserialize, Serialize};
use std::net::SocketAddr;
use tokio;
use tower_http::cors::{Any, CorsLayer}; // NEW: Import the CORS utilities

// --- Structs for JSON data ---
#[derive(Deserialize)]
struct CouncilRequest {
    query: String,
}
#[derive(Serialize)]
struct CouncilResponse {
    final_answer: String,
    model_answers: Vec<ModelAnswer>,
}
#[derive(Serialize, Clone)]
struct ModelAnswer {
    model: String,
    answer: String,
}

// --- Structs for Ollama ---
#[derive(Serialize)]
struct OllamaOptions {
    num_ctx: i32,
}

#[derive(Serialize)]
struct OllamaRequest {
    model: String,
    prompt: String,
    stream: bool,
    options: OllamaOptions,
}

#[derive(Deserialize)]
struct OllamaResponse {
    response: String,
}

// --- Main Server ---
#[tokio::main]
async fn main() {
    // NEW: Define your CORS layer
    // This is a permissive setup for local development.
    let cors = CorsLayer::new()
        .allow_origin(Any) // Allows any origin
        .allow_methods(Any) // Allows any method (GET, POST, etc.)
        .allow_headers(Any); // Allows any header

    // Build the app
    let app = Router::new()
        .route("/api/council", post(handle_council_request))
        .layer(cors); // NEW: Apply the CORS layer to your app

    let addr = SocketAddr::from(([127, 0, 0, 1], 8080));
    println!("🦀 Rust council server listening on {}", addr);

    let listener = tokio::net::TcpListener::bind(addr).await.unwrap();
    axum::serve(listener, app).await.unwrap();
}

// --- The "Council" Handler ---
async fn handle_council_request(
    Json(payload): Json<CouncilRequest>,
) -> (StatusCode, Json<CouncilResponse>) {
    
    let client = Client::new();
    
    let models_to_query = vec![
        ("tinyllama", "http://localhost:11434"),
        ("tinyllama", "http://localhost:11434"),
    ];

    let mut tasks = Vec::new();

    for (model_name, ollama_host) in models_to_query {
        let client = client.clone();
        let prompt = payload.query.clone(); 
        
        tasks.push(tokio::spawn(async move {
            query_model(client, model_name, &prompt, ollama_host).await
        }));
    }

    let results = join_all(tasks).await;

    let mut model_answers = Vec::new();
    for result in results {
        match result {
            Ok(Ok(answer)) => model_answers.push(answer),
            Ok(Err(e)) => model_answers.push(ModelAnswer {
                model: "Error".to_string(),
                answer: e.to_string(),
            }),
            Err(e) => println!("Tokio task error: {}", e),
        }
    }

    let mut final_answer = String::new();
    for ans in &model_answers {
        final_answer.push_str(&format!("[Answer from {}]: {}\n\n", ans.model, ans.answer));
    }
    
    let response = CouncilResponse {
        final_answer,
        model_answers,
    };

    (StatusCode::OK, Json(response))
}

// Helper function to call a single Ollama instance
async fn query_model(
    client: Client,
    model: &str,
    prompt: &str,
    host: &str,
) -> Result<ModelAnswer, String> {
    
    let ollama_req = OllamaRequest {
        model: model.to_string(),
        prompt: prompt.to_string(),
        stream: false,
        options: OllamaOptions { num_ctx: 1024 }, 
    };
    
    let url = format!("{}/api/generate", host);

    match client.post(&url).json(&ollama_req).send().await {
        Ok(res) => match res.json::<OllamaResponse>().await {
            Ok(json_res) => Ok(ModelAnswer {
                model: model.to_string(),
                answer: json_res.response,
            }),
            Err(e) => Err(format!("Failed to parse Ollama JSON: {}", e)),
        },
        Err(e) => Err(format!("Failed to contact Ollama: {}", e)),
    }
}