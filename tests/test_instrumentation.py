"""
Tests for the instrumentation and diagnostics system.
"""
import pytest
import time
from unittest.mock import patch, MagicMock
from instrumentation import (
    InstrumentationManager, PerformanceMetrics, SystemInfo,
    instrumentation, log_chat_request, log_chat_response,
    log_provider_health_check, create_debug_panel, export_diagnostics
)


class TestInstrumentationManager:
    """Tests for the InstrumentationManager class."""

    def test_initialization(self):
        """Test that InstrumentationManager initializes correctly."""
        manager = InstrumentationManager()
        assert manager.metrics == []
        assert manager.errors == []
        assert isinstance(manager.start_time, float)
        assert manager.start_time > 0

    def test_log_operation_success(self):
        """Test logging a successful operation."""
        manager = InstrumentationManager()
        manager.log_operation("test_op", True, 1.5, op_type="chat", user="test")

        assert len(manager.metrics) == 1
        metric = manager.metrics[0]
        assert metric.operation == "test_op"
        assert metric.success is True
        assert metric.duration == 1.5
        assert metric.error_message is None
        assert metric.metadata == {"op_type": "chat", "user": "test"}

    def test_log_operation_failure(self):
        """Test logging a failed operation."""
        manager = InstrumentationManager()
        error = Exception("Test error")
        manager.log_operation("test_op", False, 2.0, error, error_code=500)

        assert len(manager.metrics) == 1
        assert len(manager.errors) == 1

        metric = manager.metrics[0]
        assert metric.operation == "test_op"
        assert metric.success is False
        assert metric.duration == 2.0
        assert "Test error" in metric.error_message

        error_entry = manager.errors[0]
        assert error_entry["operation"] == "test_op"
        assert "Test error" in error_entry["error"]

    def test_time_operation_context_manager(self):
        """Test the time_operation context manager."""
        manager = InstrumentationManager()

        with manager.time_operation("timed_op", test_param="value"):
            time.sleep(0.01)  # Small delay

        assert len(manager.metrics) == 1
        metric = manager.metrics[0]
        assert metric.operation == "timed_op"
        assert metric.success is True
        assert metric.duration >= 0.01
        assert metric.metadata == {"test_param": "value"}

    def test_time_operation_with_exception(self):
        """Test time_operation context manager with exception."""
        manager = InstrumentationManager()

        with pytest.raises(ValueError):
            with manager.time_operation("failing_op"):
                time.sleep(0.01)
                raise ValueError("Test exception")

        assert len(manager.metrics) == 1
        assert len(manager.errors) == 1

        metric = manager.metrics[0]
        assert metric.operation == "failing_op"
        assert metric.success is False
        assert "Test exception" in metric.error_message

    def test_get_recent_metrics(self):
        """Test getting recent metrics."""
        manager = InstrumentationManager()

        # Add multiple metrics
        for i in range(5):
            manager.log_operation(f"op_{i}", True, i * 0.1)

        recent = manager.get_recent_metrics(3)
        assert len(recent) == 3
        assert recent[0].operation == "op_4"  # Most recent first
        assert recent[1].operation == "op_3"
        assert recent[2].operation == "op_2"

    def test_get_error_summary_no_errors(self):
        """Test error summary when no errors exist."""
        manager = InstrumentationManager()
        summary = manager.get_error_summary()

        assert summary["total_errors"] == 0
        assert summary["error_rate"] == 0.0
        assert summary["error_types"] == {}
        assert summary["recent_errors"] == []

    def test_get_error_summary_with_errors(self):
        """Test error summary with errors."""
        manager = InstrumentationManager()

        # Add some operations
        manager.log_operation("success_op", True, 0.1)
        manager.log_operation("error_op1", False, 0.2, Exception("Error 1"))
        manager.log_operation("error_op2", False, 0.3, Exception("Error 2"))
        manager.log_operation("success_op2", True, 0.1)

        summary = manager.get_error_summary()
        assert summary["total_errors"] == 2
        assert summary["error_rate"] == 0.5  # 2 errors out of 4 operations
        assert len(summary["recent_errors"]) == 2

    @patch('instrumentation.psutil.virtual_memory')
    @patch('instrumentation.psutil.disk_usage')
    @patch('instrumentation.psutil.cpu_count')
    @patch('instrumentation.platform.system')
    @patch('instrumentation.platform.release')
    @patch('instrumentation.platform.python_version')
    def test_get_system_info(self, mock_python_version, mock_release, mock_system,
                           mock_cpu_count, mock_disk_usage, mock_memory):
        """Test getting system information."""
        # Setup mocks
        mock_system.return_value = "Linux"
        mock_release.return_value = "5.15.0"
        mock_python_version.return_value = "3.12.3"
        mock_cpu_count.return_value = 8

        mock_memory_obj = MagicMock()
        mock_memory_obj.total = 16 * 1024**3  # 16GB
        mock_memory_obj.available = 8 * 1024**3  # 8GB
        mock_memory.return_value = mock_memory_obj

        mock_disk_obj = MagicMock()
        mock_disk_obj.total = 512 * 1024**3  # 512GB
        mock_disk_obj.used = 256 * 1024**3  # 256GB used
        mock_disk_usage.return_value = mock_disk_obj

        manager = InstrumentationManager()
        sys_info = manager.get_system_info()

        assert isinstance(sys_info, SystemInfo)
        assert "Linux" in sys_info.platform
        assert sys_info.python_version == "3.12.3"
        assert sys_info.cpu_count == 8

    def test_get_performance_summary_no_metrics(self):
        """Test performance summary with no metrics."""
        manager = InstrumentationManager()
        summary = manager.get_performance_summary()

        assert summary["total_operations"] == 0
        assert summary["avg_duration"] == 0.0
        assert summary["success_rate"] == 0.0

    def test_get_performance_summary_with_metrics(self):
        """Test performance summary with metrics."""
        manager = InstrumentationManager()

        # Add test metrics
        manager.log_operation("fast_op", True, 0.1, category="api")
        manager.log_operation("slow_op", True, 1.0, category="api")
        manager.log_operation("failed_op", False, 0.5, category="api")

        summary = manager.get_performance_summary()

        assert summary["total_operations"] == 3
        assert summary["success_rate"] == 2/3  # 2 successful out of 3
        assert abs(summary["avg_duration"] - (0.1 + 1.0 + 0.5) / 3) < 0.001

        # Check operation stats
        op_stats = summary["operation_stats"]
        assert "fast_op" in op_stats
        assert "slow_op" in op_stats
        assert "failed_op" in op_stats

        assert op_stats["fast_op"]["count"] == 1
        assert op_stats["fast_op"]["errors"] == 0


class TestInstrumentationFunctions:
    """Tests for the instrumentation utility functions."""

    def test_log_chat_request(self):
        """Test logging chat requests."""
        initial_count = len(instrumentation.metrics)
        log_chat_request("OpenAI", "gpt-4", 5, True)

        assert len(instrumentation.metrics) == initial_count + 1
        metric = instrumentation.metrics[-1]
        assert metric.operation == "chat_request"
        assert metric.metadata["provider"] == "OpenAI"
        assert metric.metadata["model"] == "gpt-4"
        assert metric.metadata["message_count"] == 5
        assert metric.metadata["streaming"] is True

    def test_log_chat_response_success(self):
        """Test logging successful chat responses."""
        initial_count = len(instrumentation.metrics)
        log_chat_response("OpenAI", "gpt-4", True, 150, 100, 2.5)

        assert len(instrumentation.metrics) == initial_count + 1
        metric = instrumentation.metrics[-1]
        assert metric.operation == "chat_response"
        assert metric.success is True
        assert metric.duration == 2.5
        assert metric.metadata["response_length"] == 150
        assert metric.metadata["tokens_used"] == 100

    def test_log_chat_response_failure(self):
        """Test logging failed chat responses."""
        initial_count = len(instrumentation.metrics)
        initial_errors = len(instrumentation.errors)

        error = Exception("API timeout")
        log_chat_response("OpenAI", "gpt-4", False, duration=5.0, error=error)

        assert len(instrumentation.metrics) == initial_count + 1
        assert len(instrumentation.errors) == initial_errors + 1

        metric = instrumentation.metrics[-1]
        assert metric.operation == "chat_response"
        assert metric.success is False
        assert metric.duration == 5.0
        assert "API timeout" in metric.error_message

    def test_log_provider_health_check(self):
        """Test logging provider health checks."""
        initial_count = len(instrumentation.metrics)
        log_provider_health_check("Ollama", True, 0.5)

        assert len(instrumentation.metrics) == initial_count + 1
        metric = instrumentation.metrics[-1]
        assert metric.operation == "health_check"
        assert metric.success is True
        assert metric.duration == 0.5
        assert metric.metadata["provider"] == "Ollama"

    def test_export_diagnostics(self):
        """Test exporting diagnostics data."""
        # Add some test data
        instrumentation.log_operation("test_op", True, 1.0)
        instrumentation.log_operation("error_op", False, 0.5, Exception("Test error"))

        diagnostics = export_diagnostics()

        # Should be valid JSON
        import json
        data = json.loads(diagnostics)

        assert "timestamp" in data
        assert "performance" in data
        assert "errors" in data
        assert "system" in data
        assert "recent_metrics" in data

        assert data["performance"]["total_operations"] >= 2
        assert data["errors"]["total_errors"] >= 1


class TestPerformanceMetrics:
    """Tests for the PerformanceMetrics dataclass."""

    def test_performance_metrics_creation(self):
        """Test creating PerformanceMetrics."""
        import time
        start = time.time()

        metric = PerformanceMetrics(
            operation="test_op",
            start_time=start,
            end_time=start + 1.5,
            duration=1.5,
            success=True,
            metadata={"key": "value"}
        )

        assert metric.operation == "test_op"
        assert metric.start_time == start
        assert metric.end_time == start + 1.5
        assert metric.duration == 1.5
        assert metric.success is True
        assert metric.error_message is None
        assert metric.metadata == {"key": "value"}

    def test_performance_metrics_defaults(self):
        """Test PerformanceMetrics default values."""
        metric = PerformanceMetrics(
            operation="test_op",
            start_time=0.0,
            end_time=1.0,
            duration=1.0,
            success=False
        )

        assert metric.metadata == {}
        assert metric.error_message is None


class TestSystemInfo:
    """Tests for the SystemInfo dataclass."""

    def test_system_info_creation(self):
        """Test creating SystemInfo."""
        sys_info = SystemInfo(
            platform="Linux 5.15.0",
            python_version="3.12.3",
            cpu_count=8,
            memory_total="16.0 GB",
            memory_available="8.0 GB",
            disk_usage="50.0%"
        )

        assert sys_info.platform == "Linux 5.15.0"
        assert sys_info.python_version == "3.12.3"
        assert sys_info.cpu_count == 8
        assert sys_info.memory_total == "16.0 GB"
        assert sys_info.memory_available == "8.0 GB"
        assert sys_info.disk_usage == "50.0%"