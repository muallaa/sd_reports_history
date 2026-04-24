# Odoo 17 Work Handoff

هذا الملف هو ملخص سريع لطريقة العمل المعتمدة في هذا المشروع حتى يمكن نقلها إلى محادثة أخرى بدون فقدان السياق.

## 1) بيئة العمل

- **Odoo root:** `C:\Users\Mualla\odoo`
- **Custom addons path:** `D:\derasat\test`
- **Current custom addon:** `mail_discuss_forward_preview`
- **Expected Odoo version:** `17.0`
- **Current workspace in this chat:** `D:\derasat\test\Descuss`

## 2) أسلوب العمل المطلوب

عند تنفيذ أي تعديل على Odoo في هذا المشروع، يجب الالتزام بهذه القواعد:

- التعديل يكون عبر **custom addon فقط**
- **ممنوع تعديل Odoo core مباشرة**
- الالتزام بـ **Odoo 17 best practices**
- في الواجهة:
  - استخدام **Owl patching**
  - استخدام **QWeb inheritance**
  - استخدام **registries** عند توفر extension point
- في الباكند:
  - إعادة استخدام `message_post` و flows الأصلية بدل اختراع flow جديد
  - التحقق من الصلاحيات قبل أي عملية حساسة
- التغييرات يجب أن تكون:
  - صغيرة
  - آمنة
  - سهلة الصيانة
  - لا تكسر السلوك الأصلي

## 3) طريقة التنفيذ المعتمدة

قبل أي تعديل:

1. **افحص ملفات Odoo الأصلية أولًا**
2. حدّد:
   - component/template الفعلي المستخدم في Odoo 17
   - registry أو patch point الصحيح
   - model/backend method المناسبة
3. نفّذ التمديد من خلال addon مخصص فقط
4. تجنب استبدال ملفات كبيرة أو إعادة كتابة Discuss

## 4) ما تم تنفيذه في هذا المشروع

تم تنفيذ addon باسم:

- `mail_discuss_forward_preview`

ويضيف إلى Discuss:

1. **عرض preview لآخر رسالة** تحت اسم المحادثة في الـ sidebar
2. **إظهار اسم المرسل** داخل preview
   - إذا كان المرسل هو المستخدم الحالي: يظهر `You`
3. **Tooltip عند hover** يحتوي النص الكامل للمعاينة
4. **زر Forward** على الرسائل داخل Discuss
5. **Dialog للتحويل**
6. **اختيار target conversation**
7. **دعم تحويل الرسائل مع attachments**
8. **إنشاء chat جديدة تلقائيًا** عند التحويل إلى شخص لا توجد معه محادثة
9. **إظهار مؤشر forwarded كأيقونة فقط**
10. **عدم إظهار `Forwarded message` كنص داخل body أو sidebar preview**
11. **إذا كانت آخر رسالة attachment فقط** يظهر في preview:
   - `مرفق`

## 5) قواعد السلوك الحالية في الموديول

### Sidebar preview

- يعرض آخر رسالة meaningful
- يتجاهل `notification` قدر الإمكان
- إذا كانت الرسالة HTML يتم تحويلها إلى نص نظيف
- إذا كانت الرسالة من المستخدم الحالي:
  - preview author = `You`
- إذا لم يوجد نص ويوجد attachment:
  - preview text = `مرفق`

### Forward

- الرسالة الأصلية لا تتعدل ولا تُحذف
- الـ attachments لا تُنقل من الرسالة الأصلية
- يتم **نسخ attachments** إلى الرسالة الجديدة
- التحويل ينشئ **message جديدة** في target chat/channel
- إذا target هو شخص وليس channel موجود:
  - يتم إنشاء أو جلب direct chat تلقائيًا

## 6) ملاحظة مهمة جدًا عن `message_post`

تمت ملاحظة خطأ سابق:

`Those values are not supported when posting or notifying: is_discuss_forwarded`

والسبب:

- لا يجوز تمرير `is_discuss_forwarded` مباشرة داخل `message_post(...)`

والحل المعتمد:

1. إنشاء الرسالة عبر `message_post(...)`
2. ثم:
   - `forwarded_message.write({"is_discuss_forwarded": True})`

## 7) الملفات الأساسية في الموديول

### Backend

- `mail_discuss_forward_preview/__manifest__.py`
- `mail_discuss_forward_preview/models/discuss_channel.py`
- `mail_discuss_forward_preview/models/mail_message.py`

### Frontend JS

- `mail_discuss_forward_preview/static/src/js/discuss_sidebar_categories_patch.js`
- `mail_discuss_forward_preview/static/src/js/message_forward_action.js`
- `mail_discuss_forward_preview/static/src/js/forward_message_dialog.js`
- `mail_discuss_forward_preview/static/src/js/channel_selector_forward_patch.js`
- `mail_discuss_forward_preview/static/src/js/message_forward_indicator.js`

### Frontend XML

- `mail_discuss_forward_preview/static/src/xml/discuss_sidebar_categories_patch.xml`
- `mail_discuss_forward_preview/static/src/xml/forward_message_dialog.xml`
- `mail_discuss_forward_preview/static/src/xml/channel_selector_forward_patch.xml`
- `mail_discuss_forward_preview/static/src/xml/message_forward_indicator.xml`

### Styles

- `mail_discuss_forward_preview/static/src/scss/discuss_forward_preview.scss`

## 8) ما الذي يجب الحفاظ عليه في أي محادثة جديدة

في أي استكمال لاحق، يجب الحفاظ على هذه المبادئ:

- لا تعديل على Odoo core
- لا كسر reply/edit/delete
- لا إزالة سلوك Discuss الأصلي
- reuse للكومبوننتات الأصلية عندما يكون ذلك ممكنًا
- عند وجود native component مناسب:
  - الأفضل **extension/inheritance**
  - وليس copy-paste
- أي تغيير جديد يجب أن يكون minimal و production-safe

## 9) طريقة التفكير المطلوبة عند أي feature جديدة في Discuss

أي feature جديدة يجب تنفيذها بهذا التسلسل:

1. تحديد file/component الحقيقي في Odoo 17
2. تحديد هل المطلوب:
   - patch
   - registry extension
   - inherited template
   - backend method
3. إعادة استخدام data الموجودة في store/model إن أمكن
4. إضافة backend support فقط إذا كانت الواجهة لا تملك البيانات أصلًا
5. اختبار:
   - direct chat
   - group/channel
   - text
   - html
   - attachments
   - unauthorized cases

## 10) أوامر مفيدة

### Upgrade module

```powershell
C:\Users\Mualla\odoo\venv\Scripts\python.exe C:\Users\Mualla\odoo\odoo-bin -c C:\Users\Mualla\odoo\odoo.conf -d odoo17 -u mail_discuss_forward_preview --stop-after-init
```

### Compile Python files quickly

```powershell
python -m compileall D:\derasat\test\mail_discuss_forward_preview
```

## 11) ملاحظات Git

تم إنشاء repo محلي للموديول، وظهرت سابقًا مشاكل push متعلقة بـ:

- credentials
- GitHub token / permissions
- أو branch protection

إذا واجهت المحادثة الجديدة مشكلة `403` عند `git push`:

- افحص الحساب المستخدم فعليًا
- امسح credentials القديمة
- استخدم PAT بصلاحية كتابة
- أو استخدم SSH

## 12) Prompt مختصر يمكن نقله إلى محادثة جديدة

يمكن استخدام النص التالي كنقطة انطلاق:

> نحن نعمل على Odoo 17.  
> Root: `C:\Users\Mualla\odoo`  
> Custom addon: `D:\derasat\test\mail_discuss_forward_preview`  
> المطلوب دائمًا: custom addon only, no core edits, minimal safe changes, Odoo 17 Owl/QWeb patching, registry extension, backend methods, manifest assets.  
> هذا الموديول يمدد Discuss ليدعم sidebar message preview و message forwarding مع attachments.  
> حافظ على السلوك الحالي ولا تكسر native Discuss behavior.  
> قبل أي تعديل افحص ملفات Odoo الأصلية وحدد extension point الصحيح.  

