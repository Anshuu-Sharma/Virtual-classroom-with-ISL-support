"""
LSTM Seq2Seq Translation Model
Lightweight model for English-to-ISL translation
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import logging

logger = logging.getLogger(__name__)


class Encoder(nn.Module):
    """LSTM Encoder for English sentences"""
    
    def __init__(self, vocab_size: int, embed_dim: int, hidden_dim: int, 
                 num_layers: int, dropout: float = 0.3):
        super(Encoder, self).__init__()
        
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        
        # Embedding layer
        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=0)
        
        # LSTM layer
        self.lstm = nn.LSTM(
            embed_dim, 
            hidden_dim, 
            num_layers, 
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0,
            bidirectional=True
        )
        
        # Projection layer for bidirectional LSTM
        self.projection = nn.Linear(hidden_dim * 2, hidden_dim)
    
    def forward(self, x):
        """
        Forward pass
        
        Args:
            x: Input tensor (batch_size, seq_len)
            
        Returns:
            hidden: Hidden state (num_layers, batch_size, hidden_dim)
            cell: Cell state (num_layers, batch_size, hidden_dim)
        """
        # Embedding
        embedded = self.embedding(x)  # (batch_size, seq_len, embed_dim)
        
        # LSTM
        lstm_out, (hidden, cell) = self.lstm(embedded)
        
        # Combine bidirectional hidden states
        # hidden: (num_layers * 2, batch_size, hidden_dim)
        batch_size = hidden.size(1)
        hidden = hidden.view(self.num_layers, 2, batch_size, self.hidden_dim)
        hidden = torch.cat([hidden[:, 0, :, :], hidden[:, 1, :, :]], dim=2)
        hidden = self.projection(hidden)  # (num_layers, batch_size, hidden_dim)
        
        # Same for cell state
        cell = cell.view(self.num_layers, 2, batch_size, self.hidden_dim)
        cell = torch.cat([cell[:, 0, :, :], cell[:, 1, :, :]], dim=2)
        cell = self.projection(cell)
        
        return hidden, cell


class Decoder(nn.Module):
    """LSTM Decoder for ISL generation"""
    
    def __init__(self, vocab_size: int, embed_dim: int, hidden_dim: int,
                 num_layers: int, dropout: float = 0.3):
        super(Decoder, self).__init__()
        
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        
        # Embedding layer
        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=0)
        
        # LSTM layer
        self.lstm = nn.LSTM(
            embed_dim,
            hidden_dim,
            num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0
        )
        
        # Output projection
        self.fc_out = nn.Linear(hidden_dim, vocab_size)
        self.dropout = nn.Dropout(dropout)
    
    def forward(self, x, hidden, cell):
        """
        Forward pass
        
        Args:
            x: Input tensor (batch_size, 1)
            hidden: Hidden state (num_layers, batch_size, hidden_dim)
            cell: Cell state (num_layers, batch_size, hidden_dim)
            
        Returns:
            output: Output logits (batch_size, vocab_size)
            hidden: Updated hidden state
            cell: Updated cell state
        """
        # Embedding
        embedded = self.embedding(x)  # (batch_size, 1, embed_dim)
        embedded = self.dropout(embedded)
        
        # LSTM
        lstm_out, (hidden, cell) = self.lstm(embedded, (hidden, cell))
        
        # Output projection
        output = self.fc_out(lstm_out.squeeze(1))  # (batch_size, vocab_size)
        
        return output, hidden, cell


class Seq2SeqTranslator(nn.Module):
    """Complete Seq2Seq model for translation"""
    
    def __init__(self, src_vocab_size: int, tgt_vocab_size: int,
                 embed_dim: int = 256, hidden_dim: int = 512,
                 num_layers: int = 2, dropout: float = 0.3):
        super(Seq2SeqTranslator, self).__init__()
        
        self.encoder = Encoder(src_vocab_size, embed_dim, hidden_dim, num_layers, dropout)
        self.decoder = Decoder(tgt_vocab_size, embed_dim, hidden_dim, num_layers, dropout)
        
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
    
    def forward(self, src, tgt, teacher_forcing_ratio: float = 0.5):
        """
        Forward pass
        
        Args:
            src: Source sequence (batch_size, src_len)
            tgt: Target sequence (batch_size, tgt_len)
            teacher_forcing_ratio: Probability of using teacher forcing
            
        Returns:
            outputs: Output logits (batch_size, tgt_len, tgt_vocab_size)
        """
        batch_size = src.size(0)
        tgt_len = tgt.size(1)
        tgt_vocab_size = self.decoder.fc_out.out_features
        
        # Encoder forward pass
        hidden, cell = self.encoder(src)
        
        # Initialize decoder input with <sos> token
        decoder_input = tgt[:, 0].unsqueeze(1)  # (batch_size, 1)
        
        # Store outputs
        outputs = torch.zeros(batch_size, tgt_len, tgt_vocab_size).to(src.device)
        
        # Decoder forward pass
        for t in range(1, tgt_len):
            output, hidden, cell = self.decoder(decoder_input, hidden, cell)
            outputs[:, t, :] = output
            
            # Teacher forcing
            use_teacher_forcing = torch.rand(1).item() < teacher_forcing_ratio
            if use_teacher_forcing and self.training:
                decoder_input = tgt[:, t].unsqueeze(1)
            else:
                decoder_input = output.argmax(dim=1).unsqueeze(1)
        
        return outputs
    
    def translate(self, src, max_length: int = 100, sos_idx: int = 2, eos_idx: int = 3):
        """
        Translate source sequence to target
        
        Args:
            src: Source sequence (1, src_len)
            max_length: Maximum output length
            sos_idx: Start-of-sequence token index
            eos_idx: End-of-sequence token index
            
        Returns:
            Translated sequence (list of indices)
        """
        self.eval()
        with torch.no_grad():
            # Encoder
            hidden, cell = self.encoder(src)
            
            # Initialize decoder
            decoder_input = torch.tensor([[sos_idx]]).to(src.device)
            output_seq = []
            
            # Decode
            for _ in range(max_length):
                output, hidden, cell = self.decoder(decoder_input, hidden, cell)
                predicted_idx = output.argmax(dim=1).item()
                output_seq.append(predicted_idx)
                
                if predicted_idx == eos_idx:
                    break
                
                decoder_input = torch.tensor([[predicted_idx]]).to(src.device)
            
            return output_seq

