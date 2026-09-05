import argparse
import os
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader

# Import the model architecture defined in Step 3
from model import TemperatureForecastNet

def parse_args():
    parser = argparse.ArgumentParser()
    # Hyperparameters sent by SageMaker
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=0.001)
    
    # SageMaker container environment paths
    parser.add_argument("--model-dir", type=str, default=os.environ.get("SM_MODEL_DIR", "./model_output"))
    parser.add_argument("--train", type=str, default=os.environ.get("SM_CHANNEL_TRAIN", "./data"))
    parser.add_argument("--val", type=str, default=os.environ.get("SM_CHANNEL_VAL", "./data"))
    
    return parser.parse_args()

def load_data(data_dir, split="train"):
    # Supports both flat local testing and SageMaker channel subdirectories
    prefix = f"{data_dir}/" if os.path.exists(f"{data_dir}/X_{split}.npy") else f"{data_dir}/{split}/"
    X = np.load(f"{prefix}X_{split}.npy")
    y = np.load(f"{prefix}y_{split}.npy")
    return torch.tensor(X, dtype=torch.float32), torch.tensor(y, dtype=torch.float32)

def train():
    args = parse_args()
    os.makedirs(args.model_dir, exist_ok=True)
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using compute device: {device}")
    
    # 1. Prepare Datasets & Loaders
    X_train, y_train = load_data(args.train, split="train")
    X_val, y_val = load_data(args.val, split="val")
    
    train_loader = DataLoader(TensorDataset(X_train, y_train), batch_size=args.batch_size, shuffle=True)
    val_loader = DataLoader(TensorDataset(X_val, y_val), batch_size=args.batch_size, shuffle=False)
    
    # 2. Instantiate Model, Loss Function, and Optimizer
    model = TemperatureForecastNet().to(device)
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)
    
    print(f"\nStarting training: {args.epochs} epochs | Batch size: {args.batch_size} | Learning rate: {args.lr}")
    print("-" * 60)
    
    for epoch in range(1, args.epochs + 1):
        model.train()
        total_train_loss = 0.0
        
        for batch_X, batch_y in train_loader:
            batch_X, batch_y = batch_X.to(device), batch_y.to(device)
            
            optimizer.zero_grad()
            predictions = model(batch_X)
            loss = criterion(predictions, batch_y)
            loss.backward()
            optimizer.step()
            
            total_train_loss += loss.item() * batch_X.size(0)
            
        avg_train_loss = total_train_loss / len(train_loader.dataset)
        
        # Validation evaluation
        model.eval()
        total_val_loss = 0.0
        with torch.no_grad():
            for batch_X, batch_y in val_loader:
                batch_X, batch_y = batch_X.to(device), batch_y.to(device)
                val_preds = model(batch_X)
                val_loss = criterion(val_preds, batch_y)
                total_val_loss += val_loss.item() * batch_X.size(0)
                
        avg_val_loss = total_val_loss / len(val_loader.dataset)
        print(f"Epoch [{epoch:02d}/{args.epochs:02d}] | Train MSE: {avg_train_loss:.4f} | Val MSE: {avg_val_loss:.4f}")
    
    # 3. Save weights only (state_dict) to model_dir
    weights_path = os.path.join(args.model_dir, "model.pth")
    torch.save(model.state_dict(), weights_path)
    print("-" * 60)
    print(f"Training complete. Weights cleanly saved to: {weights_path}")

if __name__ == "__main__":
    train()
