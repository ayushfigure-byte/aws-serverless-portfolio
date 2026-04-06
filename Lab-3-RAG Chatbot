import json
import boto3

# Initialize AWS SDK clients
dynamodb = boto3.resource('dynamodb')
bedrock = boto3.client('bedrock-runtime')

# Connect to the table from Lab 2
table = dynamodb.Table('ParsedDocuments')

def lambda_handler(event, context):
    try:
        # 1. Parse the incoming request (simulating an agent asking a question)
        body = json.loads(event['body'])
        document_id = body.get('document_id')
        user_question = body.get('question')
        
        # 2. Retrieve the parsed text from DynamoDB (The "Retrieval" in RAG)
        response = table.get_item(Key={'document_id': document_id})
        
        if 'Item' not in response:
            return {'statusCode': 404, 'body': json.dumps('Document not found in database.')}
            
        extracted_text = response['Item']['extracted_text']
        
        # 3. Construct the strict prompt for the AI
        prompt = f"""
        You are an internal corporate assistant. Answer the user's question using ONLY the document text provided below. 
        If the answer is not contained in the text, say "I cannot find this in the provided document." Do not guess.
        
        ---DOCUMENT TEXT---
        {extracted_text}
        
        ---USER QUESTION---
        {user_question}
        """
        
        # 4. Call Amazon Bedrock using the new Nova Micro model (The "Generation" in RAG)
        # Using a low temperature (0.1) so the AI stays strictly factual and doesn't get "creative"
        bedrock_response = bedrock.converse(
            modelId='amazon.nova-micro-v1:0',
            messages=[{'role': 'user', 'content': [{'text': prompt}]}],
            inferenceConfig={'temperature': 0.1} 
        )
        
        # 5. Extract the AI's answer
        ai_answer = bedrock_response['output']['message']['content'][0]['text']
        
        return {
            'statusCode': 200,
            'body': json.dumps({'answer': ai_answer})
        }
        
    except Exception as e:
        print(f"Error generating answer: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
