"""
Complete Training Script for Kaggle
Copy this entire file into a Kaggle notebook and run it!

Setup:
1. Go to Kaggle → New Notebook
2. Settings → Accelerator → GPU T4 x2
3. Settings → Internet → ON
4. Add Data → Your dataset (isl-translation-dataset)
5. Copy-paste this entire script
6. Run
"""

# ============================================================================
# INSTALL DEPENDENCIES
# ============================================================================
import subprocess
import sys

print("Installing dependencies...")
subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "torch", "torchvision", "torchaudio"])
subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "tqdm"])

# ============================================================================
# IMPORTS
# ============================================================================
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import json
import numpy as np
from tqdm import tqdm
from collections import Counter
import os

print(f"\nPyTorch version: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"CUDA device: {torch.cuda.get_device_name(0)}")

# ============================================================================
# CONFIGURATION
# ============================================================================
config = {
    'EMBED_DIM': 256,
    'HIDDEN_DIM': 512,
    'NUM_LAYERS': 2,
    'DROPOUT': 0.3,
    'BATCH_SIZE': 64,
    'LEARNING_RATE': 0.001,
    'NUM_EPOCHS': 50,
    'MAX_LENGTH': 100,
    'MIN_FREQ': 1,
    'GRAD_CLIP': 5.0
}

# Update these paths to match your dataset
TRAIN_PATH = '/kaggle/input/isl-translation-dataset/train_pairs_enhanced.json'
VAL_PATH = '/kaggle/input/isl-translation-dataset/val_pairs_enhanced.json'

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"Using device: {device}\n")

# ============================================================================
# VOCABULARY CLASS
# ============================================================================
class Vocabulary:
    def __init__(self):
        self.word2idx = {'<pad>': 0, '<unk>': 1, '<sos>': 2, '<eos>': 3}
        self.idx2word = {0: '<pad>', 1: '<unk>', 2: '<sos>', 3: '<eos>'}
        self.word_counts = Counter()
    
    def add_word(self, word):
        if word not in self.word2idx:
            idx = len(self.word2idx)
            self.word2idx[word] = idx
            self.idx2word[idx] = word
    
    def add_words_from_text(self, text):
        words = text.lower().split()
        for word in words:
            self.word_counts[word] += 1
    
    def build_vocab(self, texts, min_freq=1):
        for text in texts:
            self.add_words_from_text(text)
        for word, count in self.word_counts.items():
            if count >= min_freq:
                self.add_word(word)
        print(f"Built vocabulary with {len(self.word2idx)} words")
    
    def encode(self, text, max_length=None):
        words = text.lower().split()
        indices = [self.word2idx.get(word, self.word2idx['<unk>']) for word in words]
        if max_length:
            if len(indices) > max_length:
                indices = indices[:max_length]
            else:
                indices = indices + [self.word2idx['<pad>']] * (max_length - len(indices))
        return indices
    
    def decode(self, indices):
        words = [self.idx2word.get(idx, '<unk>') for idx in indices]
        words = [w for w in words if w not in ['<pad>', '<sos>', '<eos>']]
        return ' '.join(words)
    
    def size(self):
        return len(self.word2idx)
    
    def save(self, filepath):
        with open(filepath, 'w') as f:
            json.dump({
                'word2idx': self.word2idx,
                'idx2word': {int(k): v for k, v in self.idx2word.items()}
            }, f, indent=2)
        print(f"Saved vocabulary to {filepath}")

# ============================================================================
# DATASET CLASS
# ============================================================================
class ISLDataset(Dataset):
    def __init__(self, data_path, src_vocab, tgt_vocab, max_length=100):
        self.src_vocab = src_vocab
        self.tgt_vocab = tgt_vocab
        self.max_length = max_length
        with open(data_path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
        print(f"Loaded {len(self.data)} translation pairs")
    
    def __len__(self):
        return len(self.data)
    
    def __getitem__(self, idx):
        item = self.data[idx]
        src_indices = self.src_vocab.encode(item['english'], max_length=self.max_length)
        tgt_indices = self.tgt_vocab.encode(item['isl'], max_length=self.max_length)
        return torch.tensor(src_indices, dtype=torch.long), torch.tensor(tgt_indices, dtype=torch.long)

# ============================================================================
# MODEL ARCHITECTURE
# ============================================================================
class Encoder(nn.Module):
    def __init__(self, vocab_size, embed_dim, hidden_dim, num_layers, dropout=0.3):
        super(Encoder, self).__init__()
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=0)
        self.lstm = nn.LSTM(embed_dim, hidden_dim, num_layers, batch_first=True,
                           dropout=dropout if num_layers > 1 else 0, bidirectional=True)
        self.projection = nn.Linear(hidden_dim * 2, hidden_dim)
    
    def forward(self, x):
        embedded = self.embedding(x)
        lstm_out, (hidden, cell) = self.lstm(embedded)
        batch_size = hidden.size(1)
        hidden = hidden.view(self.num_layers, 2, batch_size, self.hidden_dim)
        hidden = torch.cat([hidden[:, 0, :, :], hidden[:, 1, :, :]], dim=2)
        hidden = self.projection(hidden)
        cell = cell.view(self.num_layers, 2, batch_size, self.hidden_dim)
        cell = torch.cat([cell[:, 0, :, :], cell[:, 1, :, :]], dim=2)
        cell = self.projection(cell)
        return hidden, cell

class Decoder(nn.Module):
    def __init__(self, vocab_size, embed_dim, hidden_dim, num_layers, dropout=0.3):
        super(Decoder, self).__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=0)
        self.lstm = nn.LSTM(embed_dim, hidden_dim, num_layers, batch_first=True,
                           dropout=dropout if num_layers > 1 else 0)
        self.fc_out = nn.Linear(hidden_dim, vocab_size)
        self.dropout = nn.Dropout(dropout)
    
    def forward(self, x, hidden, cell):
        embedded = self.dropout(self.embedding(x))
        lstm_out, (hidden, cell) = self.lstm(embedded, (hidden, cell))
        output = self.fc_out(lstm_out.squeeze(1))
        return output, hidden, cell

class Seq2SeqTranslator(nn.Module):
    def __init__(self, src_vocab_size, tgt_vocab_size, embed_dim=256, hidden_dim=512, num_layers=2, dropout=0.3):
        super(Seq2SeqTranslator, self).__init__()
        self.encoder = Encoder(src_vocab_size, embed_dim, hidden_dim, num_layers, dropout)
        self.decoder = Decoder(tgt_vocab_size, embed_dim, hidden_dim, num_layers, dropout)
    
    def forward(self, src, tgt, teacher_forcing_ratio=0.5):
        batch_size, tgt_len = src.size(0), tgt.size(1)
        tgt_vocab_size = self.decoder.fc_out.out_features
        hidden, cell = self.encoder(src)
        decoder_input = tgt[:, 0].unsqueeze(1)
        outputs = torch.zeros(batch_size, tgt_len, tgt_vocab_size).to(src.device)
        for t in range(1, tgt_len):
            output, hidden, cell = self.decoder(decoder_input, hidden, cell)
            outputs[:, t, :] = output
            use_teacher_forcing = torch.rand(1).item() < teacher_forcing_ratio
            decoder_input = tgt[:, t].unsqueeze(1) if (use_teacher_forcing and self.training) else output.argmax(dim=1).unsqueeze(1)
        return outputs

# ============================================================================
# LOAD DATA
# ============================================================================
print("="*60)
print("LOADING DATA")
print("="*60)

with open(TRAIN_PATH, 'r', encoding='utf-8') as f:
    train_data = json.load(f)

print("\nBuilding vocabularies...")
src_vocab = Vocabulary()
tgt_vocab = Vocabulary()

src_texts = [item['english'] for item in train_data]
tgt_texts = [item['isl'] for item in train_data]

src_vocab.build_vocab(src_texts, min_freq=config['MIN_FREQ'])
tgt_vocab.build_vocab(tgt_texts, min_freq=config['MIN_FREQ'])

print(f"Source vocab size: {src_vocab.size()}")
print(f"Target vocab size: {tgt_vocab.size()}")

# ============================================================================
# CREATE DATASETS
# ============================================================================
print("\nCreating datasets...")
train_dataset = ISLDataset(TRAIN_PATH, src_vocab, tgt_vocab, config['MAX_LENGTH'])
val_dataset = ISLDataset(VAL_PATH, src_vocab, tgt_vocab, config['MAX_LENGTH'])

train_loader = DataLoader(train_dataset, batch_size=config['BATCH_SIZE'], shuffle=True, num_workers=2)
val_loader = DataLoader(val_dataset, batch_size=config['BATCH_SIZE'], shuffle=False, num_workers=2)

print(f"Training batches: {len(train_loader)}")
print(f"Validation batches: {len(val_loader)}")

# ============================================================================
# INITIALIZE MODEL
# ============================================================================
print("\n" + "="*60)
print("INITIALIZING MODEL")
print("="*60)

model = Seq2SeqTranslator(
    src_vocab_size=src_vocab.size(),
    tgt_vocab_size=tgt_vocab.size(),
    embed_dim=config['EMBED_DIM'],
    hidden_dim=config['HIDDEN_DIM'],
    num_layers=config['NUM_LAYERS'],
    dropout=config['DROPOUT']
).to(device)

total_params = sum(p.numel() for p in model.parameters())
print(f"Total parameters: {total_params:,}")

criterion = nn.CrossEntropyLoss(ignore_index=0)
optimizer = optim.Adam(model.parameters(), lr=config['LEARNING_RATE'])
scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=2)

# ============================================================================
# TRAINING FUNCTIONS
# ============================================================================
def train_epoch(model, train_loader, optimizer, criterion, device):
    model.train()
    total_loss = 0
    pbar = tqdm(train_loader, desc="Training")
    for src, tgt in pbar:
        src, tgt = src.to(device), tgt.to(device)
        optimizer.zero_grad()
        outputs = model(src, tgt, teacher_forcing_ratio=0.5)
        outputs = outputs[:, 1:].reshape(-1, outputs.size(-1))
        tgt = tgt[:, 1:].reshape(-1)
        loss = criterion(outputs, tgt)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), config['GRAD_CLIP'])
        optimizer.step()
        total_loss += loss.item()
        pbar.set_postfix({'loss': loss.item()})
    return total_loss / len(train_loader)

def validate(model, val_loader, criterion, device):
    model.eval()
    total_loss = 0
    with torch.no_grad():
        for src, tgt in val_loader:
            src, tgt = src.to(device), tgt.to(device)
            outputs = model(src, tgt, teacher_forcing_ratio=0.0)
            outputs = outputs[:, 1:].reshape(-1, outputs.size(-1))
            tgt = tgt[:, 1:].reshape(-1)
            loss = criterion(outputs, tgt)
            total_loss += loss.item()
    return total_loss / len(val_loader)

# ============================================================================
# TRAINING LOOP
# ============================================================================
print("\n" + "="*60)
print("STARTING TRAINING")
print("="*60)

best_val_loss = float('inf')
patience_counter = 0
patience = 5

for epoch in range(1, config['NUM_EPOCHS'] + 1):
    print(f"\nEpoch {epoch}/{config['NUM_EPOCHS']}")
    train_loss = train_epoch(model, train_loader, optimizer, criterion, device)
    val_loss = validate(model, val_loader, criterion, device)
    print(f"Train Loss: {train_loss:.4f} | Val Loss: {val_loss:.4f}")
    scheduler.step(val_loss)
    
    if val_loss < best_val_loss:
        best_val_loss = val_loss
        patience_counter = 0
        print(f"✅ Best model! Saving...")
        torch.save({
            'epoch': epoch,
            'model_state_dict': model.state_dict(),
            'optimizer_state_dict': optimizer.state_dict(),
            'train_loss': train_loss,
            'val_loss': val_loss,
            'config': config
        }, '/kaggle/working/lstm_translator.pth')
    else:
        patience_counter += 1
        if patience_counter >= patience:
            print(f"\nEarly stopping at epoch {epoch}")
            break

print("\n" + "="*60)
print("✅ TRAINING COMPLETE!")
print("="*60)
print(f"Best validation loss: {best_val_loss:.4f}")

# ============================================================================
# SAVE VOCABULARIES
# ============================================================================
print("\nSaving vocabularies...")
src_vocab.save('/kaggle/working/vocab_src.json')
tgt_vocab.save('/kaggle/working/vocab_tgt.json')

print("\n" + "="*60)
print("✅ ALL FILES SAVED!")
print("="*60)
print("\nDownload these files from Output tab:")
print("1. lstm_translator.pth")
print("2. vocab_src.json")
print("3. vocab_tgt.json")
print("="*60)

# ============================================================================
# TEST SAMPLE TRANSLATIONS
# ============================================================================
def translate_sentence(model, sentence, src_vocab, tgt_vocab, device, max_length=100):
    model.eval()
    with torch.no_grad():
        src_indices = src_vocab.encode(sentence, max_length=max_length)
        src_tensor = torch.tensor([src_indices], dtype=torch.long).to(device)
        hidden, cell = model.encoder(src_tensor)
        decoder_input = torch.tensor([[tgt_vocab.word2idx['<sos>']]], dtype=torch.long).to(device)
        output_seq = []
        for _ in range(max_length):
            output, hidden, cell = model.decoder(decoder_input, hidden, cell)
            predicted_idx = output.argmax(dim=1).item()
            output_seq.append(predicted_idx)
            if predicted_idx == tgt_vocab.word2idx.get('<eos>', 3):
                break
            decoder_input = torch.tensor([[predicted_idx]], dtype=torch.long).to(device)
        return tgt_vocab.decode(output_seq)

print("\nTesting translations:")
print("="*60)
test_sentences = [
    "<sos> hello how are you <eos>",
    "<sos> what is your name <eos>",
    "<sos> i am learning sign language <eos>",
    "<sos> thank you <eos>",
]

for sentence in test_sentences:
    eng = sentence.replace('<sos> ', '').replace(' <eos>', '')
    isl = translate_sentence(model, sentence, src_vocab, tgt_vocab, device)
    print(f"English: {eng}")
    print(f"ISL:     {isl}")
    print("-" * 60)

