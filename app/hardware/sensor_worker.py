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

    def __init__(self, timeout_total=30, parent=None):
        super().__init__(parent)
        self._running = True
        self.timeout_total = timeout_total
        self.use_real_sensor = Config.USE_REAL_SENSOR

    def run(self):
        try:
            time.sleep(0.5)

            if not self._running:
                return

            if self.use_real_sensor:
                # 使用真实 MAX30102 传感器
                print("[DEBUG] 使用真实传感器模式")
                self._read_from_real_sensor()
            else:
                # 使用模拟数据
                print("[DEBUG] 使用模拟数据模式")
                self.finger_detected.emit()
                self._read_simulated_data()

        except Exception as e:
            print(f"[ERROR] 传感器运行异常: {e}")
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
        
        # 添加 max30102 库路径（兼容 PyInstaller 打包）
        if getattr(sys, 'frozen', False):
            # PyInstaller 打包后：模块在 exe 同级的 max30102-master 目录
            project_root = os.path.dirname(os.path.abspath(sys.executable))
        else:
            # 开发环境：使用项目根目录
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        max30102_path = os.path.join(project_root, "max30102-master")
        if max30102_path not in sys.path:
            sys.path.insert(0, max30102_path)
            print(f"[DEBUG] 已添加传感器库路径: {max30102_path}")
        
        # 导入传感器库
        try:
            from max30102 import MAX30102
            from hrcalc import calc_hr_and_spo2
            import numpy as np
        except ImportError as e:
            self.measure_error.emit(f"无法导入传感器库: {str(e)}\n请确保已安装依赖: pip install numpy smbus2")
            return
        
        # 初始化传感器
        sensor = None
        try:
            i2c_bus = Config.I2C_BUS
            i2c_address = Config.MAX30102_I2C_ADDRESS
            print(f"[DEBUG] 正在初始化 MAX30102: I2C总线={i2c_bus}, 地址=0x{i2c_address:02X}")
            sensor = MAX30102(channel=i2c_bus, address=i2c_address)
            print(f"[DEBUG] 传感器初始化成功")
        except FileNotFoundError as e:
            self.measure_error.emit(f"I2C 设备不存在: {str(e)}\n请检查:\n1. 是否运行在 Linux 系统\n2. I2C 模块是否加载 (lsmod | grep i2c)\n3. 设备文件是否存在 (ls /dev/i2c-*)")
            return
        except PermissionError as e:
            self.measure_error.emit(f"I2C 权限不足: {str(e)}\n请执行: sudo chmod 666 /dev/i2c-{i2c_bus}\n或添加用户到 i2c 组: sudo usermod -aG i2c $USER")
            return
        except OSError as e:
            error_msg = str(e).lower()
            if "remote i/o" in error_msg or "remote io" in error_msg:
                self.measure_error.emit(f"I2C 远程通信错误: 无法连接到地址 0x{i2c_address:02X}\n请检查:\n1. 传感器接线是否正确 (SDA/SCL/VCC/GND)\n2. 传感器是否损坏\n3. I2C 地址是否正确 (默认 0x57)\n4. 执行 i2cdetect -y {i2c_bus} 查看设备")
            else:
                self.measure_error.emit(f"I2C 错误: {str(e)}\n请检查硬件连接和系统配置")
            return
        except Exception as e:
            self.measure_error.emit(f"传感器初始化失败: {type(e).__name__}: {str(e)}\n请检查硬件连接和I2C配置")
            return
        
        # 使用 try/finally 确保传感器正确关闭
        try:
            required_readings = 5  # 采集5次有效读数，去除最大最小后取平均
            valid_readings = 0
            hr_list = []
            spo2_list = []
            start_time = time.time()
            finger_reported = False
            
            while self._running:
                if time.time() - start_time > self.timeout_total:
                    self.measure_timeout.emit()
                    break
                
                # 读取原始数据（100个样本用于计算）
                try:
                    red_buf, ir_buf = sensor.read_sequential(amount=100)
                except (TimeoutError, OSError) as e:
                    self.measure_error.emit(f"I2C 通信错误: {str(e)}，尝试重新初始化...")
                    break  # 退出循环，外层 finally 会关闭传感器
                
                if len(red_buf) < 100 or len(ir_buf) < 100:
                    time.sleep(0.3)
                    continue
                
                # 转换为 numpy 数组
                ir_data = np.array(ir_buf)
                red_data = np.array(red_buf)
                
                # 手指检测：信号强度阈值判断
                if np.mean(ir_data) < 50000:
                    # 未检测到手指 - 始终发送 finger_lost 信号
                    print(f"[DEBUG] 未检测到手指 (IR强度: {np.mean(ir_data):.0f})，发送 finger_lost 信号")
                    self.finger_lost.emit()
                    finger_reported = False
                    time.sleep(0.5)
                    continue
                
                # 检测到手指
                if not finger_reported:
                    print(f"[DEBUG] 检测到手指 (IR强度: {np.mean(ir_data):.0f})，发送 finger_detected 信号")
                    self.finger_detected.emit()
                    finger_reported = True
                
                # 计算心率和血氧
                hr, hr_valid, spo2, spo2_valid = calc_hr_and_spo2(ir_data, red_data)
                
                # 验证数据有效性（更严格的范围判断）
                if hr_valid and spo2_valid and 40 <= hr <= 200 and 90 <= spo2 <= 100:
                    # 应用心率校准系数（修正算法系统性偏高问题）
                    hr_calibrated = hr * 0.85
                    
                    hr_rounded = round(hr_calibrated, 0)
                    spo2_rounded = round(spo2, 1)
                    
                    self.data_updated.emit(hr_rounded, spo2_rounded)
                    valid_readings += 1
                    hr_list.append(hr_rounded)
                    spo2_list.append(spo2_rounded)
                    
                    if valid_readings >= required_readings:
                        # 去除最大值和最小值后取平均
                        hr_sorted = sorted(hr_list)
                        spo2_sorted = sorted(spo2_list)
                        
                        # 去掉第一个（最小）和最后一个（最大）
                        hr_trimmed = hr_sorted[1:-1]
                        spo2_trimmed = spo2_sorted[1:-1]
                        
                        avg_hr = round(sum(hr_trimmed) / len(hr_trimmed), 0)
                        avg_spo2 = round(sum(spo2_trimmed) / len(spo2_trimmed), 1)
                        
                        print(f"[DEBUG] 最终结果 - 心率:{avg_hr}, 血氧:{avg_spo2} (基于{len(hr_trimmed)}次有效数据)")
                        self.measure_finished.emit(avg_hr, avg_spo2)
                        break
                
                time.sleep(0.5)
        
        finally:
            # 确保传感器始终被关闭，避免 I2C 总线死锁
            if sensor:
                sensor.shutdown()

    def stop(self):
        self._running = False
        self.wait(2000)
