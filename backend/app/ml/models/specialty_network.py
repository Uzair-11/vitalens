import torch
import torch.nn as nn

class VitaLensSpecialtyNet(nn.Module):
    """
    Multi-Layer Deep Neural Network for Medical Specialty Recommendation.
    Processes multi-modal input vectors:
      - TF-IDF symptom text embeddings (dim: 256)
      - Canonical biomarker numerical deviations & status flags (dim: 40)
      - Clinical severity & duration metadata (dim: 2)
    Total input dimension: 298 features -> 10 output specialty classes.
    """
    def __init__(
        self,
        input_dim: int = 298,
        num_classes: int = 10,
        hidden_dims: tuple = (256, 128, 64),
        dropout_rate: float = 0.25
    ):
        super(VitaLensSpecialtyNet, self).__init__()
        
        self.input_dim = input_dim
        self.num_classes = num_classes
        
        self.block1 = nn.Sequential(
            nn.Linear(input_dim, hidden_dims[0]),
            nn.BatchNorm1d(hidden_dims[0]),
            nn.ReLU(),
            nn.Dropout(dropout_rate)
        )
        
        self.block2 = nn.Sequential(
            nn.Linear(hidden_dims[0], hidden_dims[1]),
            nn.BatchNorm1d(hidden_dims[1]),
            nn.ReLU(),
            nn.Dropout(dropout_rate * 0.8)
        )
        
        self.block3 = nn.Sequential(
            nn.Linear(hidden_dims[1], hidden_dims[2]),
            nn.BatchNorm1d(hidden_dims[2]),
            nn.ReLU(),
            nn.Dropout(dropout_rate * 0.6)
        )
        
        self.classifier = nn.Linear(hidden_dims[2], num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        h1 = self.block1(x)
        h2 = self.block2(h1)
        h3 = self.block3(h2)
        logits = self.classifier(h3)
        return logits

    def predict_probabilities(self, x: torch.Tensor) -> torch.Tensor:
        """Returns softmax probability distribution over specialties."""
        self.eval()
        with torch.no_grad():
            logits = self.forward(x)
            probs = torch.softmax(logits, dim=-1)
        return probs
