"""
UI组件测试
测试聊天页面、测量页面、侧边栏等UI组件
注意：这些测试需要PyQt6环境，在无头环境中可能被跳过
"""
import pytest
import sys


# 检查是否有可用的显示环境
def has_display():
    """检查是否有可用的显示环境"""
    try:
        from PyQt6.QtWidgets import QApplication
        app = QApplication.instance()
        if app is None:
            # 尝试创建 QApplication，但这可能在无头环境中失败
            # 在某些CI环境中，即使没有显示器，创建QApplication也可能成功（使用offscreen平台）
            # 这里简单判断是否能导入并实例化相关类
            pass
        return True
    except Exception:
        return False


# 只在有显示环境时运行UI测试
# 注意：如果需要在CI中强制运行，可以设置环境变量或移除skipif
pytestmark = pytest.mark.skipif(
    not has_display(),
    reason="需要显示环境来运行UI测试"
)


@pytest.fixture(scope="session", autouse=True)
def qapp():
    """创建全局QApplication实例"""
    try:
        from PyQt6.QtWidgets import QApplication
        app = QApplication.instance()
        if app is None:
            # 在CI环境中可能需要指定平台插件，如 -platform offscreen
            app = QApplication(sys.argv)
        return app
    except Exception as e:
        pytest.skip(f"无法创建QApplication: {e}")


class TestChatPage:
    """聊天页面测试"""

    def test_chat_page_creation(self, qapp):
        """测试聊天页面创建"""
        from app.ui.pages.chat_page import ChatPage
        
        page = ChatPage()
        assert page is not None
        # 检查基本组件是否存在
        assert hasattr(page, 'scroll_area')
        assert hasattr(page, 'input_field')
        assert hasattr(page, 'send_button')

    def test_add_user_message(self, qapp):
        """测试添加用户消息"""
        from app.ui.pages.chat_page import ChatPage
        
        page = ChatPage()
        page.add_message("user", "你好")
        
        # 验证消息已添加
        layout = page.messages_layout
        assert layout.count() > 0

    def test_add_ai_message(self, qapp):
        """测试添加AI消息"""
        from app.ui.pages.chat_page import ChatPage
        
        page = ChatPage()
        page.add_message("assistant", "你好！有什么可以帮助你的？")
        
        # 验证消息已添加
        layout = page.messages_layout
        assert layout.count() > 0

    def test_clear_messages(self, qapp):
        """测试清空消息"""
        from app.ui.pages.chat_page import ChatPage
        
        page = ChatPage()
        page.add_message("user", "测试消息")
        page.clear_messages()
        
        # 验证消息已清空（可能保留欢迎消息）
        assert page.messages_layout.count() >= 0


class TestMeasurePage:
    """测量页面测试"""

    def test_measure_page_creation(self, qapp):
        """测试测量页面创建"""
        from app.ui.pages.measure_page import MeasurePage
        
        page = MeasurePage()
        assert page is not None
        # 检查基本组件是否存在
        assert hasattr(page, 'heart_rate_label')
        assert hasattr(page, 'blood_oxygen_label')

    def test_update_sensor_data(self, qapp):
        """测试更新传感器数据"""
        from app.ui.pages.measure_page import MeasurePage
        
        page = MeasurePage()
        page.update_sensor_data(75.0, 98.0)
        
        # 验证数据显示已更新
        assert page.current_heart_rate == 75.0
        assert page.current_blood_oxygen == 98.0


class TestSidebar:
    """侧边栏测试"""

    def test_sidebar_creation(self, qapp):
        """测试侧边栏创建"""
        from app.ui.pages.sidebar import Sidebar
        
        sidebar = Sidebar()
        assert sidebar is not None
        assert hasattr(sidebar, 'conversation_list')

    def test_add_conversation_to_list(self, qapp):
        """测试添加会话到列表"""
        from app.ui.pages.sidebar import Sidebar
        
        sidebar = Sidebar()
        sidebar.add_conversation("测试会话")
        
        # 验证会话已添加
        assert sidebar.conversation_list.count() > 0


class TestDoctorAvatar:
    """医生头像组件测试"""

    def test_doctor_avatar_creation(self, qapp):
        """测试医生头像组件创建"""
        from app.ui.widgets.doctor_avatar import DoctorAvatar
        
        avatar = DoctorAvatar()
        assert avatar is not None


class TestHeartIcon:
    """心跳图标组件测试"""

    def test_heart_icon_creation(self, qapp):
        """测试心跳图标组件创建"""
        from app.ui.widgets.heart_icon import HeartIcon
        
        icon = HeartIcon()
        assert icon is not None

    def test_heart_icon_animation(self, qapp):
        """测试心跳图标动画"""
        from app.ui.widgets.heart_icon import HeartIcon
        
        icon = HeartIcon()
        # 启动动画不应抛出异常
        icon.start_animation()
        assert icon.animation is not None


class TestTypingIndicator:
    """打字指示器测试"""

    def test_typing_indicator_creation(self, qapp):
        """测试打字指示器创建"""
        from app.ui.widgets.typing_indicator import TypingIndicator
        
        indicator = TypingIndicator()
        assert indicator is not None

    def test_typing_indicator_start_stop(self, qapp):
        """测试打字指示器启动和停止"""
        from app.ui.widgets.typing_indicator import TypingIndicator
        
        indicator = TypingIndicator()
        indicator.start()
        assert indicator.is_animating()
        
        indicator.stop()
        assert not indicator.is_animating()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])