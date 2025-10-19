# 🔒 Privox AI – Privacy-First Dual-Mode Voice Assistant (NLP)

**Project Status:** Currently in the Architecture & Proof-of-Concept (POC) Development Phase.

---

## 💡 Abstract

Privox AI is a privacy-first dual mode intelligent voice assistant that puts users fully in control of their data. It combines on-device processing with secure, end-to-end encrypted online communication to prevent data leakage and misuse. Key features include wake-word activation, local chat storage, and Zero Trace Mode for instant data wipe. The system ensures no raw audio or sensitive metadata is ever stored or leaked, delivering a trustworthy user experience. The final prototype will demonstrate dual-mode operation, real-time responses, and privacy-by-design interactions, proving AI can be both powerful and ethical.

---

## 🎯 Problem Statement: The Privacy Crisis

Commercial voice assistants create a privacy crisis through three main issues:

1.  **Data Surveillance:** Devices continuously collect and analyze personal conversations to create detailed user profiles without explicit consent.
2.  **Always-On Listening:** Devices constantly monitor ambient audio, leading to accidental recordings and the potential for eavesdropping on private conversations.
3.  **Loss of Control:** Users have minimal visibility and control over how their personal data is processed, stored, or utilized by corporations.

---

## 🏗️ Project Architecture & Workflow

The system is designed for seamless operation, prioritizing security at every step (Dual-Mode).

![Privox AI Workflow Diagram](Workflow_Diagram.png)

---

## 🛠️ Technology Stack (Defined for POC)

The system is built on a modular Python stack for the core AI pipeline, leveraging highly efficient existing models:

| Component / Tool Used | Purpose | Technology/Platform |
| :--- | :--- | :--- |
| **Core Logic** | Manages the dual-mode switching, data flow, and encryption. | **Python** |
| **Wake-Word Detection** | Always listens for the custom wake word (“Hello PriVox”). | Picovoice **Porcupine** (Lightweight ML model) |
| **Speech-to-Text (STT)** | Converts user voice into text locally. | **Whisper** (Offline Model) |
| **Offline AI Response** | Answers questions without internet access. | **Local LLM** (e.g., GPT4All / Mistral) |
| **Encryption** | Secures all data before online transmission. | **AES** (Advanced Encryption Standard) |
| **Frontend/Backend** | User interface and handling of API communication. | **React** (Frontend), **Node.js/Express** (Backend) |

---

## 📂 Repository Contents

| File/Folder | Purpose |
| :--- | :--- |
| `README.md` | **(You are here)** Project overview, problem statement, and high-level architecture. |
| `architecture/` | Detailed design documents and system requirements. |
| `src/` | Placeholder for Python Proof-of-Concept code (e.g., environment setup, initial component tests). |
| `requirements.txt` | Defines the specific Python dependencies for the AI pipeline. |

---

## 📚 Architectural Design Objectives

* **Privacy-First Architecture:** Ensure user data is fully under user control with no unauthorized storage or leakage.
* **Dual-Mode Operation:** Enable both offline processing and secure online mode for a seamless user experience.
* **End-to-End Encryption:** Implement AES for all online communications, preventing third-party data interception.
* **Zero Trace Mode:** Allow users to instantly clear session data and leave no digital footprint after use.

---
