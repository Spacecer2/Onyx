"""
JARVIS Reliability Manager - Comprehensive error handling, logging, and recovery
"""

import time
import threading
import logging
import traceback
import os
import json
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import psutil

logger = logging.getLogger(__name__)

class HealthStatus(Enum):
    """Component health status"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    FAILED = "failed"
    RECOVERING = "recovering"

@dataclass
class ComponentHealth:
    """Health information for a system component"""
    name: str
    status: HealthStatus
    last_check: float
    error_count: int
    last_error: Optional[str]
    uptime: float
    recovery_attempts: int
    metrics: Dict[str, Any]

@dataclass
class SystemMetrics:
    """System-wide metrics"""
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_active: bool
    temperature: Optional[float]
    load_average: List[float]

class ReliabilityManager:
    """Manages system reliability, error handling, and recovery"""
    
    def __init__(self):
        self.components: Dict[str, ComponentHealth] = {}
        self.system_metrics = SystemMetrics(0, 0, 0, False, None, [])
        
        # Configuration
        self.check_interval = 10.0  # seconds
        self.max_error_count = 5
        self.recovery_cooldown = 30.0  # seconds
        
        # Logging
        self.log_dir = Path("jarvis/logs")
        self.log_dir.mkdir(exist_ok=True)
        self._setup_logging()
        
        # Threading
        self.monitor_thread = None
        self.running = False
        
        # Error tracking
        self.global_error_count = 0
        self.last_critical_error = None
        
        # Recovery callbacks
        self.recovery_callbacks: Dict[str, Callable] = {}
        
        # Health history
        self.health_history: List[Dict[str, Any]] = []
        self.max_history_size = 1000
        
        logger.info("ReliabilityManager initialized")
    
    def start(self):
        """Start the reliability monitoring system"""
        if self.running:
            logger.warning("ReliabilityManager already running")
            return
        
        self.running = True
        
        # Start monitoring thread
        self.monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            name="JARVIS-Reliability",
            daemon=True
        )
        self.monitor_thread.start()
        
        logger.info("ReliabilityManager started")
    
    def stop(self):
        """Stop the reliability monitoring system"""
        if not self.running:
            return
        
        logger.info("Stopping ReliabilityManager...")
        self.running = False
        
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5.0)
        
        # Save final health report
        self._save_health_report()
        
        logger.info("ReliabilityManager stopped")
    
    def register_component(self, name: str, recovery_callback: Optional[Callable] = None):
        """Register a component for monitoring"""
        self.components[name] = ComponentHealth(
            name=name,
            status=HealthStatus.HEALTHY,
            last_check=time.time(),
            error_count=0,
            last_error=None,
            uptime=time.time(),
            recovery_attempts=0,
            metrics={}
        )
        
        if recovery_callback:
            self.recovery_callbacks[name] = recovery_callback
        
        logger.info(f"Component registered: {name}")
    
    def report_component_health(self, name: str, status: HealthStatus, 
                              metrics: Optional[Dict[str, Any]] = None,
                              error: Optional[str] = None):
        """Report health status for a component"""
        if name not in self.components:
            self.register_component(name)
        
        component = self.components[name]
        component.status = status
        component.last_check = time.time()
        
        if metrics:
            component.metrics.update(metrics)
        
        if error:
            component.error_count += 1
            component.last_error = error
            self.global_error_count += 1
            
            logger.warning(f"Component error reported: {name} - {error}")
            
            # Check if component needs recovery
            if component.error_count >= self.max_error_count:
                self._trigger_component_recovery(name)
        
        # Log critical status changes
        if status == HealthStatus.CRITICAL:
            logger.critical(f"Component critical: {name}")
            self.last_critical_error = time.time()
        elif status == HealthStatus.FAILED:
            logger.error(f"Component failed: {name}")
    
    def report_error(self, component: str, error: Exception, context: str = ""):
        """Report an error for a component"""
        error_msg = f"{context}: {str(error)}" if context else str(error)
        
        # Log full traceback for debugging
        logger.error(f"Error in {component}: {error_msg}")
        logger.debug(f"Full traceback: {traceback.format_exc()}")
        
        # Update component health
        self.report_component_health(
            component, 
            HealthStatus.WARNING, 
            error=error_msg
        )
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get comprehensive system health report"""
        overall_status = self._calculate_overall_health()
        
        return {
            'overall_status': overall_status.value,
            'components': {name: asdict(comp) for name, comp in self.components.items()},
            'system_metrics': asdict(self.system_metrics),
            'global_stats': {
                'total_errors': self.global_error_count,
                'last_critical_error': self.last_critical_error,
                'uptime': time.time() - min(comp.uptime for comp in self.components.values()) if self.components else 0
            }
        }
    
    def get_component_health(self, name: str) -> Optional[ComponentHealth]:
        """Get health information for a specific component"""
        return self.components.get(name)
    
    def force_component_recovery(self, name: str) -> bool:
        """Force recovery for a specific component"""
        if name not in self.components:
            logger.error(f"Component not found: {name}")
            return False
        
        return self._trigger_component_recovery(name)
    
    def _setup_logging(self):
        """Setup comprehensive logging"""
        # Create log files
        log_files = {
            'main': self.log_dir / 'jarvis.log',
            'errors': self.log_dir / 'errors.log',
            'health': self.log_dir / 'health.log'
        }
        
        # Setup file handlers
        for log_type, log_file in log_files.items():
            handler = logging.FileHandler(log_file)
            handler.setLevel(logging.DEBUG if log_type == 'main' else logging.WARNING)
            
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            
            # Add to root logger
            logging.getLogger().addHandler(handler)
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        logger.info("Reliability monitoring started")
        
        while self.running:
            try:
                # Update system metrics
                self._update_system_metrics()
                
                # Check component health
                self._check_component_health()
                
                # Save health snapshot
                self._save_health_snapshot()
                
                # Cleanup old data
                self._cleanup_old_data()
                
                time.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(1.0)
        
        logger.info("Reliability monitoring stopped")
    
    def _update_system_metrics(self):
        """Update system-wide metrics"""
        try:
            # CPU usage
            self.system_metrics.cpu_usage = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            self.system_metrics.memory_usage = memory.percent
            
            # Disk usage
            disk = psutil.disk_usage('/')
            self.system_metrics.disk_usage = disk.percent
            
            # Network activity
            network = psutil.net_io_counters()
            self.system_metrics.network_active = network.bytes_sent > 0 or network.bytes_recv > 0
            
            # Load average
            if hasattr(os, 'getloadavg'):
                self.system_metrics.load_average = list(os.getloadavg())
            
            # Temperature (if available)
            try:
                temps = psutil.sensors_temperatures()
                if temps:
                    # Get CPU temperature
                    for name, entries in temps.items():
                        if 'cpu' in name.lower() or 'core' in name.lower():
                            self.system_metrics.temperature = entries[0].current
                            break
            except:
                pass  # Temperature monitoring not available
                
        except Exception as e:
            logger.error(f"Error updating system metrics: {e}")
    
    def _check_component_health(self):
        """Check health of all registered components"""
        current_time = time.time()
        
        for name, component in self.components.items():
            try:
                # Check if component is stale (no recent updates)
                if current_time - component.last_check > 60.0:  # 1 minute
                    component.status = HealthStatus.WARNING
                    logger.warning(f"Component stale: {name}")
                
                # Check if component needs recovery
                if (component.status in [HealthStatus.CRITICAL, HealthStatus.FAILED] and
                    current_time - component.last_check > self.recovery_cooldown):
                    
                    self._trigger_component_recovery(name)
                
            except Exception as e:
                logger.error(f"Error checking component health {name}: {e}")
    
    def _trigger_component_recovery(self, name: str) -> bool:
        """Trigger recovery for a component"""
        if name not in self.components:
            return False
        
        component = self.components[name]
        component.recovery_attempts += 1
        component.status = HealthStatus.RECOVERING
        
        logger.info(f"Triggering recovery for component: {name} (attempt {component.recovery_attempts})")
        
        try:
            # Call recovery callback if available
            if name in self.recovery_callbacks:
                recovery_func = self.recovery_callbacks[name]
                success = recovery_func()
                
                if success:
                    component.status = HealthStatus.HEALTHY
                    component.error_count = 0
                    component.last_error = None
                    logger.info(f"Component recovery successful: {name}")
                    return True
                else:
                    component.status = HealthStatus.FAILED
                    logger.error(f"Component recovery failed: {name}")
                    return False
            else:
                logger.warning(f"No recovery callback for component: {name}")
                return False
                
        except Exception as e:
            logger.error(f"Error during component recovery {name}: {e}")
            component.status = HealthStatus.FAILED
            return False
    
    def _calculate_overall_health(self) -> HealthStatus:
        """Calculate overall system health status"""
        if not self.components:
            return HealthStatus.HEALTHY
        
        statuses = [comp.status for comp in self.components.values()]
        
        # If any component is failed, system is critical
        if HealthStatus.FAILED in statuses:
            return HealthStatus.CRITICAL
        
        # If any component is critical, system is critical
        if HealthStatus.CRITICAL in statuses:
            return HealthStatus.CRITICAL
        
        # If any component is recovering, system is warning
        if HealthStatus.RECOVERING in statuses:
            return HealthStatus.WARNING
        
        # If more than half are warning, system is warning
        warning_count = statuses.count(HealthStatus.WARNING)
        if warning_count > len(statuses) / 2:
            return HealthStatus.WARNING
        
        # Otherwise, system is healthy
        return HealthStatus.HEALTHY
    
    def _save_health_snapshot(self):
        """Save current health snapshot to history"""
        snapshot = {
            'timestamp': time.time(),
            'overall_status': self._calculate_overall_health().value,
            'component_count': len(self.components),
            'error_count': self.global_error_count,
            'system_metrics': asdict(self.system_metrics)
        }
        
        self.health_history.append(snapshot)
        
        # Limit history size
        if len(self.health_history) > self.max_history_size:
            self.health_history = self.health_history[-self.max_history_size:]
    
    def _save_health_report(self):
        """Save comprehensive health report to file"""
        try:
            report_file = self.log_dir / f"health_report_{int(time.time())}.json"
            
            report = {
                'timestamp': time.time(),
                'system_health': self.get_system_health(),
                'health_history': self.health_history[-100:]  # Last 100 snapshots
            }
            
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            logger.info(f"Health report saved: {report_file}")
            
        except Exception as e:
            logger.error(f"Error saving health report: {e}")
    
    def _cleanup_old_data(self):
        """Cleanup old log files and data"""
        try:
            # Clean up old log files (keep last 7 days)
            cutoff_time = time.time() - (7 * 24 * 3600)
            
            for log_file in self.log_dir.glob("*.log"):
                if log_file.stat().st_mtime < cutoff_time:
                    log_file.unlink()
            
            # Clean up old health reports (keep last 30)
            health_reports = sorted(self.log_dir.glob("health_report_*.json"))
            if len(health_reports) > 30:
                for report in health_reports[:-30]:
                    report.unlink()
                    
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

# Global reliability manager instance
reliability_manager = ReliabilityManager()

def get_reliability_manager() -> ReliabilityManager:
    """Get global reliability manager instance"""
    return reliability_manager
