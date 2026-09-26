# Inference Component Developer Documentation

## Overview
The `inference` module manages interactions with large language models (specifically local SLMs via Ollama) to evaluate job descriptions against the user's criteria.

## Responsibilities
- Construct and manage prompts for job evaluation.
- Communicate with the local Ollama API.
- Parse and validate the output from the language model to ensure it meets expected schemas.
- Implement safeguards and fallback mechanisms for model hallucinations or malformed JSON.

## Key Files & Modules
- `client.py`: The main client wrapper for interacting with the Ollama service, handling network requests, and managing timeouts/retries.
- `prompts.py`: Contains the system and user prompt templates used for evaluating job descriptions. Uses variables to inject job details and user criteria.
- `output_guard.py`: Responsible for parsing the raw text response from the model, extracting structured data (JSON), and validating it against `models.schemas`.

## Architecture & Interactions
- Called by the `core` pipeline during the evaluation phase.
- Uses `models` schemas to enforce output structure.
- Communicates externally with the locally running Ollama instance.
