import os
import json
import torch
from model import TemperatureForecastNet

def model_fn(model_dir):
    """1. Load model weights from disk into memory."""
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = TemperatureForecastNet()
    
    weights_path = os.path.join(model_dir, "model.pth")
    if not os.path.exists(weights_path):
        raise FileNotFoundError(f"Model file not found at {weights_path}")
        
    model.load_state_dict(torch.load(weights_path, map_location=device))
    model.to(device)
    model.eval()
    return model

def input_fn(request_body, request_content_type):
    """2. Deserialize input JSON into a PyTorch tensor of shape (batch, 7, 5)."""
    if request_content_type == "application/json":
        data = json.loads(request_body)
        tensor_data = torch.tensor(data["instances"], dtype=torch.float32)
        return tensor_data
    raise ValueError(f"Unsupported content type: {request_content_type}")

def predict_fn(input_data, model):
    """3. Run forward inference without computing gradients."""
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    input_data = input_data.to(device)
    
    with torch.no_grad():
        prediction = model(input_data)
    return prediction

def output_fn(prediction, content_type):
    """4. Format the output tensor into a clean JSON response."""
    if content_type == "application/json":
        # view(-1) flattens to a 1D tensor, ensuring .tolist() is always an iterable list
        preds = prediction.view(-1).tolist()
        response = {
            "predicted_t_max": [round(float(val), 2) for val in preds]
        }
        return json.dumps(response)
    raise ValueError(f"Unsupported accept type: {content_type}")

if __name__ == "__main__":
    # Local Smoke Test: verify the 4 functions end-to-end
    print("Testing inference handlers locally...")
    test_model = model_fn("./local_model_test")
    
    # Mock payload: 1 sample sequence of 7 days × 5 normalized features
    mock_payload = json.dumps({
        "instances": [[[0.1, 0.2, -0.1, 1.0, -0.5] for _ in range(7)]]
    })
    
    tensor_in = input_fn(mock_payload, "application/json")
    pred_raw = predict_fn(tensor_in, test_model)
    json_out = output_fn(pred_raw, "application/json")
    
    print("\n=== INFERENCE SMOKE TEST RESULT ===")
    print(f"Input Tensor Shape:  {tensor_in.shape}")
    print(f"Output JSON Payload: {json_out}")
