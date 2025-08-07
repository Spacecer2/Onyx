"""
JARVIS Task Queue System - Centralized task management with priority and retry logic
"""

import time
import threading
import queue
import logging
import uuid
from enum import Enum, IntEnum
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Union
from concurrent.futures import ThreadPoolExecutor, Future
import traceback

logger = logging.getLogger(__name__)

class TaskPriority(IntEnum):
    """Task priority levels (lower number = higher priority)"""
    CRITICAL = 0    # System critical tasks
    HIGH = 1        # User voice commands
    NORMAL = 2      # Text commands, photo capture
    LOW = 3         # Background tasks, status updates
    BACKGROUND = 4  # Cleanup, maintenance

class TaskStatus(Enum):
    """Task execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"

class TaskType(Enum):
    """Types of tasks in the system"""
    VOICE_COMMAND = "voice_command"
    TEXT_COMMAND = "text_command"
    PHOTO_CAPTURE = "photo_capture"
    CAMERA_ANALYSIS = "camera_analysis"
    TTS_SYNTHESIS = "tts_synthesis"
    SYSTEM_STATUS = "system_status"
    AUDIO_INIT = "audio_init"
    CAMERA_INIT = "camera_init"
    CLEANUP = "cleanup"

@dataclass
class Task:
    """Represents a task in the queue"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    task_type: TaskType = TaskType.TEXT_COMMAND
    priority: TaskPriority = TaskPriority.NORMAL
    function: Callable = None
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    callback: Optional[Callable] = None
    error_callback: Optional[Callable] = None
    max_retries: int = 3
    retry_delay: float = 1.0
    timeout: float = 30.0
    
    # Runtime fields
    status: TaskStatus = TaskStatus.PENDING
    attempts: int = 0
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    result: Any = None
    error: Optional[Exception] = None
    future: Optional[Future] = None

    def __lt__(self, other):
        """For priority queue ordering"""
        if self.priority != other.priority:
            return self.priority < other.priority
        return self.created_at < other.created_at

class TaskQueue:
    """Centralized task queue with parallel processing and retry logic"""
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="JARVIS-Worker")
        
        # Task queues by priority
        self.task_queue = queue.PriorityQueue()
        self.active_tasks: Dict[str, Task] = {}
        self.completed_tasks: List[Task] = []
        self.failed_tasks: List[Task] = []
        
        # Control flags
        self.running = False
        self.shutdown_event = threading.Event()
        
        # Worker threads
        self.dispatcher_thread = None
        self.monitor_thread = None
        
        # Statistics
        self.stats = {
            'total_tasks': 0,
            'completed_tasks': 0,
            'failed_tasks': 0,
            'retried_tasks': 0,
            'average_execution_time': 0.0
        }
        
        # Thread safety
        self.lock = threading.RLock()
        
        logger.info(f"TaskQueue initialized with {max_workers} workers")
    
    def start(self):
        """Start the task queue processing"""
        if self.running:
            logger.warning("TaskQueue already running")
            return
        
        self.running = True
        self.shutdown_event.clear()
        
        # Start dispatcher thread
        self.dispatcher_thread = threading.Thread(
            target=self._dispatch_tasks,
            name="JARVIS-Dispatcher",
            daemon=True
        )
        self.dispatcher_thread.start()
        
        # Start monitor thread
        self.monitor_thread = threading.Thread(
            target=self._monitor_tasks,
            name="JARVIS-Monitor",
            daemon=True
        )
        self.monitor_thread.start()
        
        logger.info("TaskQueue started")
    
    def stop(self, timeout: float = 10.0):
        """Stop the task queue processing"""
        if not self.running:
            return
        
        logger.info("Stopping TaskQueue...")
        self.running = False
        self.shutdown_event.set()
        
        # Wait for threads to finish
        if self.dispatcher_thread:
            self.dispatcher_thread.join(timeout=timeout/2)
        
        if self.monitor_thread:
            self.monitor_thread.join(timeout=timeout/2)
        
        # Shutdown executor
        self.executor.shutdown(wait=True, timeout=timeout)
        
        logger.info("TaskQueue stopped")
    
    def submit_task(self, 
                   task_type: TaskType,
                   function: Callable,
                   args: tuple = (),
                   kwargs: dict = None,
                   priority: TaskPriority = TaskPriority.NORMAL,
                   callback: Optional[Callable] = None,
                   error_callback: Optional[Callable] = None,
                   max_retries: int = 3,
                   timeout: float = 30.0) -> str:
        """Submit a task to the queue"""
        
        if kwargs is None:
            kwargs = {}
        
        task = Task(
            task_type=task_type,
            function=function,
            args=args,
            kwargs=kwargs,
            priority=priority,
            callback=callback,
            error_callback=error_callback,
            max_retries=max_retries,
            timeout=timeout
        )
        
        with self.lock:
            self.task_queue.put(task)
            self.stats['total_tasks'] += 1
        
        logger.debug(f"Task submitted: {task.id} ({task.task_type.value}, priority={priority.name})")
        return task.id
    
    def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """Get the status of a task"""
        with self.lock:
            if task_id in self.active_tasks:
                return self.active_tasks[task_id].status
            
            # Check completed tasks
            for task in self.completed_tasks:
                if task.id == task_id:
                    return task.status
            
            # Check failed tasks
            for task in self.failed_tasks:
                if task.id == task_id:
                    return task.status
        
        return None
    
    def get_task_result(self, task_id: str) -> Any:
        """Get the result of a completed task"""
        with self.lock:
            # Check completed tasks
            for task in self.completed_tasks:
                if task.id == task_id:
                    return task.result
            
            # Check active tasks
            if task_id in self.active_tasks:
                task = self.active_tasks[task_id]
                if task.status == TaskStatus.COMPLETED:
                    return task.result
        
        return None
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a pending or running task"""
        with self.lock:
            if task_id in self.active_tasks:
                task = self.active_tasks[task_id]
                if task.future and not task.future.done():
                    task.future.cancel()
                    task.status = TaskStatus.CANCELLED
                    logger.info(f"Task cancelled: {task_id}")
                    return True
        
        return False
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics"""
        with self.lock:
            return {
                **self.stats,
                'queue_size': self.task_queue.qsize(),
                'active_tasks': len(self.active_tasks),
                'worker_threads': self.max_workers
            }
    
    def _dispatch_tasks(self):
        """Main dispatcher loop - runs in separate thread"""
        logger.info("Task dispatcher started")
        
        while self.running and not self.shutdown_event.is_set():
            try:
                # Get next task (blocks with timeout)
                try:
                    task = self.task_queue.get(timeout=1.0)
                except queue.Empty:
                    continue
                
                # Submit task to executor
                with self.lock:
                    task.status = TaskStatus.RUNNING
                    task.started_at = time.time()
                    task.attempts += 1
                    self.active_tasks[task.id] = task
                
                # Submit to thread pool
                future = self.executor.submit(self._execute_task, task)
                task.future = future
                
                logger.debug(f"Task dispatched: {task.id} (attempt {task.attempts})")
                
            except Exception as e:
                logger.error(f"Error in task dispatcher: {e}")
                time.sleep(0.1)
        
        logger.info("Task dispatcher stopped")
    
    def _execute_task(self, task: Task) -> Any:
        """Execute a single task"""
        try:
            logger.debug(f"Executing task: {task.id} ({task.task_type.value})")
            
            # Execute the task function
            result = task.function(*task.args, **task.kwargs)
            
            # Task completed successfully
            with self.lock:
                task.status = TaskStatus.COMPLETED
                task.completed_at = time.time()
                task.result = result
                
                # Move to completed tasks
                if task.id in self.active_tasks:
                    del self.active_tasks[task.id]
                self.completed_tasks.append(task)
                self.stats['completed_tasks'] += 1
                
                # Update average execution time
                execution_time = task.completed_at - task.started_at
                self._update_average_execution_time(execution_time)
            
            # Call success callback
            if task.callback:
                try:
                    task.callback(result)
                except Exception as e:
                    logger.error(f"Error in task callback: {e}")
            
            logger.debug(f"Task completed: {task.id}")
            return result
            
        except Exception as e:
            logger.error(f"Task execution failed: {task.id} - {e}")
            
            with self.lock:
                task.error = e
                
                # Check if we should retry
                if task.attempts < task.max_retries:
                    task.status = TaskStatus.RETRYING
                    self.stats['retried_tasks'] += 1
                    
                    # Remove from active tasks temporarily
                    if task.id in self.active_tasks:
                        del self.active_tasks[task.id]
                    
                    # Schedule retry
                    retry_thread = threading.Thread(
                        target=self._schedule_retry,
                        args=(task,),
                        daemon=True
                    )
                    retry_thread.start()
                    
                else:
                    # Max retries reached
                    task.status = TaskStatus.FAILED
                    task.completed_at = time.time()
                    
                    # Move to failed tasks
                    if task.id in self.active_tasks:
                        del self.active_tasks[task.id]
                    self.failed_tasks.append(task)
                    self.stats['failed_tasks'] += 1
                    
                    # Call error callback
                    if task.error_callback:
                        try:
                            task.error_callback(e)
                        except Exception as callback_error:
                            logger.error(f"Error in error callback: {callback_error}")
            
            raise e
    
    def _schedule_retry(self, task: Task):
        """Schedule a task retry after delay"""
        time.sleep(task.retry_delay)
        
        if self.running:
            logger.info(f"Retrying task: {task.id} (attempt {task.attempts + 1})")
            task.status = TaskStatus.PENDING
            self.task_queue.put(task)
    
    def _monitor_tasks(self):
        """Monitor task timeouts and cleanup - runs in separate thread"""
        logger.info("Task monitor started")
        
        while self.running and not self.shutdown_event.is_set():
            try:
                current_time = time.time()
                timed_out_tasks = []
                
                with self.lock:
                    for task_id, task in list(self.active_tasks.items()):
                        if (task.started_at and 
                            current_time - task.started_at > task.timeout):
                            timed_out_tasks.append(task)
                
                # Handle timed out tasks
                for task in timed_out_tasks:
                    logger.warning(f"Task timed out: {task.id}")
                    if task.future:
                        task.future.cancel()
                    
                    with self.lock:
                        task.status = TaskStatus.FAILED
                        task.error = TimeoutError(f"Task timed out after {task.timeout}s")
                        task.completed_at = current_time
                        
                        if task.id in self.active_tasks:
                            del self.active_tasks[task.id]
                        self.failed_tasks.append(task)
                        self.stats['failed_tasks'] += 1
                
                # Cleanup old completed/failed tasks (keep last 100)
                with self.lock:
                    if len(self.completed_tasks) > 100:
                        self.completed_tasks = self.completed_tasks[-100:]
                    
                    if len(self.failed_tasks) > 100:
                        self.failed_tasks = self.failed_tasks[-100:]
                
                time.sleep(5.0)  # Check every 5 seconds
                
            except Exception as e:
                logger.error(f"Error in task monitor: {e}")
                time.sleep(1.0)
        
        logger.info("Task monitor stopped")
    
    def _update_average_execution_time(self, execution_time: float):
        """Update average execution time statistic"""
        current_avg = self.stats['average_execution_time']
        completed_count = self.stats['completed_tasks']
        
        if completed_count == 1:
            self.stats['average_execution_time'] = execution_time
        else:
            # Running average
            self.stats['average_execution_time'] = (
                (current_avg * (completed_count - 1) + execution_time) / completed_count
            )

# Global task queue instance
task_queue = TaskQueue(max_workers=6)

# Convenience functions
def submit_task(task_type: TaskType, function: Callable, *args, **kwargs) -> str:
    """Submit a task to the global queue"""
    return task_queue.submit_task(task_type, function, args, kwargs)

def get_task_status(task_id: str) -> Optional[TaskStatus]:
    """Get task status from global queue"""
    return task_queue.get_task_status(task_id)

def get_task_result(task_id: str) -> Any:
    """Get task result from global queue"""
    return task_queue.get_task_result(task_id)
