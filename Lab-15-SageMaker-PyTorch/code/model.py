import torch
import torch.nn as nn

class TemperatureForecastNet(nn.Module):
    def __init__(self, input_dim=5, hidden_dim=64, num_layers=2, dropout=0.2):
        super().__init__()
        
        # 1. Recurrent layer: processes sequential time steps
        self.lstm = nn.LSTM(
            input_size=input_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,    # Expected tensor shape: (batch, seq_len, features)
            dropout=dropout if num_layers > 1 else 0
        )
        
        # 2. Regression head: translates the final hidden state into a temperature value
        self.fc_block = nn.Sequential(
            nn.Linear(hidden_dim, 32),
            nn.LayerNorm(32),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(32, 1)     # Single continuous output: next-day T_max
        )

    def forward(self, x):
        # x shape: (batch_size, 7, 5)
        lstm_out, _ = self.lstm(x)
        
        # Slice out the final time step's hidden vector: shape (batch_size, 64)
        last_time_step_hidden = lstm_out[:, -1, :]
        
        # Pass through regression head: shape (batch_size, 1)
        prediction = self.fc_block(last_time_step_hidden)
        return prediction

if __name__ == "__main__":
    # Smoke-test: pass a dummy batch of 4 samples through the network
    dummy_input = torch.randn(4, 7, 5)
    model = TemperatureForecastNet()
    output = model(dummy_input)
    
    print("=== MODEL SMOKE TEST ===")
    print(f"Input Shape:  {dummy_input.shape}  -> 4 batches, 7 days, 5 weather features")
    print(f"Output Shape: {output.shape}        -> 4 predicted temperatures")
    print("Forward pass executed successfully.")
