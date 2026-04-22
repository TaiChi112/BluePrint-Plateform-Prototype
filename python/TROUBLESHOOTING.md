# 🔧 Troubleshooting Guide - Google Calendar Agent

## 🚨 Error 403: access_denied

### ปัญหาที่พบ
```
Access blocked: My Calendar Agent has not completed the Google verification process
Error 403: access_denied
```

### สาเหตุ
OAuth Consent Screen อยู่ใน **Testing mode** และบัญชี Google ที่คุณใช้ยังไม่ได้เพิ่มเป็น Test User

### วิธีแก้ (เลือกวิธีใดวิธีหนึ่ง)

---

## ✅ วิธีที่ 1: เพิ่ม Test Users (แนะนำสำหรับ Development)

### ขั้นตอน:

1. **ไปที่ Google Cloud Console**
   - URL: https://console.cloud.google.com/

2. **เลือก Project ของคุณ**
   - คลิก Dropdown ด้านบน → เลือก `thinking-avenue-489219-u9`

3. **ไปที่ OAuth consent screen**
   - Navigation Menu (☰) → **APIs & Services** → **OAuth consent screen**

4. **เพิ่ม Test Users**
   - Scroll ลงไปที่ส่วน **Test users**
   - คลิกปุ่ม **+ ADD USERS**
   - ใส่อีเมล Google ที่คุณจะใช้ทดสอบ (เช่น `anothai.0978452316@gmail.com`)
   - กด **SAVE**

5. **รันโปรแกรมใหม่**
   ```bash
   # ลบ token.json เก่า (ถ้ามี)
   rm token.json
   
   # รันใหม่
   python test_google_calendar.py
   ```

6. **Authorize ในเบราว์เซอร์**
   - จะเห็นหน้า warning: "Google hasn't verified this app"
   - คลิก **Advanced** → **Go to My Calendar Agent (unsafe)**
   - อนุญาตสิทธิ์ที่ขอ
   - ✅ เสร็จสิ้น!

---

## 🌐 วิธีที่ 2: เผยแพร่เป็น Production (สำหรับ Public App)

⚠️ **ข้อควรระวัง**: Google จะตรวจสอบแอปของคุณ (อาจใช้เวลา 1-2 สัปดาห์)

### ขั้นตอน:

1. **ไปที่ OAuth consent screen**
   - APIs & Services → OAuth consent screen

2. **คลิก "PUBLISH APP"**
   - อ่านและยอมรับเงื่อนไข

3. **รอ Google Verification**
   - Google จะส่งอีเมลแจ้งสถานะ
   - อาจต้องกรอกข้อมูลเพิ่มเติม (Privacy Policy, Terms of Service)

---

## 🔍 วิธีตรวจสอบสถานะปัจจุบัน

### 1. ตรวจสอบ OAuth Consent Screen Status

```
Google Cloud Console → APIs & Services → OAuth consent screen

สถานะที่เป็นไปได้:
- 🧪 Testing: ต้องเพิ่ม test users
- ✅ In production: ใช้งานได้ทุกคน (หลังผ่าน verification)
- 🔒 Needs verification: กำลังรอ Google ตรวจสอบ
```

### 2. ตรวจสอบ Test Users
```
OAuth consent screen → Test users section

ถ้าว่างเปล่า = ยังไม่มี test users → ต้องเพิ่ม!
```

---

## 🐛 ปัญหาอื่นๆ ที่อาจพบ

### Error: invalid_client
**สาเหตุ**: credentials.json ไม่ถูกต้องหรือหมดอายุ

**วิธีแก้**:
1. ดาวน์โหลด credentials.json ใหม่จาก Google Cloud Console
2. แทนที่ไฟล์เก่า
3. ลบ token.json
4. รันใหม่

---

### Error: redirect_uri_mismatch
**สาเหตุ**: Application type ไม่ใช่ "Desktop app"

**วิธีแก้**:
1. ไปที่ Credentials → OAuth 2.0 Client IDs
2. ลบ credential เก่า
3. สร้างใหม่แบบ "Desktop app"
4. ดาวน์โหลด JSON ใหม่

---

### Error: access_denied (หลังเพิ่ม test user แล้ว)
**สาเหตุ**: ใช้บัญชี Google ที่ต่างจากที่ระบุใน test users

**วิธีแก้**:
1. ตรวจสอบว่าอีเมลที่ login ตรงกับที่เพิ่มใน test users
2. ลอง logout Google account อื่นก่อน
3. เปิด Incognito/Private window

---

### token.json พังหรือหมดอายุ
**อาการ**: โปรแกรมรันไม่ได้ แม้ authorize แล้ว

**วิธีแก้**:
```bash
# ลบ token และสร้างใหม่
rm token.json
python test_google_calendar.py
```

---

## 📚 Quick Reference Commands

```bash
# ตรวจสอบว่า credentials.json ถูกต้อง
cat credentials.json | python -m json.tool

# ลบ token เก่าและรันใหม่
rm -f token.json && python test_google_calendar.py

# ดูข้อมูลใน token (ถ้ามี)
cat token.json | python -m json.tool

# ตรวจสอบว่าติดตั้ง libraries ครบ
pip list | grep google
```

---

## 🆘 ยังไม่แก้ไขได้?

### Checklist:
- [ ] Enable Google Calendar API แล้ว
- [ ] สร้าง OAuth 2.0 Credentials (Desktop app)
- [ ] ดาวน์โหลด credentials.json
- [ ] เพิ่มอีเมลใน Test users
- [ ] ใช้อีเมลเดียวกันตอน authorize
- [ ] ลบ token.json แล้วรันใหม่

### ถ้ายังไม่ได้:
1. ตรวจสอบ Project ID ใน .env ตรงกับใน Google Cloud Console
2. ลอง revoke permissions: https://myaccount.google.com/permissions
3. สร้าง Project ใหม่และเริ่มต้นใหม่

---

## 📷 Screenshots Guide

### ตำแหน่ง Test Users:
```
Google Cloud Console
  └── APIs & Services
      └── OAuth consent screen
          └── Test users (ส่วนล่าง)
              └── [+ ADD USERS] ← กดตรงนี้
```

### Warning ที่ถูกต้อง:
เมื่อเป็น test mode จะเห็นหน้าจอ:
```
⚠️ Google hasn't verified this app

[Advanced] ← กดตรงนี้
  └── Go to My Calendar Agent (unsafe) ← กดตรงนี้
```

---

## ✍️ บันทึกเพิ่มเติม

- Test users มีจำนวน จำกัด 100 คน
- Testing mode ไม่มีข้อจำกัดเวลา (ใช้ได้ตลอด)
- ถ้าต้องการให้คนอื่นใช้ (>100 คน) ต้องเผยแพร่เป็น Production
- Production mode ต้องผ่าน Google verification

---

**เมื่อแก้ไขปัญหาเสร็จแล้ว คุณจะเห็น:**
```
✅ เชื่อมต่อ Google Calendar สำเร็จ
📅 พบ X events ใน 30 วันข้างหน้า
```

สำเร็จ! 🎉
