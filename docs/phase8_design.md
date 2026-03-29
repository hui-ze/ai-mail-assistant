# Phase 8: 待办分配与提醒功能设计

## 概述
Phase 8 基于部门协作功能，实现待办分配和智能提醒，帮助Leader更好地管理团队任务。

## 功能需求

### 1. 待办分配功能
- **分配待办**：Leader可将待办分配给团队成员
- **接受/拒绝**：成员可接受或拒绝分配的待办
- **分配历史**：记录待办分配的完整历史
- **通知机制**：分配时通知相关成员

### 2. 提醒功能
- **截止提醒**：待办即将到期时提醒
- **未读提醒**：新分配待办的未读提醒
- **自定义提醒**：用户可设置自定义提醒时间
- **提醒方式**：系统通知、邮件通知（可选）

## 数据库设计

### 新增表

#### 1. todo_assignments 表（待办分配）
```sql
CREATE TABLE todo_assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    todo_id INTEGER NOT NULL,
    from_member_id INTEGER NOT NULL,  -- 分配人
    to_member_id INTEGER NOT NULL,    -- 接收人
    status VARCHAR(20) DEFAULT 'pending',  -- pending/accepted/rejected/completed
    message TEXT,                     -- 分配说明
    response_message TEXT,            -- 接受/拒绝理由
    assigned_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    responded_at DATETIME,
    FOREIGN KEY (todo_id) REFERENCES todos(id),
    FOREIGN KEY (from_member_id) REFERENCES team_members(id),
    FOREIGN KEY (to_member_id) REFERENCES team_members(id)
);

CREATE INDEX idx_assignments_todo ON todo_assignments(todo_id);
CREATE INDEX idx_assignments_to_member ON todo_assignments(to_member_id);
CREATE INDEX idx_assignments_status ON todo_assignments(status);
```

#### 2. reminders 表（提醒）
```sql
CREATE TABLE reminders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    todo_id INTEGER,
    member_id INTEGER NOT NULL,
    reminder_type VARCHAR(50) NOT NULL,  -- due_date/custom/assignment
    remind_at DATETIME NOT NULL,
    is_sent BOOLEAN DEFAULT 0,
    message TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (todo_id) REFERENCES todos(id),
    FOREIGN KEY (member_id) REFERENCES team_members(id)
);

CREATE INDEX idx_reminders_member ON reminders(member_id);
CREATE INDEX idx_reminders_time ON reminders(remind_at);
CREATE INDEX idx_reminders_sent ON reminders(is_sent);
```

## 核心类设计

### 1. TodoAssignmentService
```python
class TodoAssignmentService:
    def assign_todo(todo_id, from_member_id, to_member_id, message) -> int
    def accept_assignment(assignment_id, response_message) -> bool
    def reject_assignment(assignment_id, response_message) -> bool
    def get_pending_assignments(member_id) -> List[Assignment]
    def get_assignment_history(todo_id) -> List[Assignment]
```

### 2. ReminderService
```python
class ReminderService:
    def create_reminder(todo_id, member_id, reminder_type, remind_at, message) -> int
    def get_pending_reminders(member_id) -> List[Reminder]
    def mark_reminder_sent(reminder_id) -> bool
    def check_and_trigger_reminders() -> List[Reminder]  # 后台任务
    def create_auto_reminders(todo_id) -> None  # 自动创建截止提醒
```

## UI 设计

### 1. 待办分配对话框
- 选择待办
- 选择团队成员
- 添加分配说明
- 查看分配历史

### 2. 待办接收面板
- 显示待处理的分配
- 接受/拒绝按钮
- 添加回复说明

### 3. 提醒管理界面
- 提醒列表
- 创建自定义提醒
- 提醒设置（提前时间）

### 4. 系统通知
- Windows系统托盘通知
- 应用内通知中心

## 技术要点

### 1. 分配流程
```
Leader选择待办 → 选择成员 → 填写说明 → 创建分配记录 → 
通知接收人 → 成员查看 → 接受/拒绝 → 更新状态 → 通知Leader
```

### 2. 提醒触发机制
- **定时检查**：每分钟检查一次待发送提醒
- **截止提醒**：提前1天、1小时、10分钟
- **未读提醒**：分配后未处理超过24小时

### 3. 通知方式
- **系统通知**：使用 plyer 库实现跨平台通知
- **应用内通知**：状态栏显示未读数量

## 测试计划

### 单元测试
- TodoAssignmentService 方法测试
- ReminderService 方法测试

### 集成测试
- 完整分配流程测试
- 提醒触发测试
- 数据库级联删除测试

## 开发计划

- **数据库层**：0.5天
- **服务层**：1天
- **UI层**：1天
- **测试**：0.5天
- **总计**：3人天

## 依赖

- `plyer` - 跨平台系统通知
- `schedule` - 定时任务调度（可选，可用QTimer替代）
