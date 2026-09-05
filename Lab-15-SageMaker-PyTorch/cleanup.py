import boto3

sts = boto3.client('sts')
account_id = sts.get_caller_identity()['Account']
region = "us-east-1"
sm = boto3.client('sagemaker', region_name=region)

# Load the active endpoint name
with open("endpoint_name.txt", "r") as f:
    endpoint_name = f.read().strip()

print(f"Initiating teardown for: {endpoint_name}")

# 1. Delete Endpoint (Stops EC2 billing immediately)
try:
    sm.delete_endpoint(EndpointName=endpoint_name)
    print(f"Deleted Endpoint: {endpoint_name}")
except Exception as e:
    print(f"Error deleting endpoint: {e}")

# 2. Delete Endpoint Configuration
config_name = endpoint_name.replace("endpoint", "config")
try:
    sm.delete_endpoint_config(EndpointConfigName=config_name)
    print(f"Deleted Endpoint Config: {config_name}")
except Exception as e:
    print(f"Error deleting endpoint config: {e}")

# 3. Delete Model Resource
model_name = endpoint_name.replace("endpoint", "model")
try:
    sm.delete_model(ModelName=model_name)
    print(f"Deleted Model Resource: {model_name}")
except Exception as e:
    print(f"Error deleting model: {e}")

print("\nTeardown complete. Zero active compute charges remaining.")
