"""
Training script for LSTM Seq2Seq translation model
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
import logging
from tqdm import tqdm
import os
from pathlib import Path

from ml_pipeline.models.translator import Seq2SeqTranslator
from ml_pipeline.config import ModelConfig, TRAINING_CONFIG

logger = logging.getLogger(__name__)


class TranslationTrainer:
    """Trainer for translation model"""
    
    def __init__(self, model: Seq2SeqTranslator, config: ModelConfig):
        self.model = model
        self.config = config
        self.device = torch.device(config.DEVICE if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        
        # Loss and optimizer
        self.criterion = nn.CrossEntropyLoss(ignore_index=0)  # Ignore padding
        self.optimizer = optim.Adam(model.parameters(), lr=config.LEARNING_RATE)
        self.scheduler = optim.lr_scheduler.ReduceLROnPlateau(
            self.optimizer, mode='min', factor=0.5, patience=2
        )
        
        # Training history
        self.train_losses = []
        self.val_losses = []
        self.best_val_loss = float('inf')
        self.patience_counter = 0
    
    def train_epoch(self, train_loader: DataLoader, epoch: int):
        """Train for one epoch"""
        self.model.train()
        total_loss = 0
        
        pbar = tqdm(train_loader, desc=f"Epoch {epoch}")
        for batch_idx, (src, tgt) in enumerate(pbar):
            src = src.to(self.device)
            tgt = tgt.to(self.device)
            
            # Forward pass
            self.optimizer.zero_grad()
            outputs = self.model(src, tgt, teacher_forcing_ratio=0.5)
            
            # Reshape for loss calculation
            outputs = outputs[:, 1:].reshape(-1, outputs.size(-1))
            tgt = tgt[:, 1:].reshape(-1)
            
            # Calculate loss
            loss = self.criterion(outputs, tgt)
            
            # Backward pass
            loss.backward()
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), self.config.GRAD_CLIP)
            self.optimizer.step()
            
            total_loss += loss.item()
            
            # Update progress bar
            if batch_idx % TRAINING_CONFIG["log_interval"] == 0:
                pbar.set_postfix({'loss': loss.item()})
        
        avg_loss = total_loss / len(train_loader)
        self.train_losses.append(avg_loss)
        return avg_loss
    
    def validate(self, val_loader: DataLoader):
        """Validate model"""
        self.model.eval()
        total_loss = 0
        
        with torch.no_grad():
            for src, tgt in val_loader:
                src = src.to(self.device)
                tgt = tgt.to(self.device)
                
                outputs = self.model(src, tgt, teacher_forcing_ratio=0.0)
                
                outputs = outputs[:, 1:].reshape(-1, outputs.size(-1))
                tgt = tgt[:, 1:].reshape(-1)
                
                loss = self.criterion(outputs, tgt)
                total_loss += loss.item()
        
        avg_loss = total_loss / len(val_loader)
        self.val_losses.append(avg_loss)
        return avg_loss
    
    def save_checkpoint(self, filepath: str, epoch: int, loss: float):
        """Save model checkpoint"""
        checkpoint = {
            'epoch': epoch,
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'loss': loss,
            'train_losses': self.train_losses,
            'val_losses': self.val_losses
        }
        torch.save(checkpoint, filepath)
        logger.info(f"Saved checkpoint to {filepath}")
    
    def load_checkpoint(self, filepath: str):
        """Load model checkpoint"""
        checkpoint = torch.load(filepath, map_location=self.device)
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        self.train_losses = checkpoint.get('train_losses', [])
        self.val_losses = checkpoint.get('val_losses', [])
        logger.info(f"Loaded checkpoint from {filepath}")
        return checkpoint['epoch']
    
    def train(self, train_loader: DataLoader, val_loader: DataLoader):
        """Full training loop"""
        logger.info("Starting training...")
        
        for epoch in range(1, self.config.NUM_EPOCHS + 1):
            # Train
            train_loss = self.train_epoch(train_loader, epoch)
            
            # Validate
            if epoch % TRAINING_CONFIG["eval_interval"] == 0:
                val_loss = self.validate(val_loader)
                logger.info(f"Epoch {epoch}: Train Loss: {train_loss:.4f}, Val Loss: {val_loss:.4f}")
                
                # Learning rate scheduling
                self.scheduler.step(val_loss)
                
                # Save best model
                if val_loss < self.best_val_loss:
                    self.best_val_loss = val_loss
                    self.patience_counter = 0
                    if TRAINING_CONFIG["save_best_model"]:
                        self.save_checkpoint(self.config.MODEL_SAVE_PATH, epoch, val_loss)
                else:
                    self.patience_counter += 1
                
                # Early stopping
                if self.patience_counter >= TRAINING_CONFIG["early_stopping_patience"]:
                    logger.info(f"Early stopping at epoch {epoch}")
                    break
            
            # Save checkpoint
            if epoch % TRAINING_CONFIG["checkpoint_interval"] == 0:
                checkpoint_path = self.config.MODEL_SAVE_PATH.replace('.pth', f'_epoch_{epoch}.pth')
                self.save_checkpoint(checkpoint_path, epoch, train_loss)
        
        logger.info("Training completed!")

