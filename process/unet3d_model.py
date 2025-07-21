import torch
import torch.nn as nn
import torch.nn.functional as F

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

    def forward(self, x):
        enc1 = self.enc1(x)
        enc2 = self.enc2(self.pool1(enc1))
        bottleneck = self.bottleneck(self.pool2(enc2))

        up2 = self.up2(bottleneck)
        dec2 = self.dec2(torch.cat([up2, enc2], dim=1))
        up1 = self.up1(dec2)
        dec1 = self.dec1(torch.cat([up1, enc1], dim=1))

        return torch.sigmoid(self.final(dec1))