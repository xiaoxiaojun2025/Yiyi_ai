import time
import random
import sys
import os
from PyQt6.QtCore import QThread, pyqtSignal
from config.config import Config


class SensorWorker(QThread):
    """后台线程：MAX30102 传感器测量（飞腾派 Linux 环境）"""

    finger_detected = pyqtSignal()
    finger_lost = pyqtSignal()
    data_updated = pyqtSignal(float, float)
    measure_finished = pyqtSignal(float, float)
    measure_error = pyqtSignal(str)
    measure_timeout = pyqtSignal()

    def __init__(self, timeout_total=15, parent=None):
        super().__init__(parent)
        self._running = True
        self.timeout_total = timeout_total
        self.use_real_sensor = Config.USE_REAL_SENSOR

    def run(self):
        try:
            time.sleep(0.5)

            if not self._running:
                return

            self.finger_detected.emit()

            if self.use_real_sensor:
                # 使用真实 MAX30102 传感器
                self._read_from_real_sensor()
            else:
                # 使用模拟数据
                self._read_simulated_data()

        except Exception as e:
            self.measure_error.emit(str(e))

    def _read_simulated_data(self):
        """读取模拟传感器数据"""
        required_readings = 3
        valid_readings = 0
        hr_list = []
        spo2_list = []
        start_time = time.time()

        while self._running:
            if time.time() - start_time > self.timeout_total:
                self.measure_timeout.emit()
                break

            time.sleep(1.0)

            if not self._running:
                break

            hr = round(random.uniform(62, 95), 0)
            spo2 = round(random.uniform(95.0, 99.0), 1)

            self.data_updated.emit(hr, spo2)
            valid_readings += 1
            hr_list.append(hr)
            spo2_list.append(spo2)

            if valid_readings >= required_readings:
                avg_hr = round(sum(hr_list) / len(hr_list), 0)
                avg_spo2 = round(sum(spo2_list) / len(spo2_list), 1)
                self.measure_finished.emit(avg_hr, avg_spo2)
                break

    def _read_from_real_sensor(self):
        """从真实 MAX30102 传感器读取数据"""

        
        # 添加 max30102 库路径
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        max30102_path = os.path.join(project_root, "max30102-master")
        if max30102_path not in sys.path:
            sys.path.insert(0, max30102_path)
        
        try:
            from max30102 import MAX30102
            from hrcalc import calc_hr_and_spo2
            import numpy as np
            
            # 初始化传感器
            i2c_bus = Config.I2C_BUS
            i2c_address = Config.MAX30102_I2C_ADDRESS
            
            sensor = MAX30102(channel=i2c_bus, address=i2c_address)
            
            required_readings = 3  # 至少需要3次有效读数
            valid_readings = 0
            hr_list = []
            spo2_list = []
            start_time = time.time()
            
            while self._running:
                if time.time() - start_time > self.timeout_total:
                    self.measure_timeout.emit()
                    break
                
                # 读取原始数据（100个样本用于计算）
                red_buf, ir_buf = sensor.read_sequential(amount=100)
                
                if len(red_buf) < 100 or len(ir_buf) < 100:
                    time.sleep(0.5)
                    continue
                
                # 转换为 numpy 数组
                red_data = np.array(red_buf)
                ir_data = np.array(ir_buf)
                
                # 计算心率和血氧
                hr, hr_valid, spo2, spo2_valid = calc_hr_and_spo2(ir_data, red_data)
                
                # 验证数据有效性
                if hr_valid and spo2_valid and hr > 0 and spo2 > 0:
                    # 心率正常范围：40-200
                    # 血氧正常范围：70-100
                    if 40 <= hr <= 200 and 70 <= spo2 <= 100:
                        hr_rounded = round(hr, 0)
                        spo2_rounded = round(spo2, 1)
                        
                        self.data_updated.emit(hr_rounded, spo2_rounded)
                        valid_readings += 1
                        hr_list.append(hr_rounded)
                        spo2_list.append(spo2_rounded)
                        
                        if valid_readings >= required_readings:
                            avg_hr = round(sum(hr_list) / len(hr_list), 0)
                            avg_spo2 = round(sum(spo2_list) / len(spo2_list), 1)
                            self.measure_finished.emit(avg_hr, avg_spo2)
                            break
                
                time.sleep(1.0)
            
            # 关闭传感器
            sensor.shutdown()
            
        except ImportError as e:
            self.measure_error.emit(f"无法导入传感器库: {str(e)}\n请确保已安装依赖: pip install numpy smbus2")
        except Exception as e:
            self.measure_error.emit(f"传感器读取失败: {str(e)}\n请检查硬件连接和I2C配置")

    def stop(self):
        self._running = False
        self.wait(2000)
