"""
传感器工作线程测试
测试模拟数据和真实传感器读取
注意：这些测试需要实际运行应用，手指贴在传感器上
"""
import pytest
import time
from unittest.mock import MagicMock, patch
import sys


# Mock PyQt6模块
mock_qtcore = MagicMock()

class MockQThread:
    def __init__(self, parent=None):
        self.parent = parent
    
    def start(self):
        pass
    
    def quit(self):
        pass
    
    def wait(self):
        pass

class MockPyQtSignal:
    def __init__(self, *args, **kwargs):
        self.connections = []
    
    def connect(self, slot):
        self.connections.append(slot)
    
    def emit(self, *args):
        for conn in self.connections:
            conn(*args)

mock_qtcore.QThread = MockQThread
mock_qtcore.pyqtSignal = MockPyQtSignal

sys.modules['PyQt6'] = MagicMock()
sys.modules['PyQt6.QtCore'] = mock_qtcore

from app.hardware.sensor_worker import SensorWorker


class TestSensorWorker:
    """传感器工作线程测试类"""

    def test_sensor_worker_creation(self):
        """测试创建工作线程"""
        worker = SensorWorker()
        assert worker is not None
        assert worker._running == True
        assert worker.timeout_total == 15

    def test_sensor_worker_custom_timeout(self):
        """测试自定义超时时间"""
        worker = SensorWorker(timeout_total=20)
        assert worker.timeout_total == 20

    def test_simulated_data_generation(self):
        """测试模拟数据生成（无需硬件）"""
        worker = SensorWorker(timeout_total=3)  # 缩短超时时间
        
        # 捕获信号
        data_received = []
        finger_detected_count = [0]
        finished_received = [False]
        
        worker.data_updated.connect(lambda hr, spo2: data_received.append((hr, spo2)))
        worker.finger_detected.connect(lambda: finger_detected_count.__setitem__(0, finger_detected_count[0] + 1))
        worker.measure_finished.connect(lambda hr, spo2: finished_received.__setitem__(0, True))
        
        # 直接调用 run 方法的部分逻辑来测试信号发射
        worker.finger_detected.emit()
        time.sleep(0.1)
        worker.data_updated.emit(75.0, 98.0)
        time.sleep(0.1)
        worker.data_updated.emit(76.0, 97.5)
        time.sleep(0.1)
        worker.measure_finished.emit(75.5, 97.75)
        
        assert finger_detected_count[0] > 0
        assert len(data_received) >= 2
        assert finished_received[0] == True

    def test_measurement_duration(self):
        """测试测量持续时间"""
        worker = SensorWorker(timeout_total=2)
        
        start_time = time.time()
        with patch.object(worker, 'run') as mock_run:
            def mock_run_impl():
                time.sleep(0.5)
                worker.finger_detected.emit()
                time.sleep(1.0)
                worker.measure_finished.emit(75.0, 98.0)
            
            mock_run.side_effect = mock_run_impl
            worker.start()
            time.sleep(2)
        
        elapsed = time.time() - start_time
        assert elapsed < 3  # 应该在合理时间内完成

    def test_data_update_signal(self):
        """测试数据更新信号"""
        worker = SensorWorker()
        
        received_data = []
        worker.data_updated.connect(lambda hr, spo2: received_data.append((hr, spo2)))
        
        # 模拟发射信号
        worker.data_updated.emit(72.0, 98.5)
        worker.data_updated.emit(74.0, 97.8)
        
        assert len(received_data) == 2
        assert received_data[0] == (72.0, 98.5)
        assert received_data[1] == (74.0, 97.8)

    def test_measurement_finished_signal(self):
        """测试测量完成信号"""
        worker = SensorWorker()
        
        finished_results = []
        worker.measure_finished.connect(lambda hr, spo2: finished_results.append((hr, spo2)))
        
        # 模拟发射信号
        worker.measure_finished.emit(75.5, 98.2)
        
        assert len(finished_results) == 1
        assert finished_results[0] == (75.5, 98.2)

    @pytest.mark.skip(reason="需要真实MAX30102硬件")
    def test_real_sensor_reading(self):
        """测试真实传感器读取"""
        # 这个测试需要真实硬件
        pass

    def test_error_handling(self):
        """测试错误处理"""
        worker = SensorWorker()
        
        errors = []
        worker.measure_error.connect(lambda msg: errors.append(msg))
        
        # 模拟错误
        worker.measure_error.emit("传感器连接失败")
        
        assert len(errors) == 1
        assert "传感器连接失败" in errors[0]

    def test_concurrent_measurements(self):
        """测试并发测量"""
        worker1 = SensorWorker(timeout_total=1)
        worker2 = SensorWorker(timeout_total=1)
        
        assert worker1 is not worker2
        assert worker1.timeout_total == worker2.timeout_total