import boto3
import json

agent_client = boto3.client('bedrock-agent-runtime', region_name='us-east-1')
runtime_client = boto3.client('bedrock-runtime', region_name='us-east-1')

KNOWLEDGE_BASE_ID = "CJAQHNOSXG"
MODEL_ID = "amazon.nova-micro-v1:0"

query = (
    "Surface temperatures on the tarmac have reached 105°F. "
    "What are the mandatory ramp safety hydration intervals and takeoff roll adjustments according to our SOPs?"
)

print(f"1. Querying Knowledge Base [{KNOWLEDGE_BASE_ID}] for document chunks...\n")

# Step 1: Semantic Retrieval (using server-side defaults)
retrieval_response = agent_client.retrieve(
    knowledgeBaseId=KNOWLEDGE_BASE_ID,
    retrievalQuery={'text': query}
)

retrieved_results = retrieval_response.get('retrievalResults', [])
context_text = ""
citations = []

print("="*80)
print("[RETRIEVED DOCUMENT CHUNKS]:")
print("="*80)
for i, result in enumerate(retrieved_results, 1):
    uri = result.get('location', {}).get('s3Location', {}).get('uri', 'Unknown')
    snippet = result.get('content', {}).get('text', '').strip()
    score = result.get('score', 0)
    citations.append(uri)
    context_text += f"\n--- Document Chunk [{i}] ({uri}) ---\n{snippet}\n"
    print(f"[{i}] Source: {uri} (Relevance Score: {score:.3f})")
    print(f"    Snippet: {snippet[:160]}...\n")

# Step 2: Grounded Generation via Bedrock Converse API
print("2. Generating grounded advisory with Amazon Nova Micro...")

prompt = f"""You are an automated meteorological decision advisor for NOAA. Answer the operational question using ONLY the provided document context below. If the context does not contain the answer, say so. Explicitly cite the specific SOP and protocol rules in your response.

<context>
{context_text}
</context>

Question: {query}
"""

response = runtime_client.converse(
    modelId=MODEL_ID,
    messages=[
        {
            "role": "user",
            "content": [{"text": prompt}]
        }
    ],
    inferenceConfig={
        "maxTokens": 400,
        "temperature": 0.1
    }
)

grounded_answer = response['output']['message']['content'][0]['text']

print("\n" + "="*80)
print("[GROUNDED AI ADVISORY]:")
print("="*80)
print(grounded_answer)
print("\n[VERIFIED SOURCE CITATIONS]:")
for uri in sorted(set(citations)):
    print(f"• {uri}")
