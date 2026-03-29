# -*- coding: utf-8 -*-
"""修复邮件详情显示代码"""

import re

with open('src/ui/main_window.py', encoding='utf-8') as f:
    content = f.read()

# 修复 _on_email_selected 方法
old_on_email = '''    def _on_email_selected(self, item: QListWidgetItem):
        """邮件选中"""
        row = self.email_list.row(item)
        if 0 <= row < len(self.current_emails):
            email = self.current_emails[row]
            self._show_email_detail(email)
            self.email_selected.emit(email.id)'''

new_on_email = '''    def _on_email_selected(self, item: QListWidgetItem):
        """邮件选中"""
        row = self.email_list.row(item)
        if 0 <= row < len(self.current_emails):
            email = self.current_emails[row]
            self._show_email_detail(email)
            email_id = email.get('id')
            if email_id:
                self.email_selected.emit(email_id)'''

content = content.replace(old_on_email, new_on_email)

# 修复 _show_email_detail 方法
old_show_detail = '''    def _show_email_detail(self, email: EmailData):
        """显示邮件详情"""
        content = f"""
<b>发件人:</b> {email.sender}<br>
<b>收件人:</b> {email.recipient}<br>
<b>主题:</b> {email.subject}<br>
<b>时间:</b> {email.date}<br>
<hr>
{email.body}
:"""
        self.email_detail.setHtml(content)'''

new_show_detail = '''    def _show_email_detail(self, email: dict):
        """显示邮件详情
        
        Args:
            email: 邮件字典（来自 EmailRepo）
        """
        sender = email.get('sender', '(未知发件人)')
        sender_email = email.get('sender_email', '')
        recipients = email.get('recipients', '')
        subject = email.get('subject', '(无主题)')
        date = email.get('date', '')
        body_text = email.get('body_text', '')
        body_html = email.get('body_html', '')
        
        # 优先使用 HTML 正文，否则使用纯文本
        body_content = body_html if body_html else f"<pre>{body_text}</pre>"
        
        content = f"""
<h3>{subject}</h3>
<hr>
<p><b>发件人:</b> {sender} &lt;{sender_email}&gt;</p>
<p><b>收件人:</b> {recipients}</p>
<p><b>时间:</b> {date}</p>
<hr>
<div>{body_content}</div>
"""
        self.email_detail.setHtml(content)'''

content = content.replace(old_show_detail, new_show_detail)

with open('src/ui/main_window.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('修复完成')
