import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from torch.utils.data import DataLoader, TensorDataset
import os

# Define input/output paths
DATA_DIR = './preprocessed'
MODEL_OUT = './unet3d_kidney.pth'
BEST_MODEL_OUT = './unet3d_kidney_best.pth'
X_PATH = os.path.join(DATA_DIR, 'X.npy')
Y_PATH = os.path.join(DATA_DIR, 'Y.npy')

# Define model
class UNet3D(nn.Module):
    def __init__(self):
        super(UNet3D, self).__init__()
        def conv_block(in_channels, out_channels):
            return nn.Sequential(
                nn.Conv3d(in_channels, out_channels, kernel_size=3, padding=1),
                nn.BatchNorm3d(out_channels),
                nn.ReLU(inplace=True),
                nn.Conv3d(out_channels, out_channels, kernel_size=3, padding=1),
                nn.BatchNorm3d(out_channels),
                nn.ReLU(inplace=True)
            )

        self.enc1 = conv_block(1, 32)
        self.pool1 = nn.MaxPool3d(2)
        self.enc2 = conv_block(32, 64)
        self.pool2 = nn.MaxPool3d(2)

        self.bottleneck = conv_block(64, 128)

        self.up2 = nn.ConvTranspose3d(128, 64, kernel_size=2, stride=2)
        self.dec2 = conv_block(128, 64)
        self.up1 = nn.ConvTranspose3d(64, 32, kernel_size=2, stride=2)
        self.dec1 = conv_block(64, 32)

        self.final = nn.Conv3d(32, 1, kernel_size=1)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        enc1 = self.enc1(x)
        enc2 = self.enc2(self.pool1(enc1))
        bottleneck = self.bottleneck(self.pool2(enc2))
        up2 = self.up2(bottleneck)
        dec2 = self.dec2(torch.cat([up2, enc2], dim=1))
        up1 = self.up1(dec2)
        dec1 = self.dec1(torch.cat([up1, enc1], dim=1))
        return self.sigmoid(self.final(dec1))

# Dice loss
class DiceLoss(nn.Module):
    def __init__(self):
        super(DiceLoss, self).__init__()

    def forward(self, inputs, targets, smooth=1.0):
        inputs = inputs.contiguous().view(inputs.size(0), -1)
        targets = targets.contiguous().view(targets.size(0), -1)
        intersection = (inputs * targets).sum(dim=1)
        dice = (2. * intersection + smooth) / (inputs.sum(dim=1) + targets.sum(dim=1) + smooth)
        return 1 - dice.mean()

# Load and preprocess data
X = np.load(X_PATH)  # (N, 1, 64, 64, 64)
Y = np.load(Y_PATH)  # (N, 2, 64, 64, 64)

# Normalize inputs
X = (X - X.min()) / (X.max() - X.min() + 1e-8)

# Merge channel masks
y_merged = np.logical_or(Y[:, 0], Y[:, 1]).astype(np.float32)
y_merged = y_merged[:, np.newaxis, ...]

X_tensor = torch.tensor(X, dtype=torch.float32)
Y_tensor = torch.tensor(y_merged, dtype=torch.float32)

train_dataset = TensorDataset(X_tensor, Y_tensor)
train_loader = DataLoader(train_dataset, batch_size=2, shuffle=True)

# Initialize model
model = UNet3D()
bce = nn.BCELoss()
dice = DiceLoss()
optimizer = optim.Adam(model.parameters(), lr=1e-4)

# Resume training if model exists
if os.path.exists(MODEL_OUT):
    choice = input("⚠️ Model weights found. Resume training? (y/n): ").strip().lower()
    if choice == 'y':
        model.load_state_dict(torch.load(MODEL_OUT))
        print("✅ Loaded existing model weights.")
    else:
        print("🆕 Starting training from scratch.")
else:
    print("🆕 No existing model found. Training from scratch.")

# Training loop
num_epochs = 100
best_loss = float('inf')
model.train()

for epoch in range(num_epochs):
    epoch_loss = 0
    epoch_bce = 0
    epoch_dice = 0

    for batch_x, batch_y in train_loader:
        optimizer.zero_grad()
        output = model(batch_x)
        loss_bce = bce(output, batch_y)
        loss_dice = dice(output, batch_y)
        loss = 0.5 * loss_bce + 0.5 * loss_dice
        loss.backward()
        optimizer.step()

        epoch_loss += loss.item()
        epoch_bce += loss_bce.item()
        epoch_dice += loss_dice.item()

    avg_loss = epoch_loss / len(train_loader)
    avg_bce = epoch_bce / len(train_loader)
    avg_dice = epoch_dice / len(train_loader)

    print(f"📈 Epoch {epoch+1:02d}/{num_epochs} | Total Loss: {avg_loss:.4f} | BCE: {avg_bce:.4f} | Dice: {avg_dice:.4f}")

    # Save best model
    if avg_loss < best_loss:
        best_loss = avg_loss
        torch.save(model.state_dict(), BEST_MODEL_OUT)
        print(f"💾 Best model saved to {BEST_MODEL_OUT}")

# Save final model
torch.save(model.state_dict(), MODEL_OUT)
print(f"💾 Final model saved to {MODEL_OUT}")
