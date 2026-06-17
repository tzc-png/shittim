import torch
from transformers import HubertModel, Wav2Vec2FeatureExtractor

cnhubert_base_path = ""

class CNHubert(torch.nn.Module):
    def __init__(self, base_path: str):
        super().__init__()
        self.model = HubertModel.from_pretrained(base_path)
        self.feature_extractor = Wav2Vec2FeatureExtractor.from_pretrained(base_path)

    def forward(self, x):
        return self.model(x)

def get_model():
    assert cnhubert_base_path, "请先设置 cnhubert_base_path"
    model = CNHubert(cnhubert_base_path)
    model.eval()
    return model
