"""
تطبيق المذكرات اليومية (Diary App)
تطبيق Flask بسيط لإدارة المذكرات اليومية
"""

from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
from sqlalchemy import desc

# تهيئة تطبيق Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///diary.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# تهيئة قاعدة البيانات
db = SQLAlchemy(app)


# إضافة فلتر مخصص لـ Jinja2 لتحويل الأسطر الجديدة إلى <br>
@app.template_filter('nl2br')
def nl2br_filter(text):
    """
    فلتر لتحويل الأسطر الجديدة (\n) إلى <br> في القوالب
    """
    return text.replace('\n', '<br>') if text else ''


# نموذج جدول المذكرات
class DiaryEntry(db.Model):
    """
    نموذج جدول المذكرات اليومية
    """
    __tablename__ = 'diary_entries'
    
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)
    
    def __repr__(self):
        return f'<DiaryEntry {self.id}>'


# الصفحة الرئيسية - عرض جميع المذكرات
@app.route('/')
def index():
    """
    الصفحة الرئيسية: تعرض جميع المذكرات مرتبة حسب التاريخ
    مع إمكانية الفلترة حسب اليوم أو الشهر
    """
    # الحصول على معاملات الفلترة من URL
    filter_type = request.args.get('filter', 'all')  # all, today, month
    filter_value = request.args.get('value', '')
    
    # استعلام أساسي
    query = DiaryEntry.query
    
    # تطبيق الفلترة
    if filter_type == 'today':
        # فلترة حسب اليوم الحالي
        today = date.today()
        query = query.filter(
            db.func.date(DiaryEntry.created_at) == today
        )
    elif filter_type == 'month' and filter_value:
        # فلترة حسب الشهر
        try:
            year, month = map(int, filter_value.split('-'))
            query = query.filter(
                db.func.extract('year', DiaryEntry.created_at) == year,
                db.func.extract('month', DiaryEntry.created_at) == month
            )
        except ValueError:
            pass
    
    # ترتيب المذكرات حسب التاريخ (الأحدث أولاً)
    entries = query.order_by(desc(DiaryEntry.created_at)).all()
    
    # تمرير التاريخ الحالي للقالب
    current_date = date.today()
    
    return render_template('index.html', entries=entries, filter_type=filter_type, current_date=current_date)


# صفحة إضافة مذكرة جديدة
@app.route('/add', methods=['GET', 'POST'])
def add_entry():
    """
    صفحة إضافة مذكرة جديدة
    GET: عرض النموذج
    POST: حفظ المذكرة في قاعدة البيانات
    """
    if request.method == 'POST':
        content = request.form.get('content', '').strip()
        
        if content:
            # إنشاء مذكرة جديدة
            new_entry = DiaryEntry(
                content=content,
                created_at=datetime.now()
            )
            
            # حفظ في قاعدة البيانات
            db.session.add(new_entry)
            db.session.commit()
            
            flash('تم حفظ المذكرة بنجاح!', 'success')
            return redirect(url_for('index'))
        else:
            flash('يرجى إدخال محتوى المذكرة', 'error')
    
    return render_template('add_entry.html')


# صفحة عرض مذكرة واحدة بالتفصيل
@app.route('/entry/<int:entry_id>')
def view_entry(entry_id):
    """
    عرض مذكرة واحدة بالتفصيل
    """
    entry = DiaryEntry.query.get_or_404(entry_id)
    return render_template('view_entry.html', entry=entry)


# صفحة حذف مذكرة
@app.route('/delete/<int:entry_id>', methods=['POST'])
def delete_entry(entry_id):
    """
    حذف مذكرة من قاعدة البيانات
    """
    entry = DiaryEntry.query.get_or_404(entry_id)
    db.session.delete(entry)
    db.session.commit()
    flash('تم حذف المذكرة بنجاح!', 'success')
    return redirect(url_for('index'))


if __name__ == '__main__':
    # إنشاء الجداول قبل تشغيل التطبيق
    with app.app_context():
        db.create_all()
    
    # تشغيل التطبيق
    app.run(debug=True)

