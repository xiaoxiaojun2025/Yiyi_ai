"""
真实MAX30102传感器测试
直接测试传感器驱动，验证硬件连接和数据准确性
注意：需要飞腾派开发板和MAX30102传感器硬件
"""
import pytest
import time


@pytest.mark.skip(reason="需要真实MAX30102硬件和I2C支持")
class TestRealMAX30102:
    """真实MAX30102传感器测试类"""

    def test_i2c_connection(self):
        """测试I2C连接"""
        print("\n=== I2C连接测试 ===")
        
        try:
            import smbus
            bus = smbus.SMBus(1)  # Raspberry Pi使用I2C bus 1
            
            # MAX30102默认地址
            address = 0x57
            
            # 尝试读取ID寄存器
            part_id = bus.read_byte_data(address, 0xFF)
            
            print(f"检测到设备，Part ID: 0x{part_id:02X}")
            
            # MAX30102的Part ID应该是0x15
            assert part_id == 0x15, f"错误的Part ID: 0x{part_id:02X}"
            
            print("✓ I2C连接成功")
            
        except Exception as e:
            print(f"✗ I2C连接失败: {e}")
            raise

    def test_sensor_initialization(self):
        """测试传感器初始化"""
        print("\n=== 传感器初始化测试 ===")
        
        try:
            from max30102_master.max30102 import MAX30102
            
            sensor = MAX30102()
            sensor.setup_sensor()
            
            print("✓ 传感器初始化成功")
            
            # 清理
            sensor.shutdown()
            
        except Exception as e:
            print(f"✗ 传感器初始化失败: {e}")
            raise

    def test_raw_data_reading(self):
        """测试原始数据读取"""
        print("\n=== 原始数据读取测试 ===")
        print("请将手指贴在传感器上...")
        
        try:
            from max30102_master.max30102 import MAX30102
            
            sensor = MAX30102()
            sensor.setup_sensor()
            
            # 读取100个样本
            samples = []
            for i in range(100):
                ir, red = sensor.read_sensor()
                samples.append((ir, red))
                
                if (i + 1) % 20 == 0:
                    print(f"样本 {i+1}: IR={ir}, RED={red}")
                
                time.sleep(0.05)  # 20Hz采样率
            
            sensor.shutdown()
            
            # 验证数据有效性
            assert len(samples) == 100
            
            # 检查数据范围（应该在合理范围内）
            ir_values = [ir for ir, _ in samples]
            red_values = [red for _, red in samples]
            
            print(f"\nIR范围: {min(ir_values)} - {max(ir_values)}")
            print(f"RED范围: {min(red_values)} - {max(red_values)}")
            
            # 如果手指放置正确，应该有明显的脉搏波形
            ir_variance = max(ir_values) - min(ir_values)
            print(f"IR方差: {ir_variance}")
            
            if ir_variance > 100:
                print("✓ 检测到脉搏信号")
            else:
                print("⚠ 未检测到明显脉搏信号，请调整手指位置")
            
        except Exception as e:
            print(f"✗ 原始数据读取失败: {e}")
            raise

    def test_heart_rate_calculation(self):
        """测试心率计算"""
        print("\n=== 心率计算测试 ===")
        print("请保持手指贴在传感器上10秒...")
        
        try:
            from max30102_master.hrcalc import calculate_hr
            
            # 收集10秒数据
            samples = []
            start_time = time.time()
            
            while time.time() - start_time < 10:
                ir, red = sensor.read_sensor()
                samples.append(ir)
                time.sleep(0.02)  # 50Hz
            
            print(f"收集到 {len(samples)} 个样本")
            
            # 计算心率
            hr = calculate_hr(samples)
            
            print(f"计算心率: {hr} BPM")
            
            # 验证心率范围
            if 40 <= hr <= 180:
                print("✓ 心率计算成功")
            else:
                print(f"⚠ 心率异常: {hr} BPM")
            
        except Exception as e:
            print(f"✗ 心率计算失败: {e}")
            raise

    def test_blood_oxygen_calculation(self):
        """测试血氧计算"""
        print("\n=== 血氧计算测试 ===")
        print("请同时使用医用血氧仪对比...")
        
        try:
            from max30102_master.hrcalc import calculate_spo2
            
            # 收集IR和RED数据
            ir_samples = []
            red_samples = []
            
            for i in range(500):  # 10秒@50Hz
                ir, red = sensor.read_sensor()
                ir_samples.append(ir)
                red_samples.append(red)
                time.sleep(0.02)
            
            # 计算血氧
            spo2 = calculate_spo2(ir_samples, red_samples)
            
            print(f"计算血氧: {spo2}%")
            
            # 验证血氧范围
            if 80 <= spo2 <= 100:
                print("✓ 血氧计算成功")
            else:
                print(f"⚠ 血氧异常: {spo2}%")
            
        except Exception as e:
            print(f"✗ 血氧计算失败: {e}")
            raise

    def test_sensor_stability(self):
        """测试传感器稳定性（长时间运行）"""
        print("\n=== 传感器稳定性测试（30秒）===")
        print("请保持手指稳定贴在传感器上...")
        
        try:
            heart_rates = []
            
            for second in range(30):
                # 每秒计算一次心率
                samples = []
                for _ in range(50):  # 1秒@50Hz
                    ir, red = sensor.read_sensor()
                    samples.append(ir)
                    time.sleep(0.02)
                
                hr = calculate_hr(samples)
                if hr > 0:
                    heart_rates.append(hr)
                
                if (second + 1) % 5 == 0:
                    avg_hr = sum(heart_rates[-5:]) / len(heart_rates[-5:]) if heart_rates[-5:] else 0
                    print(f"{second+1}秒 - 当前心率: {hr}, 最近5秒平均: {avg_hr:.1f}")
            
            # 分析稳定性
            if len(heart_rates) > 10:
                import statistics
                avg = statistics.mean(heart_rates)
                std = statistics.stdev(heart_rates)
                
                print(f"\n平均心率: {avg:.1f} BPM")
                print(f"标准差: {std:.2f}")
                
                if std < 5:
                    print("✓ 传感器非常稳定")
                elif std < 10:
                    print("✓ 传感器稳定性良好")
                else:
                    print(f"⚠ 传感器波动较大: {std:.2f}")
            
        except Exception as e:
            print(f"✗ 稳定性测试失败: {e}")
            raise

    def teardown_method(self, method):
        """每个测试后清理"""
        try:
            sensor.shutdown()
        except:
            pass


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])