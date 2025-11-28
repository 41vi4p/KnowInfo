#!/bin/bash

# Setup script for Ollama models

echo "Setting up Ollama models for KnowInfo..."

# Pull embedding model
echo "Pulling nomic-embed-text (for embeddings)..."
ollama pull nomic-embed-text

# Pull LLaMA 3.2 for text generation
echo "Pulling llama3.2 (for claim extraction and verification)..."
ollama pull llama3.2

echo "Ollama models ready!"
echo "You can verify with: ollama list"
