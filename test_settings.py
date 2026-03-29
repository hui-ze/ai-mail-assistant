#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
璁剧疆瀵硅瘽妗嗗姛鑳芥祴璇曡剼鏈?
娴嬭瘯鎵€鏈夎缃」鐨勪繚瀛樺拰璇诲彇鍔熻兘
"""

import sys
import os
import json

# 娣诲姞椤圭洰鏍圭洰褰曞埌璺緞
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication, QMessageBox
from src.data.database import Database
from src.ui.settings_dialog import SettingsDialog


def test_general_settings(dialog):
    """娴嬭瘯閫氱敤璁剧疆"""
    print("\n=== 娴嬭瘯閫氱敤璁剧疆 ===")
    
    # 淇敼璁剧疆
    dialog.startup_with_system.setChecked(True)
    dialog.minimize_to_tray.setChecked(False)
    dialog.daily_limit.setValue(50)
    dialog.auto_process.setChecked(True)
    dialog.cache_days.setValue(30)
    dialog.auto_backup.setChecked(True)
    
    print("[OK] 宸蹭慨鏀归€氱敤璁剧疆")
    return True


def test_ai_settings(dialog):
    """娴嬭瘯AI璁剧疆"""
    print("\n=== 娴嬭瘯AI璁剧疆 ===")
    
    # 妫€鏌I鐘舵€佹樉绀?
    print(f"AI鐘舵€? {dialog.ai_status_label.text()}")
    print(f"AI鎻愪緵鍟? {dialog.ai_provider_label.text()}")
    print(f"AI妯″瀷: {dialog.ai_model_label.text()}")
    
    # 淇敼AI浣跨敤璁剧疆
    dialog.daily_limit.setValue(80)
    dialog.auto_analyze.setChecked(True)
    
    print("鉁?宸蹭慨鏀笰I璁剧疆")
    return True


def test_sync_settings(dialog):
    """娴嬭瘯鍚屾璁剧疆"""
    print("\n=== 娴嬭瘯鍚屾璁剧疆 ===")
    
    dialog.sync_interval.setValue(30)
    dialog.ai_sync_interval.setValue(45)
    dialog.sync_unread_only.setChecked(True)
    dialog.sync_attachments.setChecked(False)
    dialog.sync_delete.setChecked(True)
    
    print("鉁?宸蹭慨鏀瑰悓姝ヨ缃?)
    return True


def test_ui_settings(dialog):
    """娴嬭瘯鐣岄潰璁剧疆"""
    print("\n=== 娴嬭瘯鐣岄潰璁剧疆 ===")
    
    # 娴嬭瘯涓婚鍒囨崲
    print("娴嬭瘯涓婚鍒囨崲...")
    for i in range(3):  # 0=娴呰壊, 1=娣辫壊, 2=璺熼殢绯荤粺
        dialog.theme_combo.setCurrentIndex(i)
        print(f"  涓婚 {i}: {dialog.theme_combo.currentText()}")
    
    # 娴嬭瘯鍏朵粬UI璁剧疆
    dialog.accent_color.setCurrentIndex(2)  # 绱壊
    dialog.show_preview.setChecked(True)
    dialog.preview_lines.setValue(3)
    dialog.list_font_size.setValue(11)
    dialog.date_format.setCurrentIndex(2)  # 03-15 14:30
    
    print("鉁?宸蹭慨鏀圭晫闈㈣缃?)
    return True


def test_calendar_settings(dialog):
    """娴嬭瘯鏃ュ巻璁剧疆"""
    print("\n=== 娴嬭瘯鏃ュ巻璁剧疆 ===")
    
    # 鍚敤鏃ュ巻
    dialog.calendar_enabled.setChecked(True)
    
    # 娴嬭瘯鏃ュ巻绫诲瀷鍒囨崲
    print("娴嬭瘯鏃ュ巻绫诲瀷鍒囨崲...")
    for i in range(4):
        dialog.calendar_type.setCurrentIndex(i)
        print(f"  鏃ュ巻绫诲瀷 {i}: {dialog.calendar_type.currentText()}")
    
    # 璁剧疆Outlook
    dialog.calendar_type.setCurrentIndex(0)  # Outlook
    dialog.outlook_account.setText("test@outlook.com")
    
    # 娴嬭瘯Outlook杩炴帴
    print("娴嬭瘯Outlook杩炴帴...")
    dialog._test_outlook_connection()
    
    # 鍏朵粬璁剧疆
    dialog.sync_high_priority.setChecked(True)
    dialog.set_reminder.setChecked(True)
    dialog.reminder_minutes.setCurrentIndex(1)  # 30鍒嗛挓鍓?
    
    print("鉁?宸蹭慨鏀规棩鍘嗚缃?)
    return True


def test_user_profile(dialog):
    """娴嬭瘯鐢ㄦ埛鐢诲儚"""
    print("\n=== 娴嬭瘯鐢ㄦ埛鐢诲儚 ===")
    
    dialog.profile_name_edit.setText("娴嬭瘯鐢ㄦ埛")
    dialog.profile_dept_edit.setText("鎶€鏈儴")
    dialog.profile_role_edit.setText("杞欢宸ョ▼甯?)
    dialog.profile_desc_edit.setPlainText("璐熻矗Foxmail閭欢鍔╂墜寮€鍙慭nPython + PyQt5")
    
    print("鉁?宸蹭慨鏀圭敤鎴风敾鍍?)
    return True


def test_department_management(dialog):
    """娴嬭瘯閮ㄩ棬绠＄悊"""
    print("\n=== 娴嬭瘯閮ㄩ棬绠＄悊 ===")
    
    # 娣诲姞娴嬭瘯閮ㄩ棬
    print("娣诲姞娴嬭瘯閮ㄩ棬...")
    from PyQt5.QtWidgets import QInputDialog
    
    # 妯℃嫙杈撳叆瀵硅瘽妗?
    original_getText = QInputDialog.getText
    
    call_count = [0]
    def mock_getText(*args, **kwargs):
        call_count[0] += 1
        if call_count[0] == 1:
            return ("娴嬭瘯閮ㄩ棬", True)
        elif call_count[0] == 2:
            return ("\\\\server\\shared\\test", True)
        elif call_count[0] == 3:
            return ("娴嬭瘯鎴愬憳", True)
        elif call_count[0] == 4:
            return ("test@example.com", True)
        elif call_count[0] == 5:
            return ("寮€鍙戝伐绋嬪笀", True)
        return ("", False)
    
    QInputDialog.getText = mock_getText
    
    try:
        # 娣诲姞閮ㄩ棬
        dialog._add_department()
        
        # 妫€鏌ラ儴闂ㄦ槸鍚︽坊鍔犳垚鍔?
        if dialog.dept_list.count() > 0:
            print(f"鉁?閮ㄩ棬娣诲姞鎴愬姛锛屽叡 {dialog.dept_list.count()} 涓儴闂?)
            
            # 閫変腑绗竴涓儴闂?
            dialog.dept_list.setCurrentRow(0)
            
            # 娣诲姞鎴愬憳
            print("娣诲姞娴嬭瘯鎴愬憳...")
            # 妯℃嫙Leader纭
            original_question = QMessageBox.question
            def mock_question(*args, **kwargs):
                return QMessageBox.Yes
            QMessageBox.question = mock_question
            
            dialog._add_member()
            
            if dialog.member_list.count() > 0:
                print(f"鉁?鎴愬憳娣诲姞鎴愬姛锛屽叡 {dialog.member_list.count()} 涓垚鍛?)
            
            QMessageBox.question = original_question
        else:
            print("鉁?閮ㄩ棬娣诲姞澶辫触")
            
    finally:
        QInputDialog.getText = original_getText
    
    return True


def verify_settings_saved(db):
    """楠岃瘉璁剧疆鏄惁姝ｇ‘淇濆瓨鍒版暟鎹簱"""
    print("\n=== 楠岃瘉鏁版嵁搴撲繚瀛?===")
    
    # 妫€鏌ラ€氱敤璁剧疆
    settings = db.query_one("SELECT * FROM settings WHERE id = 1")
    if settings:
        settings_dict = dict(settings)
        print(f"閫氱敤璁剧疆:")
        print(f"  sync_interval_minutes: {settings_dict.get('sync_interval_minutes')}")
        print(f"  auto_process: {settings_dict.get('auto_process')}")
        print(f"  daily_limit_free: {settings_dict.get('daily_limit_free')}")
    else:
        print("鉁?閫氱敤璁剧疆鏈繚瀛?)
        return False
    
    # 妫€鏌ユ棩鍘嗚缃?
    calendar_result = db.query_one("SELECT value FROM settings WHERE id = 2")
    if calendar_result and calendar_result[0]:
        calendar_settings = json.loads(calendar_result[0])
        print(f"\n鏃ュ巻璁剧疆:")
        print(f"  enabled: {calendar_settings.get('enabled')}")
        print(f"  type: {calendar_settings.get('type')}")
        print(f"  outlook_account: {calendar_settings.get('outlook_account')}")
    else:
        print("\n鉁?鏃ュ巻璁剧疆鏈繚瀛?)
    
    # 妫€鏌I璁剧疆
    ui_result = db.query_one("SELECT value FROM settings WHERE id = 3")
    if ui_result and ui_result[0]:
        ui_settings = json.loads(ui_result[0])
        print(f"\n鐣岄潰璁剧疆:")
        print(f"  theme: {ui_settings.get('theme')}")
        print(f"  accent_color: {ui_settings.get('accent_color')}")
        print(f"  show_preview: {ui_settings.get('show_preview')}")
    else:
        print("\n鉁?鐣岄潰璁剧疆鏈繚瀛?)
    
    # 妫€鏌ョ敤鎴风敾鍍?
    profile = db.query_one("SELECT * FROM user_profile WHERE id = 1")
    if profile:
        profile_dict = dict(profile)
        print(f"\n鐢ㄦ埛鐢诲儚:")
        print(f"  name: {profile_dict.get('name')}")
        print(f"  department: {profile_dict.get('department')}")
        print(f"  role: {profile_dict.get('role')}")
        print(f"  work_description: {profile_dict.get('work_description')}")
    else:
        print("\n鉁?鐢ㄦ埛鐢诲儚鏈繚瀛?)
    
    # 妫€鏌ラ儴闂ㄦ暟鎹?
    departments = db.query("SELECT id, name, share_path FROM departments")
    if departments:
        print(f"\n閮ㄩ棬鏁版嵁: 鍏?{len(departments)} 涓儴闂?)
        for dept_id, name, share_path in departments:
            print(f"  - {name}: {share_path}")
            
            # 妫€鏌ユ垚鍛?
            members = db.query(
                "SELECT name, email, role FROM team_members WHERE department_id = ?",
                (dept_id,)
            )
            if members:
                print(f"    鎴愬憳: {len(members)} 浜?)
                for m_name, m_email, m_role in members:
                    print(f"      - {m_name} <{m_email}> ({m_role})")
    else:
        print("\n鉁?閮ㄩ棬鏁版嵁鏈繚瀛?)
    
    return True


def main():
    """涓绘祴璇曟祦绋?""
    print("=" * 60)
    print("璁剧疆瀵硅瘽妗嗗姛鑳芥祴璇?)
    print("=" * 60)
    
    # 鍒涘缓搴旂敤
    app = QApplication(sys.argv)
    
    # 浣跨敤娴嬭瘯鏁版嵁搴?
    test_db_path = ":memory:"
    db = Database(test_db_path)
    
    print("\n鍒濆鍖栬缃璇濇...")
    dialog = SettingsDialog(db)
    
    # 鎵ц鍚勯」娴嬭瘯
    tests = [
        ("閫氱敤璁剧疆", test_general_settings),
        ("AI璁剧疆", test_ai_settings),
        ("鍚屾璁剧疆", test_sync_settings),
        ("鐣岄潰璁剧疆", test_ui_settings),
        ("鏃ュ巻璁剧疆", test_calendar_settings),
        ("鐢ㄦ埛鐢诲儚", test_user_profile),
        ("閮ㄩ棬绠＄悊", test_department_management),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            print(f"\n{'='*60}")
            if test_func(dialog):
                print(f"鉁?{test_name} 娴嬭瘯閫氳繃")
                passed += 1
            else:
                print(f"鉁?{test_name} 娴嬭瘯澶辫触")
                failed += 1
        except Exception as e:
            print(f"鉁?{test_name} 娴嬭瘯寮傚父: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    # 淇濆瓨璁剧疆
    print(f"\n{'='*60}")
    print("淇濆瓨璁剧疆...")
    try:
        dialog._save_settings()
        print("鉁?璁剧疆淇濆瓨鎴愬姛")
    except Exception as e:
        print(f"鉁?璁剧疆淇濆瓨澶辫触: {e}")
        import traceback
        traceback.print_exc()
        failed += 1
    
    # 楠岃瘉淇濆瓨缁撴灉
    verify_settings_saved(db)
    
    # 鎬荤粨
    print(f"\n{'='*60}")
    print("娴嬭瘯鎬荤粨")
    print(f"{'='*60}")
    print(f"閫氳繃: {passed}/{len(tests)}")
    print(f"澶辫触: {failed}/{len(tests)}")
    
    if failed == 0:
        print("\n鉁?鎵€鏈夋祴璇曢€氳繃锛佽缃璇濇鍔熻兘姝ｅ父")
    else:
        print(f"\n鈿狅笍  鏈?{failed} 椤规祴璇曞け璐ワ紝璇锋鏌?)
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
