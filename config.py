import imaplib
import email
from email.mime.text import MIMEText
import sqlite3

def get_mail_summary():
    # 连接到IMAP服务器
    mail = imaplib.IMAP4_SSL('imap.gmail.com')
    mail.login('your_email@gmail.com', 'your_password')
    mail.select('INBOX')
    
    # 搜索邮件
    result, data = mail.search(None, 'ALL')
    
    # 获取邮件内容
    for num in data[0].split():
        typ, msg_data = mail.fetch(num, '(RFC822)')
        msg = email.message_from_bytes(msg_data[0][1])
        
        # 解析邮件信息
        subject = msg['Subject']
        body = msg.get_payload()
        
        # 打印邮件摘要
        print(f"主题: {subject}")
        print(f"发件人: {msg['From']}")
        print(f"内容摘要:")
        print(body)
        
        # 提取待办事项
        if '待办' in body.lower():
            todos = []
            for line in body.split('\n'):
                if '任务' in line or 'todo' in line:
                    todos.append(line.strip())
            
            print("待办事项列表:")
            for todo in todos:
                print(f"- {todo}")
    
    # 保存到数据库
    conn = sqlite3.connect('mail_summary.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS mail_summary
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  subject TEXT,
                  sender TEXT,
                  received_date TIMESTAMP,
                  summary TEXT,
                  todos TEXT)''')
    conn.commit()
    
    # 创建配置界面
    import sys
    from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton
    
    app = QApplication(sys.argv)
    window = QWidget()
    layout = QVBoxLayout()
    
    # 创建输入框
    email_edit = QLineEdit()
    password_edit = QLineEdit()
    password_edit.setEchoMode(QLineEdit.Password)
    
    # 连接测试按钮
    test_button = QPushButton('测试连接')
    
    # 显示区域
    summary_label = QLabel('邮件摘要:')
    todos_label = QLabel('待办事项:')
    
    layout.addWidget(email_edit)
    layout.addWidget(password_edit)
    layout.addWidget(test_button)
    
    # 处理函数
    def process_emails():
        # 连接到IMAP服务器
        mail = imaplib.IMAP4_SSL('imap.gmail.com')
        mail.login(email_edit.text(), password_edit.text())
        mail.select('INBOX')
        
        # 搜索并处理邮件
        result, data = mail.search(None, 'ALL')
        
        # 显示结果
        for num in data[0].split():
            typ, msg_data = mail.fetch(num, '(RFC822)')
            msg = email.message_from_bytes(msg_data[0][1])
            
            # 显示摘要
            print(f"主题: {msg['Subject']}")
            print(f"发件人: {msg['From']}")
            print(f"内容摘要:")
            print(msg.get_payload())
            
            # 提取待办事项
            todos = []
            body_lower = msg.get_payload().lower()
            for line in body_lower.split('\n'):
                if '待办' in line or 'todo' in line:
                    todos.append(line.strip())
            
            print("待办事项列表:")
            for todo in todos:
                print(f"- {todo}")
        
        # 保存到数据库
        c.execute('''INSERT INTO mail_summary (subject, sender, received_date, summary, todos)
                   VALUES (?, ?, ?, ?)''',
                   (subject, sender, received_date, summary, '\n'.join(todos)))
        conn.commit()
        
        # 显示结果
        window.show()
    
    sys.exit(app.exec_())

# 运行应用
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window.show()
    sys.exit(app.exec_())