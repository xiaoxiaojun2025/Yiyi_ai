"""
AI 智能问诊助手 - 设计规范 & 全局样式
============================================================
参考: ChatGPT / Claude Desktop / Figma AI Chat UI Kit

【配色系统】
  主色:     #4A90D9 (品牌蓝)
  辅助色:   #5BA0E0 (亮蓝)  /  #357ABD (深蓝)
  中性色:   #333333(主文字) /  #666666(副文字) /  #999999(弱文字) /  #CCCCCC(禁用)
  背景:     #F5F5F5(页面)  /  #FFFFFF(卡片)  /  #F0F2F5(消息区)
  边框:     #E0E0E0(默认)  /  #E9ECEF(卡片)

【字体字号】
  标题 H1:  20px bold
  标题 H2:  16px bold
  正文:     14px regular
  辅助文字: 12px regular
  时间戳:   11px regular

【圆角规范】
  小按钮:   6px
  卡片/输入框: 10px
  消息气泡:  16px (对角 4px)
  发送按钮:  20px (胶囊形)

【阴影】
  卡片阴影: 0 2px 8px rgba(0,0,0,0.08)
  悬浮阴影: 0 4px 16px rgba(0,0,0,0.12)

【间距规范】
  页面边距:  16px
  卡片内距:  12px
  元素间距:  8px
  区块间距:  16px
============================================================
"""

MAIN_STYLE = """
/* ============================================================
   全局基础
   ============================================================ */
QMainWindow {
    background-color: #f5f5f5;
}

/* ============================================================
   侧边栏
   ============================================================ */
#sidebar {
    background-color: #ffffff;
    border-right: 1px solid #e0e0e0;
}

#sidebar_title {
    font-size: 16px;
    font-weight: bold;
    color: #333333;
    padding: 12px 8px;
}

/* 新对话按钮 */
#new_chat_btn {
    background-color: #4a90d9;
    color: white;
    border: none;
    border-radius: 10px;
    padding: 10px;
    font-size: 14px;
    font-weight: bold;
}

#new_chat_btn:hover {
    background-color: #357abd;
}

/* 对话列表项 */
#conversation_title {
    font-size: 13px;
    color: #333333;
    font-weight: 500;
}

#conversation_time {
    font-size: 11px;
    color: #999999;
}

/* ============================================================
   聊天区域
   ============================================================ */
#chat_header {
    background-color: #ffffff;
    border-bottom: 1px solid #e0e0e0;
}

/* 菜单按钮 */
#menu_btn {
    border: none;
    font-size: 20px;
    padding: 6px;
    background: transparent;
    border-radius: 6px;
}

#menu_btn:hover {
    background-color: #e8e8e8;
}

/* 聊天标题 */
#chat_title {
    font-size: 18px;
    font-weight: bold;
    color: #333333;
}

/* ============================================================
   消息区域
   ============================================================ */
#message_area {
    background-color: #f0f2f5;
}

/* 欢迎界面 */
#welcome_container {
    background-color: transparent;
}

#welcome_title {
    font-size: 24px;
    font-weight: bold;
    color: #333333;
}

#welcome_subtitle {
    font-size: 14px;
    color: #888888;
}

/* ============================================================
   消息气泡
   ============================================================ */
/* 用户消息 - 右对齐，品牌蓝背景 */
#user_message {
    background-color: #4a90d9;
    color: white;
    border-radius: 16px 16px 4px 16px;
    padding: 12px 16px;
    font-size: 14px;
}

/* AI消息 - 左对齐，白色卡片 */
#ai_message {
    background-color: #ffffff;
    color: #333333;
    border-radius: 16px 16px 16px 4px;
    padding: 12px 16px;
    font-size: 14px;
    border: 1px solid #e0e0e0;
}

/* AI消息 Markdown 渲染 */
#ai_message_md {
    background-color: #ffffff;
    color: #333333;
    border-radius: 16px 16px 16px 4px;
    padding: 12px 16px;
    font-size: 14px;
    border: 1px solid #e0e0e0;
    selection-background-color: #4a90d9;
    selection-color: white;
}

#ai_message_md QScrollBar:vertical {
    width: 0px;
}

/* AI标签 */
#ai_label {
    font-size: 12px;
    color: #4a90d9;
    font-weight: bold;
}

/* ============================================================
   等待动画
   ============================================================ */
#typing_indicator {
    background-color: transparent;
}

/* ============================================================
   输入区域
   ============================================================ */
#input_area {
    background-color: #ffffff;
    border-top: 1px solid #e0e0e0;
    padding: 12px 16px;
}

/* 输入框 */
#input_field {
    border: 2px solid #e0e0e0;
    border-radius: 20px;
    padding: 10px 16px;
    font-size: 14px;
    background-color: #f8f9fa;
}

#input_field:focus {
    border-color: #4a90d9;
    background-color: #ffffff;
}

/* 发送按钮 */
#send_btn {
    background-color: #4a90d9;
    color: white;
    border: none;
    border-radius: 20px;
    padding: 10px 20px;
    font-size: 14px;
    font-weight: bold;
}

#send_btn:hover {
    background-color: #357abd;
}

#send_btn:disabled {
    background-color: #cccccc;
}

/* ============================================================
   滚动条
   ============================================================ */
QScrollBar:vertical {
    width: 6px;
    background: transparent;
}

QScrollBar::handle:vertical {
    background: #cccccc;
    border-radius: 3px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background: #aaaaaa;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: transparent;
}

/* ============================================================
   错误提示条
   ============================================================ */
#error_bar {
    background-color: #fee2e2;
    color: #dc2626;
    border-top: 1px solid #fca5a5;
    padding: 8px 16px;
    font-size: 13px;
    font-weight: 500;
}

/* ============================================================
   切换测量按钮
   ============================================================ */
#switch_measure_btn {
    background-color: transparent;
    color: #e74c3c;
    border: 2px solid #e74c3c;
    border-radius: 18px;
    padding: 6px 16px;
    font-size: 13px;
    font-weight: bold;
}

#switch_measure_btn:hover {
    background-color: #e74c3c;
    color: white;
}

/* ============================================================
   测量页面
   ============================================================ */
#measure_content {
    background-color: #f0f2f5;
}

/* 测量数据卡片 */
#measure_card {
    background-color: white;
    border-radius: 16px;
    border: 1px solid #e0e0e0;
    padding: 20px;
}

#measure_card_title {
    font-size: 14px;
    color: #666666;
    font-weight: 500;
}

#measure_card_value {
    font-size: 48px;
    font-weight: bold;
    color: #333333;
}

#measure_card_unit {
    font-size: 14px;
    color: #999999;
}

/* 测量时间 */
#measure_time {
    font-size: 13px;
    color: #999999;
}

/* 测量状态 */
#measure_status {
    font-size: 14px;
    color: #666666;
    font-weight: 500;
}

/* 测量按钮 */
#measure_btn {
    background-color: #e74c3c;
    color: white;
    border: none;
    border-radius: 30px;
    padding: 10px 30px;
    font-size: 16px;
    font-weight: bold;
}

#measure_btn:hover {
    background-color: #c0392b;
}

#measure_btn:pressed {
    background-color: #a93226;
}

/* 测量中止按钮 */
#measure_btn_stop {
    background-color: #95a5a6;
    color: white;
    border: none;
    border-radius: 30px;
    padding: 10px 30px;
    font-size: 16px;
    font-weight: bold;
}

#measure_btn_stop:hover {
    background-color: #7f8c8d;
}

#measure_btn_stop:pressed {
    background-color: #6c7a7d;
}

/* ============================================================
   导出按钮
   ============================================================ */
#export_btn {
    background-color: transparent;
    border: none;
    font-size: 16px;
    padding: 4px;
    border-radius: 4px;
}

#export_btn:hover {
    background-color: #e8e8e8;
}

#export_btn:pressed {
    background-color: #d0d0d0;
}
"""
