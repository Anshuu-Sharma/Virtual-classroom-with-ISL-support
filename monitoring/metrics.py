"""
Performance metrics collection
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List


class MetricsCollector:
    """Collect and store performance metrics"""
    
    def __init__(self, metrics_file: str = "data/metrics.json"):
        self.metrics_file = Path(metrics_file)
        self.metrics_file.parent.mkdir(parents=True, exist_ok=True)
        self.metrics = []
    
    def record_metric(self, name: str, value: float, timestamp: datetime = None):
        """
        Record a metric
        
        Args:
            name: Metric name
            value: Metric value
            timestamp: Optional timestamp (default: now)
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        metric = {
            'name': name,
            'value': value,
            'timestamp': timestamp.isoformat()
        }
        
        self.metrics.append(metric)
        self._save_metrics()
    
    def record_batch(self, metrics: Dict[str, float]):
        """Record multiple metrics at once"""
        timestamp = datetime.now()
        for name, value in metrics.items():
            self.record_metric(name, value, timestamp)
    
    def get_latest_metrics(self) -> Dict[str, float]:
        """Get latest metric values"""
        latest = {}
        for metric in reversed(self.metrics):
            if metric['name'] not in latest:
                latest[metric['name']] = metric['value']
        return latest
    
    def get_metric_history(self, name: str) -> List[Dict]:
        """Get history for a specific metric"""
        return [m for m in self.metrics if m['name'] == name]
    
    def _save_metrics(self):
        """Save metrics to file"""
        with open(self.metrics_file, 'w') as f:
            json.dump(self.metrics, f, indent=2)
    
    def load_metrics(self):
        """Load metrics from file"""
        if self.metrics_file.exists():
            with open(self.metrics_file, 'r') as f:
                self.metrics = json.load(f)


# Global metrics collector instance
_metrics_collector = None

def get_metrics_collector() -> MetricsCollector:
    """Get or create metrics collector instance"""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
        _metrics_collector.load_metrics()
    return _metrics_collector

