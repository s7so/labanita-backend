# 🔐 Labanita Authentication System

## 📋 **نظرة عامة**

نظام المصادقة الكامل لـ Labanita API يوفر:
- **مصادقة بالهاتف** مع OTP
- **JWT Tokens** (Access + Refresh)
- **إدارة الجلسات** المتعددة
- **إدارة الملف الشخصي** للمستخدمين
- **إعادة تعيين كلمات المرور**
- **مصادقة اجتماعية** (Facebook/Google - قيد التطوير)

## 🚀 **الميزات الرئيسية**

### **✅ مصادقة الهاتف**
- إرسال OTP عبر SMS
- التحقق من OTP
- تسجيل دخول بدون كلمة مرور
- إعادة إرسال OTP

### **✅ JWT Authentication**
- Access Token (30 دقيقة)
- Refresh Token (7 أيام)
- Token validation
- Automatic token refresh

### **✅ إدارة الجلسات**
- جلسات متعددة للأجهزة
- تتبع معلومات الجهاز
- تسجيل الخروج من جميع الجلسات
- تنظيف الجلسات المنتهية

### **✅ إدارة الملف الشخصي**
- عرض الملف الشخصي
- تحديث المعلومات
- تغيير كلمة المرور
- حذف الحساب (soft delete)

## 🛠️ **متطلبات التثبيت**

### **1. تثبيت المكتبات**
```bash
pip install -r requirements.txt
```

### **2. تحديث قاعدة البيانات**
```bash
# تشغيل ملف تحديث قاعدة البيانات
psql -U postgres -d labanita -f auth_database_update.sql
```

### **3. تحديث ملف .env**
```env
# JWT Configuration
JWT_SECRET_KEY="your-super-secret-jwt-key-here"
JWT_ALGORITHM="HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# OTP Configuration
OTP_EXPIRE_MINUTES=5
OTP_LENGTH=6

# External Services (Optional)
TWILIO_ACCOUNT_SID=""
TWILIO_AUTH_TOKEN=""
TWILIO_PHONE_NUMBER=""
```

## 📱 **نقاط النهاية (API Endpoints)**

### **🔐 مصادقة الهاتف**

#### **إرسال OTP**
```http
POST /api/auth/send-otp
Content-Type: application/json

{
    "phone_number": "+201234567890",
    "otp_type": "REGISTRATION"
}
```

**أنواع OTP:**
- `REGISTRATION` - للتسجيل الجديد
- `LOGIN` - لتسجيل الدخول
- `RESET_PASSWORD` - لإعادة تعيين كلمة المرور

#### **إعادة إرسال OTP**
```http
POST /api/auth/resend-otp
Content-Type: application/json

{
    "phone_number": "+201234567890",
    "otp_type": "REGISTRATION"
}
```

#### **التحقق من OTP**
```http
POST /api/auth/verify-otp
Content-Type: application/json

{
    "phone_number": "+201234567890",
    "otp_code": "123456",
    "otp_type": "REGISTRATION"
}
```

### **👤 تسجيل المستخدمين وتسجيل الدخول**

#### **تسجيل مستخدم جديد**
```http
POST /api/auth/register
Content-Type: application/json

{
    "phone_number": "+201234567890",
    "full_name": "أحمد محمد",
    "email": "ahmed@example.com",
    "password": "MyPassword123"
}
```

#### **تسجيل الدخول**
```http
POST /api/auth/login
Content-Type: application/json

{
    "phone_number": "+201234567890",
    "password": "MyPassword123"
}
```

**ملاحظة:** كلمة المرور اختيارية - يمكن تسجيل الدخول بالهاتف فقط

### **🔄 إدارة Tokens**

#### **تحديث Access Token**
```http
POST /api/auth/refresh
Content-Type: application/json

{
    "refresh_token": "your-refresh-token-here"
}
```

#### **تسجيل الخروج**
```http
POST /api/auth/logout
Content-Type: application/json

{
    "refresh_token": "your-refresh-token-here"
}
```

#### **تسجيل الخروج من جميع الجلسات**
```http
POST /api/auth/logout-all
Authorization: Bearer your-access-token-here
```

### **👤 إدارة الملف الشخصي**

#### **عرض الملف الشخصي**
```http
GET /api/auth/profile
Authorization: Bearer your-access-token-here
```

#### **تحديث الملف الشخصي**
```http
PUT /api/auth/profile
Authorization: Bearer your-access-token-here
Content-Type: application/json

{
    "full_name": "أحمد محمد علي",
    "email": "ahmed.ali@example.com"
}
```

#### **تغيير كلمة المرور**
```http
POST /api/auth/password/change
Authorization: Bearer your-access-token-here
Content-Type: application/json

{
    "current_password": "OldPassword123",
    "new_password": "NewPassword123"
}
```

### **🔑 إعادة تعيين كلمة المرور**

#### **إعادة تعيين كلمة المرور**
```http
POST /api/auth/password/reset
Content-Type: application/json

{
    "phone_number": "+201234567890",
    "new_password": "NewPassword123"
}
```

### **📱 إدارة الجلسات**

#### **عرض الجلسات النشطة**
```http
GET /api/auth/sessions
Authorization: Bearer your-access-token-here
```

## 🔒 **الأمان والحماية**

### **✅ JWT Security**
- Access tokens منتهية الصلاحية
- Refresh tokens آمنة
- Token validation صارم

### **✅ OTP Security**
- OTP منتهي الصلاحية (5 دقائق)
- حد أقصى 3 محاولات
- منع إعادة الإرسال المتكرر

### **✅ Session Security**
- تتبع معلومات الجهاز
- تتبع عنوان IP
- تسجيل الخروج التلقائي

### **✅ Password Security**
- تشفير bcrypt
- متطلبات قوة كلمة المرور
- منع إعادة استخدام كلمات المرور

## 🧪 **اختبار النظام**

### **1. اختبار إرسال OTP**
```bash
curl -X POST "http://localhost:8000/api/auth/send-otp" \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+201234567890", "otp_type": "REGISTRATION"}'
```

### **2. اختبار تسجيل الدخول**
```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+201234567890", "password": "MyPassword123"}'
```

### **3. اختبار الملف الشخصي**
```bash
curl -X GET "http://localhost:8000/api/auth/profile" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## 📊 **استجابة API**

### **✅ استجابة ناجحة**
```json
{
    "success": true,
    "message": "Operation completed successfully",
    "data": {
        "user_id": "uuid-here",
        "phone_number": "+201234567890",
        "full_name": "أحمد محمد",
        "is_verified": true
    },
    "timestamp": "2024-01-15T12:00:00Z"
}
```

### **❌ استجابة خطأ**
```json
{
    "success": false,
    "message": "Authentication failed",
    "data": null,
    "errors": [],
    "timestamp": "2024-01-15T12:00:00Z",
    "error_code": "AUTH_FAILED"
}
```

## 🚨 **رموز الخطأ**

| الكود | الوصف |
|-------|--------|
| `AUTH_FAILED` | فشل في المصادقة |
| `INVALID_CREDENTIALS` | بيانات اعتماد غير صحيحة |
| `TOKEN_EXPIRED` | انتهت صلاحية الـ token |
| `USER_EXISTS` | المستخدم موجود بالفعل |
| `OTP_FAILED` | فشل في التحقق من OTP |
| `INVALID_PHONE` | رقم هاتف غير صحيح |

## 🔧 **التخصيص والتطوير**

### **✅ إضافة مصادقة اجتماعية**
```python
# في auth/services.py
async def facebook_login(self, access_token: str) -> User:
    # تنفيذ مصادقة Facebook
    pass

async def google_login(self, access_token: str) -> User:
    # تنفيذ مصادقة Google
    pass
```

### **✅ إضافة Role-Based Access Control**
```python
# في auth/dependencies.py
def require_admin_role(current_user: User = Depends(get_current_active_user)):
    if not current_user.is_admin:
        raise AuthorizationException("Admin access required")
    return current_user
```

### **✅ إضافة Rate Limiting**
```python
# في auth/dependencies.py
def check_rate_limit(request: Request, current_user: User = Depends(get_optional_user)):
    # تنفيذ Rate Limiting
    pass
```

## 📚 **أمثلة الاستخدام**

### **📱 تطبيق Flutter**
```dart
// إرسال OTP
final response = await http.post(
  Uri.parse('http://localhost:8000/api/auth/send-otp'),
  headers: {'Content-Type': 'application/json'},
  body: jsonEncode({
    'phone_number': '+201234567890',
    'otp_type': 'REGISTRATION'
  }),
);

// التحقق من OTP
final otpResponse = await http.post(
  Uri.parse('http://localhost:8000/api/auth/verify-otp'),
  headers: {'Content-Type': 'application/json'},
  body: jsonEncode({
    'phone_number': '+201234567890',
    'otp_code': '123456',
    'otp_type': 'REGISTRATION'
  }),
);
```

### **🌐 تطبيق React**
```javascript
// تسجيل الدخول
const login = async (phoneNumber, password) => {
  const response = await fetch('/api/auth/login', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      phone_number: phoneNumber,
      password: password
    }),
  });
  
  const data = await response.json();
  if (data.success) {
    // حفظ tokens
    localStorage.setItem('access_token', data.data.tokens.access_token);
    localStorage.setItem('refresh_token', data.data.tokens.refresh_token);
  }
};

// جلب الملف الشخصي
const getProfile = async () => {
  const token = localStorage.getItem('access_token');
  const response = await fetch('/api/auth/profile', {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  const data = await response.json();
  return data.data;
};
```

## 🚀 **الخطوات التالية**

### **✅ الميزات المكتملة**
- [x] نظام المصادقة الأساسي
- [x] JWT tokens
- [x] OTP verification
- [x] إدارة الجلسات
- [x] إدارة الملف الشخصي

### **🔄 الميزات قيد التطوير**
- [ ] مصادقة Facebook
- [ ] مصادقة Google
- [ ] Role-based access control
- [ ] Rate limiting
- [ ] Two-factor authentication

### **📋 الميزات المستقبلية**
- [ ] Biometric authentication
- [ ] Hardware security keys
- [ ] Advanced session analytics
- [ ] Multi-tenant authentication

## 📞 **الدعم والمساعدة**

إذا واجهت أي مشاكل أو لديك أسئلة:

1. **تحقق من ملفات Log**
2. **راجع قاعدة البيانات**
3. **اختبر نقاط النهاية**
4. **راجع التوثيق**

## 🎯 **الخلاصة**

نظام المصادقة الكامل لـ Labanita يوفر:
- **أمان عالي** مع JWT و OTP
- **سهولة الاستخدام** للمطورين
- **مرونة في التخصيص**
- **قابلية التوسع** للمستقبل

**🚀 ابدأ باستخدام النظام الآن!**