"""
Health check utilities
"""

import time
import psutil
import os
from typing import Dict


def get_system_health() -> Dict:
    """
    Get system health metrics
    
    Returns:
        Dictionary with system health information
    """
    try:
        process = psutil.Process(os.getpid())
        
        return {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'memory_used_mb': psutil.virtual_memory().used / (1024 * 1024),
            'memory_available_mb': psutil.virtual_memory().available / (1024 * 1024),
            'process_memory_mb': process.memory_info().rss / (1024 * 1024),
            'process_cpu_percent': process.cpu_percent(interval=1),
            'uptime_seconds': time.time() - process.create_time()
        }
    except Exception as e:
        return {
            'error': str(e),
            'status': 'unhealthy'
        }


def check_service_health() -> Dict:
    """
    Check service health
    
    Returns:
        Dictionary with service health status
    """
    health = {
        'status': 'healthy',
        'timestamp': time.time(),
        'services': {}
    }
    
    # Check Whisper availability
    try:
        from services.asr_service import get_asr_service
        asr_service = get_asr_service()
        health['services']['whisper'] = asr_service.is_available()
    except:
        health['services']['whisper'] = False
    
    # Check database
    try:
        db_path = "data/training_data.db"
        health['services']['database'] = os.path.exists(db_path)
    except:
        health['services']['database'] = False
    
    # Overall status
    if not all(health['services'].values()):
        health['status'] = 'degraded'
    
    return health

