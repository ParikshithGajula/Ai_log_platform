import os
import asyncio
from dotenv import load_dotenv
from openai import OpenAI
import faiss
import numpy as np
import json

class AIAnalyzer:
    def __init__(self):
        load_dotenv()  # Load environment variables from .env file
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.index = None
        self.id_map = {}

    async def generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for a list of text inputs.
        """
        batches = [texts[i:i+100] for i in range(0, len(texts), 100)]
        total_batches = len(batches)
        embeddings = []

        for i, batch in enumerate(batches):
            response = self.client.embeddings.create(
                model="text-embedding-3-small",
                input=batch
            )
            batch_embeddings = [item.embedding for item in response.data]
            embeddings.extend(batch_embeddings)
            print(f"Embedded batch {i+1}/{total_batches}...")

        return embeddings

    def build_faiss_index(self, embeddings, log_ids: list[str]):
        """
        Build a FAISS index for efficient similarity search.
        """
        # Create FAISS index with 1536 dimensions (matches text-embedding-3-small)
        index = faiss.IndexFlatIP(1536)
        np_array = np.array(embeddings, dtype=np.float32)
        index.add(np_array)
        self.index = index
        self.id_map = {i: log_id for i, log_id in enumerate(log_ids)}

    async def search_similar(self, query: str, k=5) -> list[str]:
        """
        Find the top k most similar log entries to the given query.
        """
        # Generate query embedding
        response = self.client.embeddings.create(
            model="text-embedding-3-small",
            input=[query]
        )
        query_embedding = np.array([response.data[0].embedding], dtype=np.float32)

        if self.index is None:
            return []

        # Search for nearest neighbors
        distances, indices = self.index.search(query_embedding, k)

        # Extract corresponding log IDs
        log_ids = [self.id_map[i] for i in indices[0]]
        return log_ids

    async def analyze_root_cause(self, logs):
        """
        Analyze logs using GPT-3.5 to determine root cause and provide solutions.
        """
        # Format logs into a string for the model
        formatted_logs = "\n\n".join([
            f"Log {i+1}:\n{log}"
            for i, log in enumerate(logs[:5])  # Use top 5 logs
        ])

        # Prepare the prompt
        prompt = f"""
        You are a system analyst. Analyze the following logs to determine the root cause of an issue.
        Provide a structured response in JSON format with the following keys:
        - cause: the root cause of the issue
        - impact: the impact of the issue
        - solution: the recommended solution

        Logs:
        {formatted_logs}
        """

        # Call the GPT-3.5 model
        response = self.client.completions.create(
            model="gpt-3.5-turbo-instruct",
            prompt=prompt,
            max_tokens=500,
            temperature=0.7
        )

        # Parse the response
        try:
            analysis = json.loads(response.choices[0].text.strip())
        except json.JSONDecodeError:
            analysis = {
                "cause": "Unable to determine root cause",
                "impact": "Analysis failed",
                "solution": "Review logs manually"
            }

        return analysis
