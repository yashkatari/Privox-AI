# Privox AI: Detailed Architectural Design 

## 1. Design Philosophy

The system adheres to the **Privacy-by-Design** principle, ensuring privacy measures are foundational to the system architecture. Our goal is to counter the issues of Data Surveillance, Always-On Listening, and Loss of Control.

## 2. Dual-Mode Switching Logic

The core application logic (Python) is responsible for routing the user's request:

1.  **Input:** User speaks wake word (Porcupine) and query (Whisper converts to text).
2.  **Logic:** The Python core checks the query type:
    * **IF** query is *local* (e.g., "Set timer"): Route to **Offline AI**. Response is processed locally and spoken.
    * **IF** query is *online* (e.g., "What is the news?"): Route the text query to the **Node.js Backend**.
3.  **Online Processing:**
    * The Backend **AES Encrypts** the text payload.
    * The encrypted text is sent to the public API (Online AI).
    * The encrypted response is received, decrypted, and converted to speech.

## 3. Data and Security Model

* **Raw Audio:** Raw audio is processed on-device (Porcupine/Whisper) and is **never stored** or transmitted.
* **Chat History:** Conversational context and memory are stored using **Local JSON/MongoDB (Optional)** storage, keeping data off the cloud.
* **Zero Trace Mode:** A dedicated command will wipe all local chat history instantly.
* [cite_start]**Encryption:** The **AES** standard is implemented for all transmission across the network to secure data.

## 4. Initial Component Selection

Components were selected based on efficiency, local operation, and performance:

* **KWS:** Picovoice Porcupine (Highly accurate, minimal resource consumption, enabling on-device processing).
* **STT:** OpenAI Whisper (Proven accuracy in various environments).
* **Local LLM:** GPT4All / Mistral (Selected for ability to run locally for offline query responses).
