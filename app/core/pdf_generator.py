"""
PDF报告生成模块
"""
import os
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from config.config import Config


class PDFReportGenerator:
    """PDF报告生成器"""
    
    def __init__(self):
        # 注册中文字体（使用系统字体）
        try:
            # Windows系统字体路径
            font_path = "C:/Windows/Fonts/simhei.ttf"  # 黑体
            if os.path.exists(font_path):
                pdfmetrics.registerFont(TTFont('SimHei', font_path))
                self.chinese_font = 'SimHei'
            else:
                # 备用方案：尝试其他字体
                font_path = "C:/Windows/Fonts/msyh.ttc"  # 微软雅黑
                if os.path.exists(font_path):
                    pdfmetrics.registerFont(TTFont('MSYH', font_path))
                    self.chinese_font = 'MSYH'
                else:
                    self.chinese_font = 'Helvetica'  # fallback
        except Exception as e:
            print(f"[PDF] 字体加载失败: {e}，使用默认字体")
            self.chinese_font = 'Helvetica'
        
        self.styles = getSampleStyleSheet()
        self._setup_styles()
    
    def _setup_styles(self):
        """设置自定义样式"""
        # 标题样式
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontName=self.chinese_font,
            fontSize=24,
            textColor=colors.HexColor('#4A90D9'),
            alignment=TA_CENTER,
            spaceAfter=20
        ))
        
        # 副标题样式
        self.styles.add(ParagraphStyle(
            name='CustomSubtitle',
            parent=self.styles['Heading2'],
            fontName=self.chinese_font,
            fontSize=16,
            textColor=colors.HexColor('#333333'),
            spaceAfter=10,
            spaceBefore=15
        ))
        
        # 正文样式
        self.styles.add(ParagraphStyle(
            name='CustomBody',
            parent=self.styles['Normal'],
            fontName=self.chinese_font,
            fontSize=12,
            textColor=colors.HexColor('#333333'),
            leading=20,
            spaceAfter=8
        ))
        
        # 标签样式
        self.styles.add(ParagraphStyle(
            name='CustomLabel',
            parent=self.styles['Normal'],
            fontName=self.chinese_font,
            fontSize=12,
            textColor=colors.HexColor('#666666'),
            leading=18
        ))
        
        # 用户消息样式
        self.styles.add(ParagraphStyle(
            name='UserMessage',
            parent=self.styles['Normal'],
            fontName=self.chinese_font,
            fontSize=11,
            textColor=colors.HexColor('#4A90D9'),
            leftIndent=20,
            leading=18,
            spaceAfter=5
        ))
        
        # AI消息样式
        self.styles.add(ParagraphStyle(
            name='AIMessage',
            parent=self.styles['Normal'],
            fontName=self.chinese_font,
            fontSize=11,
            textColor=colors.HexColor('#333333'),
            leftIndent=20,
            rightIndent=20,
            leading=18,
            spaceAfter=10
        ))
        
        # 免责声明样式
        self.styles.add(ParagraphStyle(
            name='Disclaimer',
            parent=self.styles['Normal'],
            fontName=self.chinese_font,
            fontSize=9,
            textColor=colors.HexColor('#999999'),
            alignment=TA_CENTER,
            leading=14,
            spaceBefore=20
        ))
    
    def generate_report(self, conversation, output_path: str) -> bool:
        """
        生成PDF报告
        
        Args:
            conversation: Conversation对象
            output_path: 输出文件路径
            
        Returns:
            bool: 是否成功生成
        """
        try:
            doc = SimpleDocTemplate(
                output_path,
                pagesize=A4,
                rightMargin=2*cm,
                leftMargin=2*cm,
                topMargin=2*cm,
                bottomMargin=2*cm
            )
            
            story = []
            
            # 1. 标题
            story.append(Paragraph("AI智能健康问诊报告", self.styles['CustomTitle']))
            story.append(Spacer(1, 0.5*cm))
            
            # 2. 基本信息
            story.append(Paragraph("基本信息", self.styles['CustomSubtitle']))
            
            info_data = [
                ["会话标题:", conversation.title],
                ["创建时间:", conversation.created_at],
                ["更新时间:", conversation.updated_at],
            ]
            
            if conversation.last_measured_at:
                info_data.append(["测量时间:", conversation.last_measured_at])
            
            info_table = Table(info_data, colWidths=[3*cm, 12*cm])
            info_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), self.chinese_font),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#666666')),
                ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#333333')),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ]))
            story.append(info_table)
            story.append(Spacer(1, 0.5*cm))
            
            # 3. 检测数据
            if conversation.heart_rate or conversation.blood_oxygen:
                story.append(Paragraph("检测数据", self.styles['CustomSubtitle']))
                
                health_data = []
                if conversation.heart_rate:
                    health_data.append(["心率", f"{conversation.heart_rate:.0f} BPM", 
                                       "正常" if 60 <= conversation.heart_rate <= 100 else "异常"])
                if conversation.blood_oxygen:
                    health_data.append(["血氧饱和度", f"{conversation.blood_oxygen:.1f}%",
                                       "正常" if conversation.blood_oxygen >= 95 else "偏低"])
                
                if health_data:
                    health_table = Table(health_data, colWidths=[4*cm, 4*cm, 3*cm])
                    health_table.setStyle(TableStyle([
                        ('FONTNAME', (0, 0), (-1, -1), self.chinese_font),
                        ('FONTSIZE', (0, 0), (-1, -1), 11),
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F0F2F5')),
                        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#333333')),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E0E0E0')),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                        ('TOPPADDING', (0, 0), (-1, -1), 10),
                    ]))
                    story.append(health_table)
                    story.append(Spacer(1, 0.5*cm))
            
            # 4. 问诊记录
            if conversation.messages:
                story.append(Paragraph("问诊记录", self.styles['CustomSubtitle']))
                story.append(Spacer(1, 0.3*cm))
                
                for msg in conversation.messages:
                    role = msg.get('role', '')
                    content = msg.get('content', '')
                    
                    if role == 'user':
                        story.append(Paragraph(f"<b>【用户】</b> {content}", self.styles['UserMessage']))
                    elif role in ('ai', 'assistant'):
                        # 处理Markdown简单转换
                        formatted_content = self._format_ai_message(content)
                        story.append(Paragraph(formatted_content, self.styles['AIMessage']))
                
                story.append(Spacer(1, 0.5*cm))
            
            # 5. 免责声明
            disclaimer = (
                "免责声明：本报告由AI生成，仅供参考，不能替代专业医疗诊断。"
                "如有严重不适，请立即就医或拨打急救电话120。"
            )
            story.append(Paragraph(disclaimer, self.styles['Disclaimer']))
            
            # 生成PDF
            doc.build(story)
            print(f"[PDF] 报告生成成功: {output_path}")
            return True
            
        except Exception as e:
            print(f"[PDF] 报告生成失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _format_ai_message(self, content: str) -> str:
        """
        格式化AI消息（处理Markdown语法）
        
        Args:
            content: 原始Markdown内容
            
        Returns:
            格式化后的HTML字符串
        """
        import re
        
        # 转义特殊字符（先保护HTML标签）
        content = content.replace('&', '&amp;')
        
        # 处理标题 (###, ##, #)
        content = re.sub(r'^###\s+(.+)$', r'<b><font size="4">\1</font></b>', content, flags=re.MULTILINE)
        content = re.sub(r'^##\s+(.+)$', r'<b><font size="5">\1</font></b>', content, flags=re.MULTILINE)
        content = re.sub(r'^#\s+(.+)$', r'<b><font size="6">\1</font></b>', content, flags=re.MULTILINE)
        
        # 处理加粗 **text**
        content = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', content)
        
        # 处理斜体 *text*
        content = re.sub(r'\*(.+?)\*', r'<i>\1</i>', content)
        
        # 处理代码块 `code`
        content = re.sub(r'`([^`]+)`', r'<font color="#e74c3c">\1</font>', content)
        
        # 处理换行
        lines = content.split('\n')
        formatted_lines = []
        
        for line in lines:
            line_stripped = line.strip()
            
            if not line_stripped:
                formatted_lines.append('<br/>')
                continue
            
            # 处理列表项 - 或 * （在转义后处理）
            if line_stripped.startswith('- ') or line_stripped.startswith('* '):
                item_text = line_stripped[2:]  # 去掉 "- " 或 "* "
                formatted_lines.append(f'&nbsp;&nbsp;&bull; {item_text}')
            elif line_stripped.startswith('• '):
                item_text = line_stripped[2:]  # 去掉 "• "
                formatted_lines.append(f'&nbsp;&nbsp;&bull; {item_text}')
            # 处理数字列表 1. 2. 等
            elif re.match(r'^\d+\.\s+', line_stripped):
                formatted_lines.append(f'<b>{line_stripped}</b>')
            else:
                formatted_lines.append(line_stripped)
        
        return '<br/>'.join(formatted_lines)
