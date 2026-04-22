# 🚀 Quick Reference - Calendar Agent

## ⚡ คำสั่งที่ใช้บ่อย

### เริ่มใช้งานด่วน
```bash
# Mock mode (ทดสอบ)
python main.py

# Interactive mode
python example_usage.py --interactive

# Google Calendar API
python example_usage.py --mode api --interactive
```

### แก้ปัญหา OAuth
```bash
# 1. ลบ token เก่า
rm token.json

# 2. ทดสอบ connection ใหม่
python test_google_calendar.py

# 3. อ่านวิธีแก้ถ้ายังไม่ได้
cat TROUBLESHOOTING.md | less
```

### รัน Tests
```bash
# ทั้งหมด
python -m pytest test_main.py -v

# เฉพาะ auto-suggest
python -m pytest test_main.py::TestAutoSuggest -v

# ดู coverage
python -m pytest test_main.py --cov=main
```

---

## 🎮 Interactive Mode - ตัวเลือก

เมื่อพบ conflict จะมีตัวเลือก:

| ตัวเลือก | คำอธิบาย | ผลลัพธ์ |
|----------|----------|---------|
| **1** | ข้ามสัปดาห์ที่ชน | บันทึกแค่สัปดาห์ที่ไม่ชน |
| **2** | ลงทับ (Overwrite) | บันทึกทุกอย่าง (จะชนกับ event เดิม) |
| **3** | ใช้ Auto-Suggest ⭐ | ใช้เวลาทางเลือกที่ Agent แนะนำ + Scoring |
| **4** | ยกเลิก | ไม่บันทึกอะไรเลย |

---

## 📊 Scoring System

คะแนนเวลา (0-100):

| เงื่อนไข | คะแนน |
|---------|-------|
| ช่วงเช้า (8-12) | +20 |
| ช่วงบ่าย (13-17) | +10 |
| ช่วงกลางวัน (11:30-13) | -15 |
| ช่วงเย็น (17-20) | -10 |
| ใกล้เวลาที่ชอบ | +15 |
| ตอนต้นวัน (8-9 AM) | +10 |

**ยิ่งคะแนนสูง = เหมาะสมกว่า**

---

## 🔧 Troubleshooting ด่วน

### Error 403: access_denied
```bash
# แก้: เพิ่ม test user ใน Google Cloud Console
# https://console.cloud.google.com/
# → APIs & Services → OAuth consent screen → Test users
```

### ไฟล์ไม่เจอ
```bash
# ตรวจสอบว่าอยู่ใน folder python/
pwd  # ควรเป็น .../python
ls credentials.json  # ต้องมีไฟล์นี้
```

### Import Error
```bash
# ติดตั้ง dependencies
pip install -r requirements.txt
```

---

## 📝 ไฟล์สำคัญ

| ไฟล์ | จุดประสงค์ |
|------|-----------|
| `main.py` | Core Agent Logic |
| `example_usage.py` | CLI + Interactive Mode |
| `test_google_calendar.py` | ทดสอบ OAuth |
| `credentials.json` | OAuth Credentials (ห้ามลบ!) |
| `token.json` | OAuth Token (สร้างอัตโนมัติ) |
| `TROUBLESHOOTING.md` | แก้ปัญหา OAuth |
| `MCP_IMPLEMENTATION_GUIDE.md` | Setup MCP Server |

---

## 🎯 Use Cases

### 1. ลงตารางเรียน 1 เทอม
```python
user_intent = {
    "summary": "CS301: Data Mining",
    "start": datetime(2026, 6, 1, 9, 30),
    "duration_weeks": 18
}
response = agent.process_recurring_request(user_intent, interactive=True)
```

### 2. ทดสอบ Google Calendar
```bash
python test_google_calendar.py
# ครั้งแรกจะเปิด browser ให้ authorize
```

### 3. ดู Events ที่มีอยู่
```python
from calendar_integrations import get_calendar_tool
calendar = get_calendar_tool("api")
events = calendar.get_events(start_date, end_date)
```

---

## 💡 Tips

- **ครั้งแรก**: ใช้ `--mode mock` ทดสอบก่อน
- **Authorization**: ครั้งแรกจะเปิด browser → คลิก "Advanced" → "Go to ... (unsafe)"
- **Test Users**: เพิ่มอีเมลที่จะใช้ใน OAuth Consent Screen
- **Token หมดอายุ**: ลบ `token.json` แล้วรันใหม่
- **Interactive Mode**: กด Ctrl+C เพื่อยกเลิก

---

## 📚 เอกสารเพิ่มเติม

- [README.md](README.md) - คู่มือหลัก + Setup Google Cloud
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - แก้ปัญหา OAuth 403
- [MCP_IMPLEMENTATION_GUIDE.md](MCP_IMPLEMENTATION_GUIDE.md) - Setup MCP Server
- [FINAL_SUMMARY.md](FINAL_SUMMARY.md) - สรุปฟีเจอร์ทั้งหมด

---

## 🆘 ช่องทางติดต่อ

หากติดปัญหา:
1. อ่าน TROUBLESHOOTING.md
2. ดู error message ใน terminal
3. เช็ค unit tests: `python -m pytest test_main.py -v`

---

**Version**: 2.0 (with Interactive CLI + Smart Rescheduling)  
**Last Updated**: March 5, 2026

---

🚀 **Ready to Schedule!** 🚀
