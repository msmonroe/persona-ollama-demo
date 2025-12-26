"""
Instrumentation and diagnostics utilities for the Persona Creator app.
Provides comprehensive logging, performance monitoring, and debugging tools.
"""

import logging
import time
import json
import psutil
import platform
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from contextlib import contextmanager
import streamlit as st

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """Performance metrics for operations."""
    operation: str
    start_time: float
    end_time: float
    duration: float
    success: bool
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class SystemInfo:
    """System information for diagnostics."""
    platform: str
    python_version: str
    cpu_count: int
    memory_total: str
    memory_available: str
    disk_usage: str

class InstrumentationManager:
    """Central manager for application instrumentation."""

    def __init__(self):
        self.metrics: List[PerformanceMetrics] = []
        self.errors: List[Dict[str, Any]] = []
        self.start_time = time.time()

    def log_operation(self, operation: str, success: bool, duration: float = None,
                     error: Exception = None, **metadata):
        """Log an operation with performance metrics."""
        if duration is None:
            duration = 0.0

        metric = PerformanceMetrics(
            operation=operation,
            start_time=time.time() - duration,
            end_time=time.time(),
            duration=duration,
            success=success,
            error_message=str(error) if error else None,
            metadata=metadata
        )

        self.metrics.append(metric)

        # Log to file
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "success": success,
            "duration": duration,
            "error": str(error) if error else None,
            **metadata
        }

        if success:
            logger.info(f"Operation completed: {operation}", extra=log_data)
        else:
            logger.error(f"Operation failed: {operation}", extra={"error": str(error), **log_data})
            self.errors.append(log_data)

    @contextmanager
    def time_operation(self, operation: str, **metadata):
        """Context manager to time operations."""
        start_time = time.time()
        try:
            yield
            duration = time.time() - start_time
            self.log_operation(operation, True, duration, **metadata)
        except Exception as e:
            duration = time.time() - start_time
            self.log_operation(operation, False, duration, e, **metadata)
            raise

    def get_recent_metrics(self, limit: int = 50) -> List[PerformanceMetrics]:
        """Get recent performance metrics."""
        return list(reversed(self.metrics[-limit:]))

    def get_error_summary(self) -> Dict[str, Any]:
        """Get error summary statistics."""
        if not self.errors:
            return {
                "total_errors": 0,
                "error_rate": 0.0,
                "error_types": {},
                "recent_errors": []
            }

        total_operations = len(self.metrics)
        error_rate = len(self.errors) / total_operations if total_operations > 0 else 0

        # Group errors by type
        error_types = {}
        for error in self.errors:
            error_type = error.get("error", "Unknown").split(":")[0]
            error_types[error_type] = error_types.get(error_type, 0) + 1

        return {
            "total_errors": len(self.errors),
            "error_rate": error_rate,
            "error_types": error_types,
            "recent_errors": self.errors[-5:]  # Last 5 errors
        }

    def get_system_info(self) -> SystemInfo:
        """Get system information."""
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        return SystemInfo(
            platform=f"{platform.system()} {platform.release()}",
            python_version=platform.python_version(),
            cpu_count=psutil.cpu_count(),
            memory_total=".1f",
            memory_available=".1f",
            disk_usage=".1f"
        )

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary statistics."""
        if not self.metrics:
            return {"total_operations": 0, "avg_duration": 0.0, "success_rate": 0.0}

        total_ops = len(self.metrics)
        successful_ops = sum(1 for m in self.metrics if m.success)
        avg_duration = sum(m.duration for m in self.metrics) / total_ops

        # Group by operation type
        op_stats = {}
        for metric in self.metrics:
            if metric.operation not in op_stats:
                op_stats[metric.operation] = {"count": 0, "total_duration": 0.0, "errors": 0}
            op_stats[metric.operation]["count"] += 1
            op_stats[metric.operation]["total_duration"] += metric.duration
            if not metric.success:
                op_stats[metric.operation]["errors"] += 1

        return {
            "total_operations": total_ops,
            "success_rate": successful_ops / total_ops,
            "avg_duration": avg_duration,
            "operation_stats": op_stats,
            "uptime": time.time() - self.start_time
        }

# Global instrumentation instance
instrumentation = InstrumentationManager()

def log_chat_request(provider: str, model: str, message_count: int, streaming: bool):
    """Log chat request details."""
    instrumentation.log_operation(
        "chat_request",
        True,
        provider=provider,
        model=model,
        message_count=message_count,
        streaming=streaming
    )

def log_chat_response(provider: str, model: str, success: bool, response_length: int = 0,
                     tokens_used: int = 0, duration: float = 0.0, error: Exception = None):
    """Log chat response details."""
    instrumentation.log_operation(
        "chat_response",
        success,
        duration,
        error,
        provider=provider,
        model=model,
        response_length=response_length,
        tokens_used=tokens_used
    )

def log_provider_health_check(provider: str, success: bool, duration: float, error: Exception = None):
    """Log provider health check results."""
    instrumentation.log_operation(
        "health_check",
        success,
        duration,
        error,
        provider=provider
    )

def create_debug_panel():
    """Create a debug panel in Streamlit for diagnostics."""
    with st.expander("🔧 Debug & Diagnostics", expanded=False):
        tab1, tab2, tab3, tab4 = st.tabs(["Performance", "Errors", "System", "Logs"])

        with tab1:
            st.subheader("Performance Metrics")
            perf_summary = instrumentation.get_performance_summary()

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Operations", perf_summary["total_operations"])
            with col2:
                st.metric("Success Rate", ".1%")
            with col3:
                st.metric("Avg Duration", ".2f")

            st.subheader("Operation Statistics")
            if perf_summary["operation_stats"]:
                for op, stats in perf_summary["operation_stats"].items():
                    with st.container():
                        st.write(f"**{op}**")
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Count", stats["count"])
                        with col2:
                            st.metric("Avg Duration", ".2f")
                        with col3:
                            st.metric("Total Duration", ".2f")
                        with col4:
                            st.metric("Errors", stats["errors"])

        with tab2:
            st.subheader("Error Summary")
            error_summary = instrumentation.get_error_summary()

            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Errors", error_summary["total_errors"])
            with col2:
                st.metric("Error Rate", ".1%")

            if error_summary["error_types"]:
                st.subheader("Error Types")
                for error_type, count in error_summary["error_types"].items():
                    st.write(f"• {error_type}: {count}")

            if error_summary["recent_errors"]:
                st.subheader("Recent Errors")
                for error in error_summary["recent_errors"]:
                    with st.container():
                        st.error(f"**{error['operation']}** - {error['error']}")
                        st.caption(f"Time: {error['timestamp']}")

        with tab3:
            st.subheader("System Information")
            sys_info = instrumentation.get_system_info()

            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Platform:** {sys_info.platform}")
                st.write(f"**Python:** {sys_info.python_version}")
                st.write(f"**CPU Cores:** {sys_info.cpu_count}")
            with col2:
                st.write(f"**Memory Total:** {sys_info.memory_total}")
                st.write(f"**Memory Available:** {sys_info.memory_available}")
                st.write(f"**Disk Usage:** {sys_info.disk_usage}")

            st.metric("App Uptime", ".1f")

        with tab4:
            st.subheader("Recent Operations")
            recent_metrics = instrumentation.get_recent_metrics(20)

            if recent_metrics:
                for metric in reversed(recent_metrics):
                    status_icon = "✅" if metric.success else "❌"
                    duration_str = ".2f"

                    with st.container():
                        col1, col2, col3 = st.columns([2, 1, 1])
                        with col1:
                            st.write(f"{status_icon} **{metric.operation}**")
                        with col2:
                            st.write(f"{duration_str}s")
                        with col3:
                            st.caption(datetime.fromtimestamp(metric.start_time).strftime("%H:%M:%S"))

                        if metric.metadata:
                            with st.expander("Details", expanded=False):
                                st.json(metric.metadata)
            else:
                st.info("No operations logged yet.")

def export_diagnostics():
    """Export diagnostics data for support."""
    diagnostics = {
        "timestamp": datetime.now().isoformat(),
        "performance": instrumentation.get_performance_summary(),
        "errors": instrumentation.get_error_summary(),
        "system": asdict(instrumentation.get_system_info()),
        "recent_metrics": [asdict(m) for m in instrumentation.get_recent_metrics(100)]
    }

    return json.dumps(diagnostics, indent=2, default=str)