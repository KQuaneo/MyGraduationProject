"""
PCA9685 共享管理器
解决多个模块同时访问 PCA9685 导致的冲突问题
"""
import time
import board
from adafruit_pca9685 import PCA9685

class PCA9685Manager:
    """PCA9685 单例管理器，确保整个程序只创建一个实例"""
    _instance = None
    _pca = None
    _initialized = False
    
    @classmethod
    def get_instance(cls):
        """获取 PCA9685 实例（单例模式）"""
        if cls._pca is None:
            try:
                i2c = board.I2C()
                cls._pca = PCA9685(i2c)
                cls._pca.frequency = 50  # 舵机标准频率 50Hz
                cls._initialized = True
                print("🔌 PCA9685 共享实例已创建")
            except Exception as e:
                print(f"❌ PCA9685 初始化失败: {e}")
                cls._initialized = False
                raise
        return cls._pca
    
    @classmethod
    def get_channel(cls, channel_index):
        """获取指定通道"""
        if not isinstance(channel_index, int) or channel_index < 0 or channel_index > 15:
            raise ValueError(f"通道索引必须在 0-15 之间，当前: {channel_index}")
        pca = cls.get_instance()
        return pca.channels[channel_index]
    
    @classmethod
    def reset_all_channels(cls):
        """重置所有通道为 0（关闭舵机）"""
        if cls._pca is not None:
            print("🔌 正在重置所有舵机通道...")
            for i in range(16):
                try:
                    cls._pca.channels[i].duty_cycle = 0
                except Exception as e:
                    print(f"  通道 {i} 重置失败: {e}")
            time.sleep(0.1)
    
    @classmethod
    def deinit(cls):
        """释放 PCA9685 资源，关闭所有通道输出防止舵机异响"""
        if cls._pca is not None:
            cls.reset_all_channels()
            
            try:
                cls._pca.deinit()
            except Exception as e:
                print(f"⚠️ PCA9685 deinit 出错: {e}")
            
            cls._pca = None
            cls._initialized = False
            print("🔌 PCA9685 已释放")

# 便捷函数
def get_pca():
    """获取 PCA9685 实例"""
    return PCA9685Manager.get_instance()

def get_channel(channel_index):
    """获取指定通道"""
    return PCA9685Manager.get_channel(channel_index)
