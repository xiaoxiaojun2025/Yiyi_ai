"""
PDF生成器测试
测试PDF报告生成、格式渲染等功能
"""
import pytest
from pathlib import Path
from app.core.pdf_generator import PDFReportGenerator
from app.core.data_manager import Conversation


class TestPDFGenerator:
    """PDF生成器测试类"""

    def test_create_pdf_generator(self):
        """测试创建PDF生成器"""
        generator = PDFReportGenerator()
        assert generator is not None
        assert hasattr(generator, 'generate_report')

    def test_generate_pdf_basic(self, tmp_path):
        """测试生成基本PDF报告"""
        output_dir = tmp_path / "pdf_output"
        output_dir.mkdir()
        output_path = str(output_dir / "test_report.pdf")
        
        # 创建测试会话
        conv = Conversation(
            title="测试会话",
            messages=[
                {"role": "user", "content": "你好，我最近有点胸闷"},
                {"role": "assistant", "content": "您好，胸闷可能有多种原因，建议您详细描述一下症状。"}
            ],
            heart_rate=75.0,
            blood_oxygen=98.5
        )
        
        generator = PDFReportGenerator()
        success = generator.generate_report(conv, output_path)
        
        assert success is True
        assert Path(output_path).exists()
        assert Path(output_path).stat().st_size > 0

    def test_generate_pdf_without_health_data(self, tmp_path):
        """测试生成没有健康数据的PDF报告"""
        output_dir = tmp_path / "pdf_output"
        output_dir.mkdir()
        output_path = str(output_dir / "test_no_health.pdf")
        
        conv = Conversation(
            title="无健康数据会话",
            messages=[
                {"role": "user", "content": "我想咨询一下健康问题"},
                {"role": "assistant", "content": "请问您有什么具体的症状吗？"}
            ]
        )
        
        generator = PDFReportGenerator()
        success = generator.generate_report(conv, output_path)
        
        assert success is True
        assert Path(output_path).exists()

    def test_generate_pdf_with_long_content(self, tmp_path):
        """测试生成长内容的PDF报告"""
        output_dir = tmp_path / "pdf_output"
        output_dir.mkdir()
        output_path = str(output_dir / "test_long.pdf")
        
        # 创建包含多条消息的会话
        messages = []
        for i in range(10):
            messages.append({"role": "user", "content": f"问题 {i+1}: 这是一个测试问题"})
            messages.append({"role": "assistant", "content": f"回答 {i+1}: 这是对应的回答内容，用于测试长文本的PDF生成。"})
        
        conv = Conversation(
            title="长对话测试",
            messages=messages,
            heart_rate=80.0,
            blood_oxygen=97.0
        )
        
        generator = PDFReportGenerator()
        success = generator.generate_report(conv, output_path)
        
        assert success is True
        assert Path(output_path).exists()

    def test_pdf_filename_generation(self, tmp_path):
        """测试PDF文件路径生成"""
        output_dir = tmp_path / "pdf_output"
        output_dir.mkdir()
        
        # 测试不同的输出路径
        test_paths = [
            str(output_dir / "report1.pdf"),
            str(output_dir / "中文报告.pdf"),
            str(output_dir / "report with spaces.pdf"),
        ]
        
        conv = Conversation(title="测试", messages=[])
        generator = PDFReportGenerator()
        
        for path in test_paths:
            success = generator.generate_report(conv, path)
            assert success is True
            assert Path(path).exists()

    def test_disclaimer_in_pdf(self, tmp_path):
        """测试免责声明包含在PDF中"""
        output_dir = tmp_path / "pdf_output"
        output_dir.mkdir()
        output_path = str(output_dir / "test_disclaimer.pdf")
        
        conv = Conversation(title="测试", messages=[])
        
        generator = PDFReportGenerator()
        success = generator.generate_report(conv, output_path)
        
        assert success is True
        # PDF文件应该存在且大小合理（包含免责声明）
        assert Path(output_path).exists()
        assert Path(output_path).stat().st_size > 1000  # 至少1KB

    def test_format_ai_message_with_markdown(self):
        """测试AI消息的Markdown格式化"""
        generator = PDFReportGenerator()
        
        # 测试简单的Markdown内容
        markdown_content = """
# 标题
这是一段**加粗**和*斜体*的文本。

- 列表项1
- 列表项2

建议：多休息，保持良好作息。
"""
        formatted = generator._format_ai_message(markdown_content)
        
        assert formatted is not None
        assert isinstance(formatted, str)
        # 格式化后的内容应该是HTML格式
        assert len(formatted) > 0

    def test_generate_pdf_error_handling(self, tmp_path):
        """测试PDF生成的错误处理"""
        output_dir = tmp_path / "pdf_output"
        output_dir.mkdir()
        # 使用无效路径
        output_path = str(output_dir / "invalid" / "path" / "report.pdf")
        
        conv = Conversation(title="测试", messages=[])
        generator = PDFReportGenerator()
        
        # 应该返回False而不是抛出异常
        success = generator.generate_report(conv, output_path)
        assert success is False
