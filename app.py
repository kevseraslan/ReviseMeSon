from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, render_template_string, session
from flask_migrate import Migrate

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func, and_, or_
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_mail import Mail, Message
from flask_wtf.csrf import CSRFProtect
import urllib
from datetime import datetime, timedelta
import threading
import time
import hashlib # hashlib importunu tekrar ekledim
import random # Bu satırı ekledim
import os
from werkzeug.utils import secure_filename
import secrets
import matplotlib.pyplot as plt # Grafik çizmek için
import pandas as pd # Veri işlemek için
import io # Grafik görselini kaydetmek için
import base64 # Grafik görselini base64 olarak encode etmek için

app = Flask(__name__)
# app.config['SECRET_KEY'] = secrets.token_hex(16) # Daha güvenli bir anahtar oluştur - Bu satırı devre dışı bırak
app.config['SECRET_KEY'] = 'bu-sabit-bir-test-anahtaridir' # TEST AMAÇLI SABİT ANAHTAR

# MSSQL bağlantı parametreleri
driver = "ODBC Driver 17 for SQL Server"
server = "MSI\\SQLK"
database = "ReviseMe"

connection_string = f"DRIVER={{{driver}}};SERVER={server};DATABASE={database};Trusted_Connection=yes;TrustServerCertificate=yes;MARS_Connection=yes;"
params = urllib.parse.quote_plus(connection_string)

# SQLAlchemy ayarları
app.config['SQLALCHEMY_DATABASE_URI'] = (
    'mssql+pyodbc://@MSI\\SQLK/ReviseMe?'
    'driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# CSRF koruması
csrf = CSRFProtect(app)
app.config['WTF_CSRF_CHECK_DEFAULT'] = False  # CSRF korumasını isteğe bağlı hale getir

# Mail ayarları
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'inforeviseme@gmail.com'  # Gmail adresin
app.config['MAIL_PASSWORD'] = 'calggattsmcvrlvt'     # Gmail uygulama şifren
app.config['MAIL_DEFAULT_SENDER'] = 'inforeviseme@gmail.com'

# SendGrid ayarları
app.config['SENDGRID_API_KEY'] = 'YOUR_SENDGRID_API_KEY'
app.config['SENDGRID_FROM_EMAIL'] = 'your-verified-sender@yourdomain.com'

# SQLAlchemy nesnesi
db = SQLAlchemy(app)

migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
mail = Mail(app)

# Database Models
class User(UserMixin, db.Model):
    __tablename__ = 'Users'
    UserId = db.Column(db.Integer, primary_key=True)
    UserName = db.Column(db.String(50), unique=True, nullable=False)
    PasswordHash = db.Column(db.String(128), nullable=False)
    Name = db.Column(db.String(50))
    Surname = db.Column(db.String(50))
    Class = db.Column(db.String(50))
    YearOfBirth = db.Column(db.Integer)
    Area = db.Column(db.String(50))
    Aim = db.Column(db.String(100))
    Email = db.Column(db.String(100))
    PhoneNumber = db.Column(db.String(20))
    GoogleAuthId = db.Column(db.String(100))
    SecurityQuestion = db.Column(db.String(200))

    def get_id(self):
        return str(self.UserId)
        
    def can_modify(self, question):
        return self.UserId == question.UserId

class Category(db.Model):
    __tablename__ = 'Categories'
    CategoryId = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String(50))

class Question(db.Model):
    __tablename__ = 'Questions'
    
    QuestionId = db.Column(db.Integer, primary_key=True)
    UserId = db.Column(db.Integer, db.ForeignKey('Users.UserId'), nullable=False)
    Content = db.Column(db.Text, nullable=False)
    CategoryId = db.Column(db.Integer, db.ForeignKey('Categories.CategoryId'), nullable=False)
    Topic = db.Column(db.String(100))
    DifficultyLevel = db.Column(db.String(20))
    PhotoPath = db.Column(db.String(255))
    IsRepeated = db.Column(db.Boolean, default=False)
    RepeatCount = db.Column(db.Integer, default=0)
    Repeat1Date = db.Column(db.DateTime)
    Repeat2Date = db.Column(db.DateTime)
    Repeat3Date = db.Column(db.DateTime)
    IsCompleted = db.Column(db.Boolean, default=False)
    IsViewed = db.Column(db.Boolean, default=False)
    Explanation = db.Column(db.Text)
    ImagePath = db.Column(db.String(255))
    IsHidden = db.Column(db.Boolean, default=False)
    
    user = db.relationship('User', backref=db.backref('questions', lazy=True))
    category = db.relationship('Category', backref=db.backref('questions', lazy=True))

class Note(db.Model):
    __tablename__ = 'Notes'
    NoteId = db.Column(db.Integer, primary_key=True)
    QuestionId = db.Column(db.Integer, db.ForeignKey('Questions.QuestionId'))
    Content = db.Column(db.Text)
    
    question = db.relationship('Question', backref='notes')

class Favorite(db.Model):
    __tablename__ = 'Favorites'
    FavoriteId = db.Column(db.Integer, primary_key=True)
    QuestionId = db.Column(db.Integer, db.ForeignKey('Questions.QuestionId'), nullable=False)
    UserId = db.Column(db.Integer, db.ForeignKey('Users.UserId'), nullable=False)
    
    # İlişkiler
    question = db.relationship('Question', backref='favorites')
    user = db.relationship('User', backref='favorites')

class Notification(db.Model):
    __tablename__ = 'Notifications'
    NotificationId = db.Column(db.Integer, primary_key=True)
    UserId = db.Column(db.Integer, db.ForeignKey('Users.UserId'))
    NotificationType = db.Column(db.String(50))
    Schedule = db.Column(db.DateTime)
    
    user = db.relationship('User', backref='notifications')

class PasswordResetToken(db.Model):
    __tablename__ = 'PasswordResetTokens'
    TokenId = db.Column(db.Integer, primary_key=True)
    UserId = db.Column(db.Integer, db.ForeignKey('Users.UserId'), nullable=False)
    Token = db.Column(db.String(100), unique=True, nullable=False)
    ExpiresAt = db.Column(db.DateTime, nullable=False)
    IsUsed = db.Column(db.Boolean, default=False)
    
    user = db.relationship('User', backref='password_reset_tokens')

class TedTalk(db.Model):
    __tablename__ = 'TedTalks'
    TalkId = db.Column(db.Integer, primary_key=True)
    Title = db.Column(db.String(200), nullable=False)
    Speaker = db.Column(db.String(100), nullable=False)
    VideoUrl = db.Column(db.String(500), nullable=False)
    Description = db.Column(db.Text)
    Duration = db.Column(db.String(50))
    Category = db.Column(db.String(100))
    IsWatched = db.Column(db.Boolean, default=False)
    UserId = db.Column(db.Integer, db.ForeignKey('Users.UserId'), nullable=False)
    user = db.relationship('User', backref='ted_talks')

class Book(db.Model):
    __tablename__ = 'Books'
    BookId = db.Column(db.Integer, primary_key=True)
    Title = db.Column(db.String(200))
    Author = db.Column(db.String(100))
    CurrentPage = db.Column(db.Integer)
    TotalPages = db.Column(db.Integer)
    StartDate = db.Column(db.DateTime)
    UserId = db.Column(db.Integer, db.ForeignKey('Users.UserId'))
    IsCompleted = db.Column(db.Boolean, default=False)  # <-- BUNU EKLE!
    user = db.relationship('User', backref='books')

class BookQuote(db.Model):
    __tablename__ = 'BookQuotes'
    QuoteId = db.Column(db.Integer, primary_key=True)
    BookId = db.Column(db.Integer, db.ForeignKey('Books.BookId'))
    PageNumber = db.Column(db.Integer)
    Content = db.Column(db.Text)
    Note = db.Column(db.Text)
    CreatedAt = db.Column(db.DateTime, default=datetime.utcnow)
    book = db.relationship('Book', backref='quotes')

class ChatMessage(db.Model):
    __tablename__ = 'ChatMessages'
    MessageId = db.Column(db.Integer, primary_key=True)
    UserId = db.Column(db.Integer, db.ForeignKey('Users.UserId'))
    Content = db.Column(db.Text)
    IsFromAI = db.Column(db.Boolean, default=False)
    CreatedAt = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref='chat_messages')

class Task(db.Model):
    __tablename__ = 'Tasks'
    TaskId = db.Column(db.Integer, primary_key=True)
    UserId = db.Column(db.Integer, db.ForeignKey('Users.UserId'))
    Title = db.Column(db.String(200))
    Description = db.Column(db.Text)
    DueDate = db.Column(db.DateTime)
    Priority = db.Column(db.String(20))  # 'high', 'medium', 'low'
    Category = db.Column(db.String(50))  # 'work', 'personal', 'hobby'
    Status = db.Column(db.String(20))  # 'pending', 'completed'
    CreatedAt = db.Column(db.DateTime, default=datetime.utcnow)
    CompletedAt = db.Column(db.DateTime)
    user = db.relationship('User', backref='tasks')

class TaskTime(db.Model):
    __tablename__ = 'TaskTimes'
    TimeId = db.Column(db.Integer, primary_key=True)
    TaskId = db.Column(db.Integer, db.ForeignKey('Tasks.TaskId'))
    StartTime = db.Column(db.DateTime)
    EndTime = db.Column(db.DateTime)
    Duration = db.Column(db.Integer)  # Dakika cinsinden
    task = db.relationship('Task', backref='time_records')

class TaskReport(db.Model):
    __tablename__ = 'TaskReports'
    ReportId = db.Column(db.Integer, primary_key=True)
    UserId = db.Column(db.Integer, db.ForeignKey('Users.UserId'))
    ReportDate = db.Column(db.DateTime)
    CompletedTasks = db.Column(db.Integer)
    OverdueTasks = db.Column(db.Integer)
    TotalTimeSpent = db.Column(db.Integer)  # Dakika cinsinden
    ReportContent = db.Column(db.Text)
    user = db.relationship('User', backref='task_reports')

class UserSettings(db.Model):
    __tablename__ = 'UserSettings'
    SettingId = db.Column(db.Integer, primary_key=True)
    UserId = db.Column(db.Integer, db.ForeignKey('Users.UserId'))
    Theme = db.Column(db.String(20), default='light')  # 'light', 'dark'
    EmailNotifications = db.Column(db.Boolean, default=True)
    user = db.relationship('User', backref='settings')

class Reminder(db.Model):
    __tablename__ = 'Reminders'
    ReminderId = db.Column(db.Integer, primary_key=True)
    UserId = db.Column(db.Integer, db.ForeignKey('Users.UserId'), nullable=False)
    QuestionId = db.Column(db.Integer, db.ForeignKey('Questions.QuestionId'), nullable=False)
    Frequency = db.Column(db.String(20))  # 'daily', 'weekly', 'monthly'
    Time = db.Column(db.Time)  # Hatırlatma saati
    IsActive = db.Column(db.Boolean, default=True)
    LastSent = db.Column(db.DateTime)
    CreatedAt = db.Column(db.DateTime, default=datetime.now)
    
    user = db.relationship('User', backref='reminders')
    question = db.relationship('Question', backref='reminders')

class Listening(db.Model):
    __tablename__ = 'Listenings'
    ListeningId = db.Column(db.Integer, primary_key=True)
    UserId = db.Column(db.Integer, db.ForeignKey('Users.UserId'))
    Title = db.Column(db.String(200))
    IsCompleted = db.Column(db.Boolean, default=False)
    user = db.relationship('User', backref='listenings')

def create_categories():
    categories = [
        {'name': 'Matematik', 'icon': 'math.png'},
        {'name': 'Türk Dili ve Edebiyatı', 'icon': 'literature.png'},
        {'name': 'Felsefe', 'icon': 'philosophy.png'},
        {'name': 'Din', 'icon': 'religion.png'},
        {'name': 'Coğrafya', 'icon': 'geography.png'},
        {'name': 'Fizik', 'icon': 'physics.png'},
        {'name': 'Kimya', 'icon': 'chemistry.png'},
        {'name': 'Biyoloji', 'icon': 'biology.png'},
        {'name': 'Tarih', 'icon': 'history.png'},
        {'name': 'Yabancı Dil', 'icon': 'language.png'}
    ]
    
    for category in categories:
        if not Category.query.filter_by(Name=category['name']).first():
            new_category = Category(Name=category['name'])
            db.session.add(new_category)
    
    try:
        db.session.commit()
        print("Kategoriler başarıyla oluşturuldu.")
    except Exception as e:
        db.session.rollback()
        print(f"Kategori oluşturma hatası: {str(e)}")

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/welcome')
def welcome():
    return render_template('welcome.html')

@app.route('/notifications')
@login_required
def notifications():
    today = datetime.now().date()
    now = datetime.now()

    # Soru Bildirimleri için verileri çek (her tekrar tarihi için ayrı ayrı say, and_ ve or_ ile)
    today_questions = Question.query.filter(
        Question.UserId == current_user.UserId,
        Question.IsCompleted == False,
        Question.IsHidden == False,
        or_(
            and_(Question.Repeat1Date != None, db.func.cast(Question.Repeat1Date, db.Date) == today),
            and_(Question.Repeat2Date != None, db.func.cast(Question.Repeat2Date, db.Date) == today),
            and_(Question.Repeat3Date != None, db.func.cast(Question.Repeat3Date, db.Date) == today)
        )
    ).all()

    # Geçmiş soruları past_questions route'u ile aynı mantıkta çek
    past_questions = Question.query.filter(
        Question.UserId == current_user.UserId,
        Question.IsCompleted == False,
        Question.RepeatCount < 3,
        (
            (Question.RepeatCount == 0) & (db.func.cast(Question.Repeat1Date, db.Date) < today)
            |
            (Question.RepeatCount == 1) & (db.func.cast(Question.Repeat2Date, db.Date) < today)
            |
            (Question.RepeatCount == 2) & (db.func.cast(Question.Repeat3Date, db.Date) < today)
        )
    ).order_by(Question.Repeat1Date.desc()).all()

    # Görev Bildirimleri için verileri çek
    # Vade tarihi geçmiş ve tamamlanmamış görevler
    overdue_tasks = Task.query.filter(
        Task.UserId == current_user.UserId,
        Task.DueDate < now,
        Task.Status != 'completed'
    ).all()

    # Bugüne ait görevler (vade tarihi bugün olan ve tamamlanmamış)
    today_tasks = Task.query.filter(
        Task.UserId == current_user.UserId,
        Task.DueDate >= today,
        Task.DueDate < today + timedelta(days=1),
        Task.Status != 'completed'
    ).all()

    # Kitap Bildirimleri için verileri çek
    reading_books = Book.query.filter(
        Book.UserId == current_user.UserId,
        Book.IsCompleted == False
    ).all()

    # Listening Bildirimleri için verileri çek
    reading_listenings = Listening.query.filter(
        Listening.UserId == current_user.UserId,
        Listening.IsCompleted == False
    ).all()

    return render_template(
        'notifications.html',
        today_questions=today_questions,
        past_questions=past_questions,
        overdue_tasks=overdue_tasks,
        today_tasks=today_tasks,
        reading_books=reading_books,
        reading_listenings=reading_listenings,
        section='takipsistemi',
        show_sidebar=True
    )

@app.route('/mark_notification_read/<int:notification_id>', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    # ... existing code ...
    pass

@app.route('/today_questions')
@login_required
def today_questions():
    today = datetime.now().date()
    questions = Question.query.filter(
        Question.UserId == current_user.UserId,
        Question.IsCompleted == False,
        Question.IsHidden == False,
        (
            (Question.RepeatCount == 0) & (db.func.cast(Question.Repeat1Date, db.Date) == today)
            |
            (Question.RepeatCount == 1) & (db.func.cast(Question.Repeat2Date, db.Date) == today)
            |
            (Question.RepeatCount == 2) & (db.func.cast(Question.Repeat3Date, db.Date) == today)
        )
    ).order_by(Question.Repeat1Date).all()
    categories = Category.query.all()
    return render_template('today_questions.html', questions=questions, categories=categories, section='takipsistemi', show_sidebar=True)

@app.route('/past_questions')
@login_required
def past_questions():
    today = datetime.now().date()
    # Tekrar tarihi bugün veya öncesi olup, tekrar tarihi gününde tamamlanmamış sorular
    questions = Question.query.filter(
        Question.UserId == current_user.UserId,
        Question.IsCompleted == False,
        Question.RepeatCount < 3,
        (
            (Question.RepeatCount == 0) & (db.func.cast(Question.Repeat1Date, db.Date) < today)
            |
            (Question.RepeatCount == 1) & (db.func.cast(Question.Repeat2Date, db.Date) < today)
            |
            (Question.RepeatCount == 2) & (db.func.cast(Question.Repeat3Date, db.Date) < today)
        )
    ).order_by(Question.Repeat1Date.desc()).all()
    categories = Category.query.all()
    return render_template('past_questions.html', questions=questions, categories=categories, section='takipsistemi', show_sidebar=True)

@app.route('/reminders')
@login_required
def reminders():
    today = datetime.now().date()
    questions = Question.query.filter(
        Question.UserId == current_user.UserId,
        db.text("CAST([Questions].[Repeat1Date] AS DATE) > :today"),
        Question.IsCompleted == False,
        Question.RepeatCount < 3
    ).params(today=today).order_by(Question.Repeat1Date).all()
    
    categories = Category.query.all()
    return render_template('reminders.html', questions=questions, categories=categories, section='takipsistemi', show_sidebar=True)

@app.route('/set_reminder/<int:question_id>', methods=['POST'])
# ... existing code ...

@app.route('/')
def index():
    if not current_user.is_authenticated:
        return redirect(url_for('welcome'))
    
    # Bugünün sorularını say (mevcut index verisi)
    today = datetime.now().date()
    daily_questions_count = Question.query.filter(
        Question.UserId == current_user.UserId,
        db.text("CAST([Questions].[Repeat1Date] AS DATE) = :today"),
        Question.IsCompleted == False
    ).params(today=today).count()

    # Toplam soru sayısı (mevcut index verisi)
    total_questions_count = Question.query.filter_by(
        UserId=current_user.UserId
    ).count()

    # Okunan kitap sayısı (mevcut index verisi)
    books_count = Book.query.filter_by(
        UserId=current_user.UserId
    ).count()

    # İzlenen TEDx sayısı (mevcut index verisi)
    ted_talks_count = TedTalk.query.filter_by(
        UserId=current_user.UserId
    ).count()

    # Aktif görev sayısı (mevcut index verisi)
    tasks_count = Task.query.filter_by(
        UserId=current_user.UserId,
        Status='pending'
    ).count()

    # Motivasyon mesajları (hem eski index hem de questions verisi)
    motivation_messages = [
        "Başarı, küçük adımların toplamıdır!",
        "Her gün bir adım daha ileriye!",
        "Zorlandığında vazgeçme, mola ver ve devam et!",
        "Küçük adımlar büyük başarılar getirir!",
        "Bugün dünden daha iyi ol!",
        "Başarı yolunda ilerliyorsun!",
        "Kendine inan, başarabilirsin!",
        "Her tekrar seni hedefe yaklaştırır!"
    ]
    motivation_message = random.choice(motivation_messages)

    # Kategorileri ve her kategorinin soru sayısını getir
    categories = Category.query.filter(Category.Name != 'İngilizce').all()
    for category in categories:
        category.question_count = Question.query.filter_by(
            UserId=current_user.UserId,
            CategoryId=category.CategoryId,
            IsHidden=False
        ).count()

    # --- Son Aktiviteler İçin Veri Hazırlığı ---
    today = datetime.now().date()
    yesterday = datetime.now() - timedelta(days=1)
    last_7_days = datetime.now() - timedelta(days=7)

    notifications = []

    # 1. Bugünün Soruları
    today_questions_count = Question.query.filter(
        Question.UserId == current_user.UserId,
        Question.IsCompleted == False,
        Question.IsHidden == False,
        or_(
            and_(Question.Repeat1Date != None, db.func.cast(Question.Repeat1Date, db.Date) == today),
            and_(Question.Repeat2Date != None, db.func.cast(Question.Repeat2Date, db.Date) == today),
            and_(Question.Repeat3Date != None, db.func.cast(Question.Repeat3Date, db.Date) == today)
        )
    ).count()
    if today_questions_count > 0:
        notifications.append({
            'icon': 'fas fa-clock',
            'color_class': 'blue', # Renk sınıfı
            'type': 'Bugünün Soruları',
            'msg': f'{today_questions_count} soru çözülmeyi bekliyor',
            'timestamp': None,
        })

    # 2. Görev Tamamlandı (Son 24 saat)
    completed_tasks_last_24h = Task.query.filter(
        Task.UserId == current_user.UserId,
        Task.Status == 'completed',
        Task.CompletedAt >= yesterday
    ).count()
    if completed_tasks_last_24h > 0:
         notifications.append({
             'icon': 'fas fa-check-circle',
             'color_class': 'green', # Renk sınıfı
             'type': 'Görev Tamamlandı',
             'msg': f'Son 24 saatte tamamlanan {completed_tasks_last_24h} görev',
             'timestamp': None, # İsteğe bağlı olarak son tamamlanma zamanı eklenebilir
         })

    # 3. Yeni Kitap Eklendi (Son 7 gün)
    new_books_last_7_days = Book.query.filter(
        Book.UserId == current_user.UserId,
        Book.StartDate >= last_7_days
    ).count()
    # Bu bölümde kitap bildirimi ekleniyordu, artık tamamen kaldırıldı.

    # 4. Başarı Kazanıldı (Örnek Statik Mesaj)
    # Gerçek bir başarı sistemi olmadığından statik bir mesaj ekliyorum.
    notifications.append({
        'icon': 'fas fa-star',
        'color_class': 'yellow', # Renk sınıfı
        'type': 'Başarı Kazanıldı',
        'msg': 'Düzenli çalışma için +5 puan',
        'timestamp': None,
    })

    # --- Şablonu Render Et ---
    return render_template('index.html',
                         daily_questions_count=daily_questions_count,
                         total_questions_count=total_questions_count,
                         books_count=books_count,
                         ted_talks_count=ted_talks_count,
                         tasks_count=tasks_count,
                         motivation_message=motivation_message,
                         categories=categories,
                         notifications=notifications, # Yeni eklenen bildirim listesi
                         section='takipsistemi',
                         show_sidebar=True
                         )

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            # Form verilerini al
            username = request.form.get('username')
            password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')
            first_name = request.form.get('name')
            last_name = request.form.get('surname')
            email = request.form.get('email')
            class_level = request.form.get('class_level')
            year_of_birth = request.form.get('year_of_birth')
            area = request.form.get('area')
            aim = request.form.get('aim')
            security_question = request.form.get('security_question')
            security_answer = request.form.get('security_answer')

            # Zorunlu alanları kontrol et
            if not all([username, password, first_name, last_name, email, class_level, year_of_birth, area, aim, security_question, security_answer]):
                flash('Lütfen tüm zorunlu alanları doldurun.', 'error')
                return redirect(url_for('register'))

            # Kullanıcı adı kontrolü
            if User.query.filter_by(UserName=username).first():
                flash('Bu kullanıcı adı zaten kullanılıyor.', 'error')
                return redirect(url_for('register'))

            # E-posta kontrolü
            if User.query.filter_by(Email=email).first():
                flash('Bu e-posta adresi zaten kullanılıyor.', 'error')
                return redirect(url_for('register'))

            # Şifre kontrolü
            if password != confirm_password:
                flash('Şifreler eşleşmiyor.', 'error')
                return redirect(url_for('register'))

            # Şifreyi hashle
            password_hash = hashlib.sha256(password.encode()).hexdigest()

            # Yeni kullanıcı oluştur
            new_user = User(
                UserName=username,
                PasswordHash=password_hash,
                Name=first_name,
                Surname=last_name,
                Email=email,
                Class=class_level,
                YearOfBirth=int(year_of_birth),
                Area=area,
                Aim=aim,
                SecurityQuestion=security_question
            )

            # Veritabanına kaydet
            db.session.add(new_user)
            db.session.commit()

            flash('Kayıt başarılı! Şimdi giriş yapabilirsiniz.', 'success')
            return redirect(url_for('login'))

        except Exception as e:
            db.session.rollback()
            print(f"Kayıt hatası: {str(e)}")  # Hata logla
            flash('Kayıt sırasında bir hata oluştu. Lütfen tekrar deneyin.', 'error')
            return redirect(url_for('register'))

    return render_template('register.html', show_sidebar=False)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember') # 'remember' onay kutusunu al
        user = User.query.filter_by(UserName=username).first()
        
        if user and user.PasswordHash == hashlib.sha256(password.encode()).hexdigest():
            # Eğer 'remember' onay kutusu işaretli ise remember=True olarak login_user'ı çağır
            login_user(user, remember=bool(remember)) 
            flash('Başarıyla giriş yaptınız!', 'success')
            return redirect(url_for('welcome_options'))
        else:
            flash('Geçersiz kullanıcı adı veya şifre', 'danger')
    return render_template('login.html', show_sidebar=False)

@app.route('/welcome_options') # New route for the welcome options page
@login_required
def welcome_options():
    return render_template('welcome_options.html', show_sidebar=False)

@app.route('/welcome_after_login')
@login_required
def welcome_after_login():
    return redirect(url_for('welcome_options'))

@app.route('/hedefleyici')
@login_required
def hedefleyici():
    # Render the main hedefleyici template
    return render_template('hedefleyici.html', section='hedefleyici')

@app.route('/kitaplarim')
@login_required
def kitaplarim():
    books = Book.query.filter_by(UserId=current_user.UserId).all()
    return render_template('kitaplarim.html', books=books, section='hedefleyici')

@app.route('/gorevlerim')
@login_required
def gorevlerim():
    filter_type = request.args.get('filter', 'all')
    now = datetime.now()
    # Aktif görevler
    active_tasks = Task.query.filter_by(UserId=current_user.UserId, Status='new').filter(Task.Title != 'Serbest Çalışma').order_by(Task.DueDate).all()
    # Son tamamlanan görevler
    completed_tasks = Task.query.filter_by(UserId=current_user.UserId, Status='completed').filter(Task.Title != 'Serbest Çalışma').order_by(Task.CompletedAt.desc()).all()
    # 24 saatten eski tamamlananları filtrele
    if filter_type == 'completed':
        completed_tasks = [t for t in completed_tasks if t.CompletedAt and (now - t.CompletedAt) <= timedelta(hours=24)]
    if filter_type == 'completed':
        tasks = completed_tasks
    else:
        tasks = active_tasks
    
    # --- Günlük Rapor Verilerini Çek ---
    today = datetime.now().date()
    # Tamamlanan görevler (bugün tamamlananlar)
    completed_tasks_report = Task.query.filter(
        Task.UserId == current_user.UserId,
        Task.Status == 'completed',
        db.text("CAST([Tasks].[CompletedAt] AS DATE) = :today")
    ).params(today=today).all()
    # Gecikmiş görevler (Status='new' ve DueDate < now)
    overdue_tasks_report = Task.query.filter(
        Task.UserId == current_user.UserId,
        Task.Status == 'new',
        Task.DueDate < datetime.now()
    ).all()
    # Toplam çalışma süresi (görev türü fark etmeksizin, o günün tüm TaskTime kayıtları)
    # Not: TaskTime modelinin app.py'de tanımlı olması gerekir.
    # TaskTime import edildiğinden emin olun.
    try:
        total_time = db.session.query(db.func.sum(TaskTime.Duration)).join(Task).filter(
            Task.UserId == current_user.UserId,
            db.text("CAST([TaskTimes].[StartTime] AS DATE) = :today")
        ).params(today=today).scalar() or 0
    except: # Eğer TaskTime veya ilişki bulunamazsa hata olmaması için
         total_time = 0

    # Pomodoro süreleri (Serbest Çalışma görevlerinden)
    try:
        pomodoro_time = db.session.query(db.func.sum(TaskTime.Duration)).join(Task).filter(
            Task.UserId == current_user.UserId,
            Task.Title == 'Serbest Çalışma',
            db.text("CAST([TaskTimes].[StartTime] AS DATE) = :today")
        ).params(today=today).scalar() or 0
    except: # Eğer TaskTime veya ilişki bulunamazsa hata olmaması için
        pomodoro_time = 0

    total_tasks_for_rate = len(completed_tasks_report) + len(overdue_tasks_report)
    completion_rate = int((len(completed_tasks_report) / total_tasks_for_rate) * 100) if total_tasks_for_rate > 0 else 0

    # --- Şablonu Render Et ---
    return render_template(
        'gorevlerim.html',
        active_tasks=active_tasks,
        completed_tasks=completed_tasks, # Son 24 saatlik
        tasks=tasks,
        filter=filter_type,
        section='hedefleyici',
        now=now
    )

# Listening video linkleri (YouTube video ID'leri)
LISTENING_VIDEO_IDS = [
    'we4KiShNjlA', '26PrgjTboVQ', '2USh8OmgiJE', 'Y681hXWwhQY', 'wkjSBC-_bDA', 'FZDImEiPgMk',
    'g8q-Nq-ajx8', '1iHeeMlOsyc', 'HZd53TJpmoQ', 'JjESWHykTJQ', '5R3WdBE1-JM', 'zsOnAHAY6to',
    'fG7dJ6A3l7w', 'Mqnlb_yj3bY', 'Joc4kJ4M1Bk', 'oTPZWpQ9pbA', '7F1iJZr-p4E', '_5siHrpPnmw',
    'uxtXEuK05-w', 'j8d5kkKfDbo', 'FKwmUNffu7M', 'DsQMLrPdLf8', 'V2eW5jGQe8I', 'qoNRZKgLDhg',
    'vq2x7k_nofw', 'KkrhHUeMjIU', 'h_pvijqmolQ', 'xy27CfuFtJE', 'R_0E8HBxYN8', 'iKzpnVWdZ70',
    'mpxwlItsDA8', 'u6QrbYDsj1g', '7BIp53who2A', 'KLz5u2pH-yM', 'ybQORSQWWdc', '4YHtcINPkjM',
    'UIg6n0ypaHw', 'vP3VOKBcloo', 'TVHePsQLa3w', 'FjU9qyTZ_OU', 'WjFQIP8w5Jw', 'p0SUyXLS-ME',
    'j2PdEQpu5js', 'xGhbhWUqL-w', 's1HxJVusR2w', '3hwEplr-g5w', 'Kmc7TtKkTs4', 'Y5sSvaAKF90',
    'xltewJgQVV0', '8p7HytjrKj4', 'rvZWLTtEyoU', 'Xbv4IIqwW-4', '2zFyz6uO9-0', 'Fez57g8jMNM',
    'wlEuiYq8tcM', 'vdS3QBy9WeU', 'Egn-pNaM27U', 'H4yeMxZ07zY', 'SiQInf3_NIE', 'WsKg6HsoDaw',
    'rQK37u961Eo', 'CcMhB1DD-Gg', 'UEH3oRSgVXQ', '8P_ya85lxzw', '1lNbOH-cvl8', 'MY1Rk1polgM',
    'Tp8xIgyyK7I', 'HZi9ls9emUE', 'WunqZ9SF4hU', 'uhfVT5iAtMM', 'Ag7-U4ga9mA', '5kr5ADrMeYU',
    'tieXTqc15rE', 'UhR-Bn4UII0', 'Oq2bnLC_DXU', 'StEB_wntlZ0', 'tHZRXN_pVi8', 'uEgpgnKNF9Q',
    'TejfD82oLfU', 'rWHGKGS7zSc', 'bywWgD9yJq0', 'JZ_EV9DPtt0', 'VkLIUXjNwYc', 'mLYwM-kdbwM',
    '8XOA3-XwTaQ', 'jDqsNK1hmM8', 'mv3Fx8-O9co', 'v5p7WY9nOJM', 'c5Ppkvg7xHI', 'ACG6qr4waWU',
    'eEBc_QB5VIQ', 'jwAoLZXFLjo', 'bRzP7hwIGWE', 'lC_lCOxR5e0', 'Y3vHuw97AiA', 'DdOburEdIPg',
    'tyvMjvvrq74', 'bJq9kPc_-tw', 'YY1mN_ibteU', 'WBLuy_YU-Zw', 'AJRqLvAZp4Q', '6R0Wy4kwxes',
    'K-9-dtJpZ9c', 'wCgPjVzREqs', 'Z51Q29u4CWc', 'zFpk5FsNndM', 'bizx7atWYkQ', 'vBiBiCdlXes',
    'yz4a2soLDl4', 'WeNuLW5uPGc', 'tD-6xHAHrQ4', 'af7VzZTzmlg', '0YpwaYUGF94', 'DaW-Kha9qAM',
    'AlrXqakHPuk', 'rTSSchYtAXk', 'eXp4Mt1S8Lg', 'Q6MAcmJdYdA', 'MwqWPzDK6Hs', 'dRgwAU7Y4yY',
    '2OjMuGloIRo', 'mEoSi6l99OE', 'OHExziy0xLY', 'TyC762eWXzo', 'jdu6GCU42zU', 'wNJQPn-SLk8',
    'Dk8AAU_UdVk', 'el2iTDgF0y8', 'fgZl4Mp0Y_w', 'VZcW--Wi7mY', 'EiCs_8ZKVJc', '3-icphihD6Y',
    'wAV-vbHLn3Q', 'sm6EtQg-hxw', 'KB4Mn5XHdMc', 'yoFhTmWrYz8', 'fFLLQEFgK6s', 'wgO7yK7NZpg',
    'JFIhleM0Kbo', 'fJoCs5Z_QvE', 'MVGl4QJTZqY', 'ziimjZ-OrgU', 'Eofp060BEnw', 'rCh9MQibJ3c',
    'nQrS3-L9id4', 'kglKCEGytsk', 'oviVRMuVgAs', 'KFajmtdj-J0', 'LrZGtTuMpk8', 'O3tp5Y9lH88',
    'a66Gx6c-ZeE', 'luh9xTJ7ExM', 'l1DLZhZXsw0', '9hus12iCyL8', '5IqtP2fzNlA', 'pIOkrFZ-D1w',
    '5ZQ65RbsAB8', 'Dd3QvqyT2x4', '0VPwGqiWT04', 'w4BvAaL1S3g', 'hGzKWfQOKeQ', '5pxlzf0Tz_0',
    'NODkUzmamP8', 'NhVXCMjhmho', 'fGeQH4_lH3Q', 'l66TJNGKQFQ', 'P0siKVerEUg', 'ZDzklx1T6E0',
    'ipktRrpIjz8', 'Nb7wVCJ68YY', '6Y3rL9LVV9w', '9ifQ3xRz4hM', 'nNlS1lWEiQA', 'k-pl1DwhIFk',
    'Zho2dPAiZ74', '16hzMhzgaM0', 'aq1snwtQUQ4', '9g5X11dH-Lc', 'N3cE1lO8aCE', 'fWzD45xDQDo',
    'DxR2waii1Ck', 'rqPeFokY-T8', 'XMfNMnH8KyQ', '9EKvO6tu7a0', 'rT_zp4KQ4p8', 'MmODCOXX_2c',
    'Y7QvqbwRjLQ', 'fKg0nLaQzn4', 'tYKm_8dXmMc', 'WaQWL1Qr9i8', 'SYh7YSKxL6U', 'HMKqVxiPFVI',
    '_zmMl7T8164', 'r5iFFBpFSlU', 'hM4HYNE32wQ', 'PL90RepTkhk', '1niTruE-PNs', '7ZJxdmEKn0Q',
    'AQSGyV0rh5Y', 't2J-_-v-Spw', 'Z2xcl93o7F0', 'C4vC-Y3USfk', 'a5dR3olXGWU', 'H5BVbrZ64bQ',
    'wcEgBAORLM4', 'A2lIdSnv1Vw', '91liS87P9CY', 'hlsBs3XSDUM', 'XGx13d-QdIM', 'jnFeXaL02Fg',
    'eoXv4JgwjeM', 'RN6HGltVp2A', '8yzy7ucYcII', 'mxwJsvMj7JA', '31FjeWvLIxM', '7L2oJIob6X0',
    'B_TWPas7ZAw', 'WKmsxJkJCqM', 'Iigy0LpJjN4', '5w-zLrlTcY4', 'HKfDfWrCwEA', 'drWlSGryMkY',
    'jkMW1qtz01c', '4KcXgXgSxDI', 'P2UOO6L8rio', 'NGY-HJ_l35E', '8E8DQnmd4zs', 'X5YjfOKBffU',
    'x4HNOP6Ko6Y', '_WHCjv1MRmM', 'd6BGuntMwCM', 'CNoggf2Ibek', '0emVXTaESvs', 'EcTdPfg4wO8',
    'AfNSMykrG1I', 'lJMPosxMV2M', 'OQAS9pqC8V4', '9ry87N2tC_k', 'aA35kVsHuCo', 'jp1FCIQUBkw',
    'xf2RF9vx-G4', 'MrCklBFENkQ', 'COB_5wL_xv4', 'vHtvi6EtGkw', 'WAaAoXsIHvI', '2Z5iHh2omRA',
    'CRFHPkLgAKc', 'RS4MrptnnP8', 'Fxh3HeJvRhw', 'JaGXfJBx0BM', '2K2gB8b7qUw', 'Cn0oOdwryPo',
    'LC_3i_EPd6s', '9mIYleesmSU', 'gu_GfdJpdsA', 'B1hl-eRpGmI', '4pDImFxHNuY', 'gJ0BSnuX1GA',
    'dJZ9CSbGueU', 'atPNphv-NEI', 'cSlPuxN_yws', '1jgT2Wgsox8', 'iNRqZNXsB8k', 'XqZoDfJwNKE',
    'jO8d0wwXyk8', 'WVPcKah4CbA', 'lZIacnbb52Q', 'g2Ki5GeMevU', 's94XlBnJwZU', 'HTdQ8bDEhAQ',
    'Tcf1dbiWKsk', 'f0FkoUFJUo0', 'WbAeqhkL8aA', 'savzorNB_sI', 'gfnyMyCZjqA', '0R9NLQM4ZKA',
    'fVpEwW_4Yt4', 'cr2TXucwjVk', 'DvBWBSl2DKA', 'WcION1-0_VI', 'naB_3XYRtew', 'xZxmMQCZsu4',
    '0UOdAKVdbMo', '-aLUbUMVYAc', 'O3vGss0ELfg', 'iOao1dfGP2s', '8tFbax73NtA', 'hmnW6F3-KqE',
    'Dfc3ZqVwrNc', 'HZpEq-r7_Nw', 'obpKWRcXezA', '9mQkGyApBX0', '3DL3Htt8vck', 'kjVd228S-yQ',
    'lVFXbzzm1Bw', 'AhgRjqgrgkk', 'WUcNXALk_fQ', 'x4xlQTP-XDU', '0E9KurvLzqE', '-Bi-T52-F-s',
    'IKDqlHCOxrg', 'GUGtU7Ii1yk', 'NFZH67BgO5c', 'ZRkEwwOyTa4', 'l22DvDwD6Ow', 'oRhVmbfy1sY',
    '4yiVfwDkntQ', 'o2pdhO76ld4', 'MgoZwkSXzGw', 'ktgDXNML2uI', 'BCzbEQlk3to', 'RNZwLILj0Uw',
    'Engjh-aEevc', '2FqYQaLwWLo', 'adFreL6VqQY', 'ypXp6-MT_Co', 'k_qKbYrOq98', 'o8LAh3AUyXs',
    'vezrsZv5UcE', 'pfJ15WGdoWo', 'as-vRWOmJWU', 'Umb9e-L2DVg', 'GdGcE_-_T8Y', 'NVgpf-SFs0g',
    'aMe78rHCzF0', 'K-Nps59NeBA', 'EBAc4PIQC2Y', 'iHLgOqZ5CXc', '_q8geBY3vPA', 'KNhwmHq1asM',
    'dKUwijDI2KE', 'NwPkZgd6L-o', 'hfNU4h38Iis', 'cMjvx9GfaO0', 'uiSNeh10yPc', 'ObuDxIh89V8',
    'NLj72KSNZoo', 'tOxD9PEH8DU', 'WW4RnT1YuLg', 'URw3ITsBU6s', 'BvNNuSz-EFw', 'z3OykfkE_R0',
    'ZxTpScOY8c4', 'kU65ZNNOPc4', 'gcuCCv-n7YQ', 'RwBO6Hi5FvE', 'Xv5i11wmpQM', 'glK2V-7DJD8',
    'u6Ke0rdjKEg', '9bSMwNO_OCY', '3nw9cWGmI5E', 'xg7OWeR7tr4', '_StSUVR6_ok', 'Ac67KPcSqsM',
    'mQ8P4E7LKqI', 'n5p85sRPTLo', 'uoujHpVJSe8', 'ibQx65L7mcI', 'bLkvQrqkVCI', 'izx0SSLoTls',
    'G_a3ILspt-w', 'Jde-H7WW7BQ', '3fBxa1IEb74', 'xwbAWiqMuNE', 'Dn-uY9q4rLs', 'u6GOoQnJicg',
    '0cg27Y1atuI', 'Nn0QvidINiA', 'ojgogr0St9g', 'tnmgIUxfFE4', '6FY51RKsK3c', '1MqRALnIvWY',
    'SmKTe9okerg', 'gdIskHlqRwc', '69o1qyxZBuw', '360sNcECglc', 'LXw2xdWqkS0', 'lvhEPmiaeMs',
    'NrU4Cx2gAoU', 'l5dsQB0rqms', '-yJj6rYX6H0', 'uziFF8NSxaQ', 'wMQjmpVgor8', 'AhoslePC6yI',
    'hCMKloIx8vk', '95yoKdm5sMk', 'DD9IbPnCxMM', 'z2JsYmGmF8E', 'Pzq2slM4Wu4', 'bq9U_3exOLo',
    'x4qC_ed3dRg', 'NUHIoZFuDAw', 'l31dAwfYjhI', 'RTi-D3ykhqM', 'aOiuSsnWEik', 'bGsUkpvV9_w',
    'KaFF0__DnoM'
]

def get_today_video_ids():
    watched = session.get('watched_listening_videos', [])
    available = [vid for vid in LISTENING_VIDEO_IDS if vid not in watched]
    if len(available) < 2:
        # Tüm videolar izlendiyse sıfırla
        session['watched_listening_videos'] = []
        available = LISTENING_VIDEO_IDS.copy()
    # Her gün aynı 2 video gelsin diye tarihi hashle
    today = datetime.now().strftime('%Y-%m-%d')
    hash_val = sum([ord(c) for c in today])
    available.sort(key=lambda x: (ord(x[0]) + hash_val))
    return available[:2]

@app.route('/listening')
@login_required
def listening():
    video_ids = get_today_video_ids()
    return render_template('listening.html', video_ids=video_ids, section='hedefleyici')

@app.route('/mark_listening_watched', methods=['POST'])
@login_required
def mark_listening_watched():
    data = request.get_json()
    video_id = data.get('video_id')
    if not video_id:
        return jsonify({'success': False, 'error': 'Video ID eksik'}), 400
    watched = session.get('watched_listening_videos', [])
    if video_id not in watched:
        watched.append(video_id)
        session['watched_listening_videos'] = watched
    return jsonify({'success': True})

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        # Formdan gelen verileri al
        current_user.Name = request.form.get('name')
        current_user.Surname = request.form.get('surname')
        current_user.Class = request.form.get('class')
        current_user.YearOfBirth = request.form.get('year_of_birth')
        current_user.Email = request.form.get('email')
        current_user.PhoneNumber = request.form.get('phone')
        current_user.Area = request.form.get('area')
        current_user.Aim = request.form.get('aim')

        # Şifre değişikliği kontrolü
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        if current_password or new_password or confirm_password:
            # Mevcut şifrenin doğru olup olmadığını kontrol et
            if hashlib.sha256(current_password.encode()).hexdigest() != current_user.PasswordHash:
                flash('Mevcut şifreniz yanlış.', 'error')
                return redirect(url_for('profile'))

            # Yeni şifrelerin eşleşip eşleşmediğini kontrol et
            if new_password != confirm_password:
                flash('Yeni şifreler eşleşmiyor.', 'error')
                return redirect(url_for('profile'))

            # Yeni şifreyi kaydet
            current_user.PasswordHash = hashlib.sha256(new_password.encode()).hexdigest()

        try:
            db.session.commit()
            flash('Profil başarıyla güncellendi.', 'success')
            return redirect(url_for('profile'))
        except Exception as e:
            db.session.rollback()
            flash('Profil güncellenirken bir hata oluştu: ' + str(e), 'error')
            return redirect(url_for('profile'))

    return render_template('profile.html', section='takipsistemi', show_sidebar=True)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/add_question', methods=['GET', 'POST'])
@login_required
def add_question():
    if request.method == 'POST':
        try:
            content = request.form.get('content')
            category = request.form.get('category')
            topic = request.form.get('topic')  # Yeni eklenen alan
            question_image = request.files.get('question_image')
            difficulty = request.form.get('difficulty') # Zorluk seviyesini al
            # Check if required fields (category, topic, and difficulty) are present.
            if not category or not topic or not difficulty:
                flash('Lütfen tüm zorunlu alanları doldurun.', 'error')
                return redirect(url_for('add_question'))
            content = content if content is not None else ''
            image_path = None
            now = datetime.now() # Soru eklenme zamanı
            repeat1_date = now + timedelta(minutes=1)
            repeat2_date = now + timedelta(days=10)
            repeat3_date = now + timedelta(days=20)
            if question_image and question_image.filename:
                try:
                    filename = secure_filename(question_image.filename)
                    unique_filename = f"{now.strftime('%Y%m%d_%H%M%S')}_{filename}"
                    upload_folder = os.path.join(app.static_folder, 'uploads')
                    if not os.path.exists(upload_folder):
                        os.makedirs(upload_folder)
                    image_path = f"uploads/{unique_filename}"
                    full_path = os.path.join(app.static_folder, 'uploads', unique_filename)
                    question_image.save(full_path)
                except Exception as e:
                    flash('Görsel yüklenirken bir hata oluştu.', 'error')
            new_question = Question(
                UserId=current_user.UserId,
                Content=content,
                CategoryId=category,
                Topic=topic,  # Yeni eklenen alan
                DifficultyLevel=difficulty, # Zorluk seviyesini ata
                PhotoPath=None,
                IsCompleted=False,
                IsViewed=False,
                IsRepeated=False,
                RepeatCount=0,
                Repeat1Date=repeat1_date,
                Repeat2Date=repeat2_date,
                Repeat3Date=repeat3_date,
                Explanation=None,
                ImagePath=image_path
            )
            db.session.add(new_question)
            db.session.commit()

            # Yeni Soru Eklendi bildirimi oluştur
            new_notification = Notification(
                UserId=current_user.UserId,
                NotificationType='Yeni Soru Eklendi',
                Schedule=datetime.now()
            )
            db.session.add(new_notification)
            db.session.commit() # Bildirimi kaydet

            flash('Soru başarıyla eklendi.', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            flash('Soru eklenirken bir hata oluştu: ' + str(e), 'error')
            return redirect(url_for('add_question'))
    # Kategorileri veritabanından çek
    categories = Category.query.order_by(Category.Name).all()
    if not categories:
        # Kategori yoksa otomatik ekle
        create_categories()
        categories = Category.query.order_by(Category.Name).all()
        if not categories:
            flash('Hiç kategori bulunamadı ve otomatik eklenemedi. Lütfen yöneticinize başvurun.', 'error')
            return render_template('add_question.html', categories=[], section='takipsistemi', show_sidebar=True)
    return render_template('add_question.html', categories=categories, section='takipsistemi', show_sidebar=True)

@app.route('/edit_question/<int:question_id>', methods=['GET', 'POST'])
@login_required
def edit_question(question_id):
    question = Question.query.get_or_404(question_id)
    if question.UserId != current_user.UserId:
        flash('Bu soruyu düzenleme yetkiniz yok.')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        question.Content = request.form.get('content')
        question.CategoryId = request.form.get('category')
        
        try:
            db.session.commit()
            flash('Soru başarıyla güncellendi.')
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            flash('Soru güncellenirken bir hata oluştu.')
            return redirect(url_for('edit_question', question_id=question_id))
    
    categories = Category.query.order_by(Category.Name).all()
    return render_template('edit_question.html', question=question, categories=categories, section='takipsistemi', show_sidebar=True)

@app.route('/view_today_question/<int:question_id>')
@login_required
def view_today_question(question_id):
    question = Question.query.get_or_404(question_id)
    if question.UserId != current_user.UserId:
        abort(403) # Kullanıcı sorunun sahibi değilse izin verme
        
    # Notları getir (varsa)
    notes = Note.query.filter_by(QuestionId=question.QuestionId).all()

    # Favori bilgisini kontrol et
    is_favorite = Favorite.query.filter_by(UserId=current_user.UserId, QuestionId=question.QuestionId).first() is not None

    return render_template('view_today_question.html', question=question, notes=notes, is_favorite=is_favorite, section='takipsistemi', show_sidebar=True) # section'ı isteğe göre ayarlayabilirsiniz

@app.route('/view_question/<int:question_id>')
@login_required
def view_question(question_id):
    question = Question.query.get_or_404(question_id)
    if question.UserId != current_user.UserId:
        flash('Bu soruyu görüntüleme yetkiniz yok.', 'error')
        return redirect(url_for('index'))
    
    # Notları getir
    notes = Note.query.filter_by(QuestionId=question_id).order_by(Note.NoteId.desc()).all()
    
    # Favori durumunu kontrol et
    is_favorite = Favorite.query.filter_by(
        QuestionId=question_id,
        UserId=current_user.UserId
    ).first() is not None
    
    # Tekrar durumunu hesapla
    repeat_status = {
        'count': question.RepeatCount,
        'is_completed': question.IsCompleted,
        'is_repeated': question.IsRepeated,
        'dates': {
            'repeat1': question.Repeat1Date,
            'repeat2': question.Repeat2Date,
            'repeat3': question.Repeat3Date
        }
    }
    # section parametresi query string ile gelirse onu kullan, yoksa defaultu kullan
    section = request.args.get('section', 'takipsistemi')
    return render_template('view_question.html', 
                         question=question, 
                         notes=notes,
                         is_favorite=is_favorite,
                         repeat_status=repeat_status,
                         section=section, # section artık dinamik
                         show_sidebar=True
                         )

@app.route('/add_note/<int:question_id>', methods=['POST'])
@login_required
def add_note(question_id):
    try:
        question = Question.query.get_or_404(question_id)
        if question.UserId != current_user.UserId:
            return jsonify({'success': False, 'error': 'Bu işlem için yetkiniz yok.'}), 403

        data = request.get_json()
        if not data or 'content' not in data:
            return jsonify({'success': False, 'error': 'Not içeriği gerekli.'}), 400

        note = Note(
            QuestionId=question_id,
            Content=data['content']
        )
        db.session.add(note)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'note': {
                'id': note.NoteId,
                'content': note.Content
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/delete_question/<int:question_id>', methods=['POST'])
@login_required
def delete_question(question_id):
    try:
        question = Question.query.get_or_404(question_id)
        if question.UserId != current_user.UserId:
            return jsonify({'success': False, 'error': 'Bu işlem için yetkiniz yok.'}), 403

        # Önce favorilerden sil
        Favorite.query.filter_by(QuestionId=question_id).delete()
        
        # Sonra soruyu sil
        db.session.delete(question)
        db.session.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/mark_completed/<int:question_id>', methods=['POST'])
@login_required
def mark_completed(question_id):
    question = Question.query.get_or_404(question_id)
    if question.UserId != current_user.UserId:
        abort(403)

    # Tekrar sayısını artır
    if question.RepeatCount < 3:
        question.RepeatCount += 1

    # Eğer tüm tekrarlar tamamlandıysa soruyu tamamlandı olarak işaretle
    if question.RepeatCount >= 3:
        question.IsCompleted = True
        #question.CompletedAt = datetime.now() # CompletedAt sadece soru tamamen bitince mi set edilmeli? Şimdilik RepeatCount >= 3 olunca set etmiyorum.

    db.session.commit()

    # Kullanıcıyı aynı soru detay sayfasına geri yönlendir yerine JSON yanıtı döndür
    # flash('Tekrar tamamlandı!', 'success') # Flash mesajı istemci tarafında gösterilebilir
    return jsonify({'success': True, 'message': 'Tekrar tamamlandı!'})

@app.route('/settings')
@login_required
def settings():
    return render_template('settings.html', section='takipsistemi', show_sidebar=True)

@app.route('/category/<int:category_id>')
@login_required
def category_questions(category_id):
    category = Category.query.get_or_404(category_id)
    
    # Get the selected topic from the query parameters, default to None
    selected_topic = request.args.get('topic')

    # Base query for questions in this category for the current user, not hidden
    query = Question.query.filter_by(
        UserId=current_user.UserId,
        CategoryId=category_id,
        IsHidden=False
    )
    
    # If a topic is selected, filter the query by topic
    if selected_topic:
        # Handle the case where "Diğer" (Other) is selected for questions with no topic
        if selected_topic == "Diğer":
            query = query.filter(Question.Topic == None)
        else:
            query = query.filter_by(Topic=selected_topic)

    questions = query.order_by(Question.Topic).all()
    
    # Get all unique topics for this category and user (for the filter dropdown)
    all_topics_query = Question.query.with_entities(Question.Topic).filter_by(
        UserId=current_user.UserId,
        CategoryId=category_id,
        IsHidden=False
    ).distinct()
    all_topics = [topic[0] if topic[0] is not None else "Diğer" for topic in all_topics_query]
    all_topics.sort() # Sort topics alphabetically

    return render_template('category_questions.html', 
                         category=category, 
                         questions=questions, # Pass filtered questions
                         all_topics=all_topics, # Pass all unique topics for the filter
                         selected_topic=selected_topic, # Pass the currently selected topic
                         section='takipsistemi', # Set section for sidebar
                         show_sidebar=True # Show sidebar
                         )

@app.route('/favorites')
@login_required
def favorites():
    categories = Category.query.all() # Tüm kategorileri çek
    category_id = request.args.get('category') # URL'den kategori ID'sini al

    query = Question.query.join(
        Favorite,
        Question.QuestionId == Favorite.QuestionId
    ).filter(
        Favorite.UserId == current_user.UserId
    ).order_by(Question.Repeat1Date)

    if category_id:
        try:
            category_id = int(category_id)
            query = query.filter(Question.CategoryId == category_id)
        except ValueError:
            # Geçersiz kategori ID'si durumunda hata yönetimi veya tüm favorileri gösterme
            flash('Geçersiz kategori seçimi.', 'warning')
            pass # Hata durumunda filtreleme yapma

    questions = query.all()

    return render_template('favorites.html', questions=questions, categories=categories, selected_category_id=category_id, section='takipsistemi', show_sidebar=True)

@app.route('/toggle_favorite/<int:question_id>', methods=['POST'])
@login_required
def toggle_favorite(question_id):
    try:
        question = Question.query.get_or_404(question_id)
        if question.UserId != current_user.UserId:
            return jsonify({'success': False, 'error': 'Bu işlem için yetkiniz yok.'}), 403

        # Favori durumunu kontrol et
        favorite = Favorite.query.filter_by(
            QuestionId=question_id,
            UserId=current_user.UserId
        ).first()

        if favorite:
            # Favori varsa sil
            db.session.delete(favorite)
        else:
            # Favori yoksa ekle
            new_favorite = Favorite(
                QuestionId=question_id,
                UserId=current_user.UserId
            )
            db.session.add(new_favorite)
        
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/get_reminders')
@login_required
def get_reminders():
    try:
        reminders = Reminder.query.filter_by(
            UserId=current_user.UserId,
            IsActive=True
        ).all()
        
        reminder_list = []
        for reminder in reminders:
            question = Question.query.get(reminder.QuestionId)
            if question and not question.IsCompleted:
                reminder_list.append({
                    'id': reminder.ReminderId,
                    'question_id': reminder.QuestionId,
                    'question_content': question.Content[:100] + '...' if len(question.Content) > 100 else question.Content,
                    'frequency': reminder.Frequency,
                    'time': reminder.Time.strftime('%H:%M'),
                    'category': question.category.Name
                })
        
        return jsonify({'success': True, 'reminders': reminder_list})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/delete_reminder/<int:reminder_id>', methods=['POST'])
@login_required
def delete_reminder(reminder_id):
    try:
        reminder = Reminder.query.get_or_404(reminder_id)
        if reminder.UserId != current_user.UserId:
            return jsonify({'success': False, 'error': 'Bu hatırlatıcıya erişim izniniz yok.'})
        
        db.session.delete(reminder)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

def check_reminders():
    """Hatırlatıcıları kontrol eden ve bildirim gönderen fonksiyon"""
    with app.app_context():
        try:
            now = datetime.now()
            current_time = now.time()
            
            # Aktif hatırlatıcıları al
            reminders = Reminder.query.filter_by(IsActive=True).all()
            
            for reminder in reminders:
                # Son gönderim zamanını kontrol et
                if reminder.LastSent:
                    time_diff = now - reminder.LastSent
                    
                    # Frekansa göre kontrol
                    if reminder.Frequency == 'daily' and time_diff.days < 1:
                        continue
                    elif reminder.Frequency == 'weekly' and time_diff.days < 7:
                        continue
                    elif reminder.Frequency == 'monthly' and time_diff.days < 30:
                        continue
                
                # Hatırlatma saatini kontrol et
                if reminder.Time.hour == current_time.hour and reminder.Time.minute == current_time.minute:
                    # Bildirim gönder
                    question = Question.query.get(reminder.QuestionId)
                    if question and not question.IsCompleted:
                        notification = Notification(
                            UserId=reminder.UserId,
                            NotificationType='reminder',
                            TaskId=None,
                            Schedule=now
                        )
                        db.session.add(notification)
                        reminder.LastSent = now
                        db.session.commit()
                        
                        print(f"Hatırlatma gönderildi: {question.Content[:50]}...")
        
        except Exception as e:
            print(f"Hatırlatıcı kontrolü hatası: {str(e)}")

# Hatırlatıcı kontrolü için zamanlanmış görev
def schedule_reminder_check():
    while True:
        check_reminders()
        time.sleep(60)  # Her dakika kontrol et

# Arka planda çalışacak hatırlatıcı thread'ini başlat
reminder_thread = threading.Thread(target=schedule_reminder_check, daemon=True)
reminder_thread.start()

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(Email=email).first()
        
        if user:
            # Benzersiz bir token oluştur
            token = secrets.token_urlsafe(32)
            expires_at = datetime.now() + timedelta(hours=24)
            
            # Token'ı veritabanına kaydet
            reset_token = PasswordResetToken(
                UserId=user.UserId,
                Token=token,
                ExpiresAt=expires_at
            )
            db.session.add(reset_token)
            db.session.commit()
            
            # E-posta gönder
            reset_url = url_for('reset_password', token=token, _external=True)
            msg = Message('Şifre Sıfırlama',
                        recipients=[user.Email])
            msg.body = f'''Şifrenizi sıfırlamak için aşağıdaki bağlantıya tıklayın:
{reset_url}

Bu bağlantı 24 saat boyunca geçerlidir.

Eğer bu isteği siz yapmadıysanız, bu e-postayı görmezden gelebilirsiniz.
'''
            mail.send(msg)
            
            flash('Şifre sıfırlama bağlantısı e-posta adresinize gönderildi.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Bu e-posta adresi ile kayıtlı bir kullanıcı bulunamadı.', 'error')
    
    return render_template('forgot_password.html', show_sidebar=False)

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    reset_token = PasswordResetToken.query.filter_by(Token=token, IsUsed=False).first()
    
    if not reset_token or reset_token.ExpiresAt < datetime.now():
        flash('Geçersiz veya süresi dolmuş şifre sıfırlama bağlantısı.', 'error')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Şifreler eşleşmiyor.', 'error')
            return redirect(url_for('reset_password', token=token))
        
        # Şifreyi güncelle
        user = User.query.get(reset_token.UserId)
        user.PasswordHash = hashlib.sha256(password.encode()).hexdigest()
        
        # Token'ı kullanıldı olarak işaretle
        reset_token.IsUsed = True
        
        db.session.commit()
        flash('Şifreniz başarıyla güncellendi. Şimdi giriş yapabilirsiniz.', 'success')
        return redirect(url_for('login'))
    
    return render_template('reset_password.html', show_sidebar=False)

@app.route('/report')
@login_required
def report():
    today = datetime.now().date()
    # Tamamlanan görevler (bugün tamamlananlar)
    completed_tasks = Task.query.filter(
        Task.UserId == current_user.UserId,
        Task.Status == 'completed',
        db.text("CAST([Tasks].[CompletedAt] AS DATE) = :today")
    ).params(today=today).all()
    # Gecikmiş görevler (Status='new' ve DueDate < now)
    overdue_tasks = Task.query.filter(
        Task.UserId == current_user.UserId,
        Task.Status == 'new',
        Task.DueDate < datetime.now()
    ).all()
    # Toplam çalışma süresi (görev türü fark etmeksizin, o günün tüm TaskTime kayıtları)
    total_time = db.session.query(db.func.sum(TaskTime.Duration)).join(Task).filter(
        Task.UserId == current_user.UserId,
        db.text("CAST([TaskTimes].[StartTime] AS DATE) = :today")
    ).params(today=today).scalar() or 0
    # Pomodoro süreleri (Serbest Çalışma görevlerinden)
    pomodoro_time = db.session.query(db.func.sum(TaskTime.Duration)).join(Task).filter(
        Task.UserId == current_user.UserId,
        Task.Title == 'Serbest Çalışma',
        db.text("CAST([TaskTimes].[StartTime] AS DATE) = :today")
    ).params(today=today).scalar() or 0
    total_tasks = len(completed_tasks) + len(overdue_tasks)
    completion_rate = int((len(completed_tasks) / total_tasks) * 100) if total_tasks > 0 else 0
    return render_template(
        'report.html',
        report_date=today.strftime('%d.%m.%Y'),
        completed_count=len(completed_tasks),
        overdue_count=len(overdue_tasks),
        total_time=pomodoro_time,
        completed_tasks=completed_tasks,
        overdue_tasks=overdue_tasks,
        completion_rate=completion_rate,
        section='hedefleyici',
        show_sidebar=False
    )

@app.route('/pomodoro_settings')
@login_required
def pomodoro_settings():
    return render_template('pomodoro_settings.html', section='takipsistemi', show_sidebar=True)

@app.route('/timer')
@login_required
def timer():
    return render_template('timer.html', section='takipsistemi', show_sidebar=True)

@app.route('/hide_question/<int:question_id>', methods=['POST'])
@login_required
def hide_question(question_id):
    question = Question.query.get_or_404(question_id)
    if question.UserId != current_user.UserId:
        return jsonify({'success': False, 'error': 'Bu işlem için yetkiniz yok'}), 403
    
    try:
        question.IsHidden = True
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/progress_report')
@login_required
def progress_report():
    today = datetime.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)

    # Haftalık ve aylık tamamlanan soru/görev
    weekly_questions = Question.query.filter(
        Question.UserId == current_user.UserId,
        Question.IsCompleted == True,
        db.text("CAST([Questions].[CompletedAt] AS DATE) >= :week_ago")
    ).params(week_ago=week_ago).all()
    monthly_questions = Question.query.filter(
        Question.UserId == current_user.UserId,
        Question.IsCompleted == True,
        db.text("CAST([Questions].[CompletedAt] AS DATE) >= :month_ago")
    ).params(month_ago=month_ago).all()

    weekly_tasks = Task.query.filter(
        Task.UserId == current_user.UserId,
        Task.Status == 'completed',
        db.text("CAST([Tasks].[CompletedAt] AS DATE) >= :week_ago")
    ).params(week_ago=week_ago).all()
    monthly_tasks = Task.query.filter(
        Task.UserId == current_user.UserId,
        Task.Status == 'completed',
        db.text("CAST([Tasks].[CompletedAt] AS DATE) >= :month_ago")
    ).params(month_ago=month_ago).all()

    # Kategori bazlı dağılım (haftalık)
    categories = Category.query.all()
    category_stats = []
    for category in categories:
        count = Question.query.filter(
            Question.UserId == current_user.UserId,
            Question.IsCompleted == True,
            Question.CategoryId == category.CategoryId,
            db.text("CAST([Questions].[CompletedAt] AS DATE) >= :week_ago")
        ).params(week_ago=week_ago).count()
        category_stats.append({
            'category': category.Name,
            'count': count
        })

    # Başarı oranı (haftalık)
    total_weekly_questions = Question.query.filter(
        Question.UserId == current_user.UserId,
        db.text("CAST([Questions].[Repeat1Date] AS DATE) >= :week_ago")
    ).params(week_ago=week_ago).count()
    completed_weekly_questions = len(weekly_questions)
    success_rate = int((completed_weekly_questions / total_weekly_questions) * 100) if total_weekly_questions > 0 else 0

    # Öneri ve hedef (en az yapılan kategori)
    min_category = min(category_stats, key=lambda x: x['count']) if category_stats else None
    suggestion = None
    if min_category and min_category['count'] < 5:
        suggestion = f"Bu hafta {min_category['category']} kategorisinde daha fazla soru çözmeye çalış!"
    elif min_category:
        suggestion = f"Harika! Tüm kategorilerde iyi gidiyorsun."

    # Haftalık hedef (örnek: 10 soru)
    weekly_goal = 10
    goal_message = f"Bu hafta en az {weekly_goal} soru çöz!"

    return jsonify({
        'weekly_questions': completed_weekly_questions,
        'monthly_questions': len(monthly_questions),
        'weekly_tasks': len(weekly_tasks),
        'monthly_tasks': len(monthly_tasks),
        'success_rate': success_rate,
        'category_stats': category_stats,
        'suggestion': suggestion,
        'goal_message': goal_message
    })

@app.route('/progress')
@login_required
def progress():
    # Kullanıcının sorularını veritabanından çek
    questions = Question.query.filter_by(UserId=current_user.UserId).all()

    # Veriyi DataFrame formatına dönüştür
    data = []
    for q in questions:
        # Her tekrar tarihi için ayrı bir satır oluştur
        if q.Repeat1Date:
            data.append({'ders': q.category.Name, 'tekrar_no': 1, 'durum': 'tamamlandı' if q.RepeatCount >= 1 else 'kaçırıldı', 'date': q.Repeat1Date})
        if q.Repeat2Date:
            data.append({'ders': q.category.Name, 'tekrar_no': 2, 'durum': 'tamamlandı' if q.RepeatCount >= 2 else 'kaçırıldı', 'date': q.Repeat2Date})
        if q.Repeat3Date:
            data.append({'ders': q.category.Name, 'tekrar_no': 3, 'durum': 'tamamlandı' if q.RepeatCount >= 3 else 'kaçırıldı', 'date': q.Repeat3Date})


    df = pd.DataFrame(data)

    # Tarih sütununu datetime formatına çevir (gerekirse)
    if 'date' in df.columns:
         df['date'] = pd.to_datetime(df['date'])


    # --- İstatistikler ve Karşılaştırma Verileri ---
    today = datetime.now().date()
    week_start = today - timedelta(days=today.weekday()) # Haftanın başlangıcı (Pazartesi)
    week_ago_start = week_start - timedelta(days=7)
    month_ago_start = today.replace(day=1) # Ayın başlangıcı

    # Mevcut Hafta/Ay Verileri (DataFrame'deki tekrar tarihlerine göre)
    current_week_repeats_df = df[(df['date'].dt.date >= week_start) & (df['date'].dt.date <= today)]
    current_month_repeats_df = df[(df['date'].dt.date >= month_ago_start) & (df['date'].dt.date <= today)]

    # Tamamlanan tekrar sayıları bu hafta/ay içinde tekrar tarihi olanlardan
    current_weekly_completed_repeats_count = current_week_repeats_df[current_week_repeats_df['durum'] == 'tamamlandı'].shape[0]
    current_monthly_completed_repeats_count = current_month_repeats_df[current_month_repeats_df['durum'] == 'tamamlandı'].shape[0]

    # Haftalık/Aylık Görev Verileri (Tamamlananlar - Task modelinde CompletedAt var)
    current_weekly_completed_tasks = Task.query.filter(
        Task.UserId == current_user.UserId,
        Task.Status == 'completed',
        Task.CompletedAt >= datetime.combine(week_start, datetime.min.time()),
        Task.CompletedAt <= datetime.combine(today + timedelta(days=1), datetime.min.time()) # Bugünü de dahil et
    ).count()
    current_monthly_completed_tasks = Task.query.filter(
        Task.UserId == current_user.UserId,
        Task.Status == 'completed',
        Task.CompletedAt >= datetime.combine(month_ago_start, datetime.min.time()),
        Task.CompletedAt <= datetime.combine(today + timedelta(days=1), datetime.min.time()) # Bugünü de dahil et
    ).count()


    # Başarı Oranı (Bu hafta tekrar tarihi olan tekrarların kaçı tamamlandı?)
    total_due_this_week = current_week_repeats_df.shape[0]
    weekly_success_rate = int((current_weekly_completed_repeats_count / total_due_this_week) * 100) if total_due_this_week > 0 else 0


    # Geçmiş Hafta Verileri (DataFrame'deki tekrar tarihlerine göre)
    last_week_repeats_df = df[(df['date'].dt.date >= week_ago_start) & (df['date'].dt.date < week_start)]
    last_week_completed_repeats_count = last_week_repeats_df[last_week_repeats_df['durum'] == 'tamamlandı'].shape[0]

    # Geçmiş Haftalık Görev Verileri (Task modelinde CompletedAt var)
    last_week_completed_tasks = Task.query.filter(
        Task.UserId == current_user.UserId,
        Task.Status == 'completed',
        Task.CompletedAt >= datetime.combine(week_ago_start, datetime.min.time()),
        Task.CompletedAt < datetime.combine(week_start, datetime.min.time())
    ).count()


    # Kategori İstatistikleri (Öneri için - Sadece tamamlanan tekrar sayıları)
    category_completion_counts = df[df['durum'] == 'tamamlandı'].groupby('ders').size().to_dict()

    # En az tekrar tamamlanan kategoriyi bul (Tamamlanan tekrar sayısı en az olan)
    min_category = None
    if category_completion_counts:
        min_category_name = min(category_completion_counts, key=category_completion_counts.get)
        min_category = min_category_name
        # Eğer hiç tekrar tamamlanmadıysa genel bir mesaj ver
        if all(count == 0 for count in category_completion_counts.values()):
             suggestion = "Henüz tekrar tamamlamadınız. Başlamak için bugün tekrar edilmesi gereken sorulara göz atın!"
        else:
            suggestion = f"Bu hafta {min_category} kategorisine daha fazla odaklanmayı düşünebilirsin."
    else:
        suggestion = "Henüz hiç soru eklememiş veya tekrar yapmamışsınız. Hadi ilk sorunuzu ekleyin!"


    # Haftalık Hedef (Örnek)
    weekly_goal = 10 # Haftalık hedef tamamlanan tekrar sayısı olabilir
    goal_message = f"Bu hafta {weekly_goal} tekrar tamamlamayı hedefle!" # Hedef türünü netleştirebiliriz


    # --- Grafik Oluşturma (Mevcut kod) ---
    graph_url = None
    if not df.empty:
        # Her ders için toplam tamamlanan ve kaçırılan tekrar sayısını bul
        # Burada sadece verisi olan dersleri alalım
        ders_stats = df.groupby('ders')['durum'].value_counts().unstack(fill_value=0).dropna(axis=0, how='all')
        dersler = ders_stats.index.tolist()

        if dersler: # Eğer hiç ders istatistiği yoksa grafik çizme
            num_categories = len(dersler)
            # Calculate the number of rows needed for subplots (2 columns)
            num_rows = (num_categories + 1) // 2 # Integer division to get ceiling

            # Adjust figure size based on number of rows, minimum size for single row
            fig_height = max(5, num_rows * 5)
            fig, axs = plt.subplots(num_rows, 2, figsize=(10, fig_height))

            # If only one row, axs might not be a 2D array, flatten it safely
            if num_rows == 1 and len(dersler) == 1:
                 axs = [axs] # Make it a list to iterate
            else:
                 axs = axs.flatten()


            # Hide unused subplots if the total number of categories is odd
            for i in range(num_categories, len(axs)):
                fig.delaxes(axs[i])


            for i, ders in enumerate(dersler):
                ax = axs[i]

                # Tamamlanan ve kaçırılan sayıları al
                tamamlanan = ders_stats.loc[ders].get('tamamlandı', 0)
                kaçırılan = ders_stats.loc[ders].get('kaçırıldı', 0)

                # Sadece veri varsa daire grafiği çiz
                if tamamlanan + kaçırılan > 0:
                    labels = ['Tamamlandı', 'Kaçırıldı']
                    sizes = [tamamlanan, kaçırılan]
                    colors = ['#98D8AA', '#FFB5B5'] # Soft renkler: Açık yeşil ve soft kırmızı

                    ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=140)
                    ax.axis('equal')  # Eşit en boy oranı, dairenin çizgi değil daire olmasına sağlar.

                ax.set_title(f'{ders}') # Ders adını başlık yap
                # Eğer veri yoksa veya sıfırsa grafiğin üzerine "Veri Yok" yazabiliriz
                if tamamlanan + kaçırılan == 0:
                     ax.text(0, 0, "Veri Yok", ha='center', va='center', fontsize=12, color='gray')


            plt.suptitle('Derslere Göre Tekrar Performansı', y=1.02, fontsize=16) # Ana başlığı güncelle
            plt.tight_layout(rect=[0, 0.03, 1, 0.95])

            # Grafiği bir buffer'a kaydet
            buf = io.BytesIO()
            plt.savefig(buf, format='png')
            buf.seek(0)
            graph_url = base64.b64encode(buf.read()).decode('utf-8')
            plt.close(fig) # Figürü kapat

    # Şablonu render et ve tüm verileri gönder
    return render_template(
        'progress_report.html',
        graph_url=graph_url,
        section='takipsistemi',
        show_sidebar=True,
        # Yeni eklenen veriler
        current_weekly_questions=current_weekly_completed_repeats_count, # Tekrar sayısı olarak güncellendi
        current_monthly_questions=current_monthly_completed_repeats_count, # Tekrar sayısı olarak güncellendi
        current_weekly_tasks=current_weekly_completed_tasks,
        current_monthly_tasks=current_monthly_completed_tasks,
        weekly_success_rate=weekly_success_rate,
        suggestion=suggestion,
        goal_message=goal_message,
        last_week_completed_questions=last_week_completed_repeats_count, # Tekrar sayısı olarak güncellendi
        last_week_completed_tasks=last_week_completed_tasks
    )

@app.route('/add_task', methods=['POST'])
@login_required
def add_task():
    try:
        title = request.form.get('title')
        description = request.form.get('description')
        due_date_str = request.form.get('due_date')
        priority = request.form.get('priority')
        category = request.form.get('category')

        # Tarih formatını kontrol et ve dönüştür
        due_date = None
        if due_date_str:
            try:
                # 'YYYY-MM-DDTHH:MM' formatı için uygun dönüşüm
                due_date = datetime.strptime(due_date_str, '%Y-%m-%dT%H:%M')
            except ValueError:
                flash('Geçerli bir son tarih formatı girin.', 'error')
                return redirect(url_for('gorevlerim')) # Hata durumunda geri yönlendir

        if not title or not due_date or not priority or not category:
            flash('Lütfen tüm zorunlu alanları (Başlık, Son Tarih, Öncelik, Kategori) doldurun.', 'error')
            return redirect(url_for('gorevlerim')) # Hata durumunda geri yönlendir

        new_task = Task(
            UserId=current_user.UserId,
            Title=title,
            Description=description,
            DueDate=due_date,
            Priority=priority,
            Category=category,
            Status='new', # Yeni görev başlangıçta 'new' durumunda
            CreatedAt=datetime.utcnow()
        )

        db.session.add(new_task)
        db.session.commit()

       

    except Exception as e:
        db.session.rollback()
        flash('Görev eklenirken bir hata oluştu: ' + str(e), 'error')

    return redirect(url_for('gorevlerim'))

@app.route('/update_book_progress/<int:book_id>', methods=['POST'])
@login_required
def update_book_progress(book_id):
    try:
        book = Book.query.get_or_404(book_id)
        if book.UserId != current_user.UserId:
            flash('Bu kitabı güncelleme yetkiniz yok.', 'error')
            return redirect(url_for('kitaplarim'))

        current_page = request.form.get('current_page', type=int)

        if current_page is None or current_page < 0 or current_page > book.TotalPages:
            flash('Geçerli bir sayfa numarası girin.', 'error')
            return redirect(url_for('kitaplarim'))

        book.CurrentPage = current_page
        
        # Eğer mevcut sayfa toplam sayfaya eşitse kitabı tamamlandı olarak işaretle
        if book.CurrentPage == book.TotalPages:
            book.IsCompleted = True

        db.session.commit()
        flash('Kitap ilerlemesi güncellendi.', 'success')

    except Exception as e:
        db.session.rollback()
        flash('Kitap ilerlemesi güncellenirken bir hata oluştu: ' + str(e), 'error')

    return redirect(url_for('kitaplarim'))

@app.route('/add_quote/<int:book_id>', methods=['POST'])
@login_required
def add_quote(book_id):
    try:
        book = Book.query.get_or_404(book_id)
        if book.UserId != current_user.UserId:
            flash('Bu kitaba alıntı ekleme yetkiniz yok.', 'error')
            return redirect(url_for('kitaplarim'))

        page_number = request.form.get('page_number', type=int)
        content = request.form.get('content')

        if page_number is None or content is None:
            flash('Sayfa numarası ve alıntı içeriği gerekli.', 'error')
            return redirect(url_for('kitaplarim'))
            
        if page_number <= 0 or page_number > book.TotalPages:
             flash(f'Geçerli bir sayfa numarası girin (1 ile {book.TotalPages} arası).' , 'error')
             return redirect(url_for('kitaplarim'))

        new_quote = BookQuote(
            BookId=book_id,
            PageNumber=page_number,
            Content=content,
            CreatedAt=datetime.utcnow()
        )

        db.session.add(new_quote)
        db.session.commit()

        flash('Alıntı başarıyla eklendi.', 'success')

    except Exception as e:
        db.session.rollback()
        flash('Alıntı eklenirken bir hata oluştu: ' + str(e), 'error')

    return redirect(url_for('kitaplarim'))

@app.route('/add_book', methods=['POST'])
@login_required
def add_book():
    try:
        title = request.form.get('title')
        author = request.form.get('author')
        total_pages = request.form.get('total_pages', type=int)

        if not title or not author or total_pages is None or total_pages <= 0:
            flash('Kitap adı, yazar ve toplam sayfa sayısı gerekli.', 'error')
            return redirect(url_for('kitaplarim'))

        new_book = Book(
            UserId=current_user.UserId,
            Title=title,
            Author=author,
            CurrentPage=0,
            TotalPages=total_pages,
            StartDate=datetime.utcnow(),
            IsCompleted=False
        )

        db.session.add(new_book)
        db.session.commit()

        flash('Kitap başarıyla eklendi!', 'success')

    except Exception as e:
        db.session.rollback()
        flash('Kitap eklenirken bir hata oluştu: ' + str(e), 'error')

    return redirect(url_for('kitaplarim'))

@app.route('/edit_task/<int:task_id>', methods=['GET', 'POST'])
@login_required
def edit_task(task_id):
    task = Task.query.filter_by(TaskId=task_id, UserId=current_user.UserId).first()
    if not task:
        flash('Görev bulunamadı veya yetkiniz yok.', 'error')
        return redirect(url_for('gorevlerim'))
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        due_date_str = request.form.get('due_date')
        priority = request.form.get('priority')
        category = request.form.get('category')
        try:
            if due_date_str:
                task.DueDate = datetime.strptime(due_date_str, '%Y-%m-%dT%H:%M')
            task.Title = title
            task.Description = description
            task.Priority = priority
            task.Category = category
            db.session.commit()
            flash('Görev başarıyla güncellendi!', 'success')
            return redirect(url_for('gorevlerim'))
        except Exception as e:
            db.session.rollback()
            flash('Güncelleme sırasında hata oluştu: ' + str(e), 'error')
    return render_template('edit_task.html', task=task)

@app.route('/delete_task', methods=['POST'])
@login_required
def delete_task():
    import json
    data = request.get_json()
    task_id = data.get('task_id')
    if not task_id:
        return jsonify({'success': False, 'error': 'Görev ID eksik'}), 400
    task = Task.query.filter_by(TaskId=task_id, UserId=current_user.UserId).first()
    if not task:
        return jsonify({'success': False, 'error': 'Görev bulunamadı veya yetkiniz yok'}), 404
    try:
        db.session.delete(task)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/get_task/<int:task_id>')
@login_required
def get_task(task_id):
    task = Task.query.filter_by(TaskId=task_id, UserId=current_user.UserId).first()
    if not task:
        return jsonify({'success': False, 'error': 'Görev bulunamadı'}), 404
    return jsonify({
        'TaskId': task.TaskId,
        'Title': task.Title,
        'Description': task.Description,
        'DueDate': task.DueDate.strftime('%Y-%m-%dT%H:%M') if task.DueDate else '',
        'Priority': task.Priority,
        'Category': task.Category
    })

@app.route('/edit_task_modal', methods=['POST'])
@login_required
def edit_task_modal():
    task_id = request.form.get('task_id')
    title = request.form.get('title')
    description = request.form.get('description')
    due_date_str = request.form.get('due_date')
    priority = request.form.get('priority')
    category = request.form.get('category')
    task = Task.query.filter_by(TaskId=task_id, UserId=current_user.UserId).first()
    if not task:
        return jsonify({'success': False, 'error': 'Görev bulunamadı'}), 404
    try:
        if due_date_str:
            task.DueDate = datetime.strptime(due_date_str, '%Y-%m-%dT%H:%M')
        task.Title = title
        task.Description = description
        task.Priority = priority
        task.Category = category
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/complete_task/<int:task_id>', methods=['POST'])
@login_required
def complete_task(task_id):
    task = Task.query.filter_by(TaskId=task_id, UserId=current_user.UserId).first()
    if not task:
        return jsonify({'success': False, 'error': 'Görev bulunamadı'}), 404
    try:
        task.Status = 'completed'
        task.CompletedAt = datetime.utcnow()
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/update_repeat_count/<int:question_id>', methods=['POST'])
@login_required
def update_repeat_count(question_id):
    question = Question.query.get_or_404(question_id)
    if question.UserId != current_user.UserId:
        return jsonify({'success': False, 'error': 'Bu işlem için yetkiniz yok'}), 403

    today = datetime.now().date()
    # Bugünkü tekrar zaten yapılmış mı kontrolü
    if question.RepeatCount == 0 and question.Repeat1Date and question.Repeat1Date.date() == today:
        if question.RepeatCount > 0:
            return jsonify({'success': False, 'error': 'Bugünkü tekrar zaten tamamlandı.'})
    elif question.RepeatCount == 1 and question.Repeat2Date and question.Repeat2Date.date() == today:
        if question.RepeatCount > 1:
            return jsonify({'success': False, 'error': 'Bugünkü tekrar zaten tamamlandı.'})
    elif question.RepeatCount == 2 and question.Repeat3Date and question.Repeat3Date.date() == today:
        if question.RepeatCount > 2:
            return jsonify({'success': False, 'error': 'Bugünkü tekrar zaten tamamlandı.'})

    updated_dates = {
        'repeat1': question.Repeat1Date.strftime('%d.%m.%Y') if question.Repeat1Date else 'Belirlenmedi',
        'repeat2': question.Repeat2Date.strftime('%d.%m.%Y') if question.Repeat2Date else 'Belirlenmedi',
        'repeat3': question.Repeat3Date.strftime('%d.%m.%Y') if question.Repeat3Date else 'Belirlenmedi',
    }

    if question.RepeatCount == 0:
        question.RepeatCount = 1
    elif question.RepeatCount == 1:
        question.RepeatCount = 2
    elif question.RepeatCount == 2:
        question.RepeatCount = 3
        question.IsCompleted = True
    else:
        return jsonify({'success': False, 'error': 'Zaten tamamlandı.'})

    db.session.commit()

    return jsonify({
        'success': True,
        'repeat_count': question.RepeatCount,
        'is_completed': question.IsCompleted,
        'updated_repeat_dates': updated_dates
    })

@app.context_processor
def inject_notifications():
    if current_user.is_authenticated:
        today = datetime.now().date()
        yesterday = datetime.now() - timedelta(days=1)
        notifications = []

        # Bugünün soruları bildirimi
        today_questions_count = Question.query.filter(
            Question.UserId == current_user.UserId,
            Question.IsCompleted == False,
            Question.IsHidden == False,
            (
                (Question.Repeat1Date != None) & (db.func.cast(Question.Repeat1Date, db.Date) == today)
                |
                (Question.Repeat2Date != None) & (db.func.cast(Question.Repeat2Date, db.Date) == today)
                |
                (Question.Repeat3Date != None) & (db.func.cast(Question.Repeat3Date, db.Date) == today)
            )
        ).count()
        if today_questions_count > 0:
            notifications.append({
                'icon': 'fas fa-clock',
                'color_class': 'blue',
                'type': 'Bugünün Soruları',
                'msg': f'{today_questions_count} soru çözülmeyi bekliyor',
                'timestamp': None,
            })

        # Son 24 saatte tamamlanan görev bildirimi
        completed_tasks_last_24h = Task.query.filter(
            Task.UserId == current_user.UserId,
            Task.Status == 'completed',
            Task.CompletedAt >= yesterday
        ).count()
        if completed_tasks_last_24h > 0:
            notifications.append({
                'icon': 'fas fa-check-circle',
                'color_class': 'green',
                'type': 'Görev Tamamlandı',
                'msg': f'Son 24 saatte tamamlanan {completed_tasks_last_24h} görev',
                'timestamp': None,
            })

        # Okunan kitap bildirimi
        books_count = Book.query.filter_by(
            UserId=current_user.UserId
        ).count()
        # if books_count > 0:
        #     notifications.append({
        #         'icon': 'fas fa-book',
        #         'color_class': 'purple',
        #         'type': 'Kitap',
        #         'msg': f'{books_count} kitap okuyorsun!',
        #         'timestamp': None,
        #     })

        # Motivasyon mesajı
        motivation_messages = [
            "Başarı, küçük adımların toplamıdır!",
            "Her gün bir adım daha ileriye!",
            "Zorlandığında vazgeçme, mola ver ve devam et!",
            "Küçük adımlar büyük başarılar getirir!",
            "Bugün dünden daha iyi ol!",
            "Başarı yolunda ilerliyorsun!",
            "Kendine inan, başarabilirsin!",
            "Her tekrar seni hedefe yaklaştırır!"
        ]
        import random
        motivation_message = random.choice(motivation_messages)
        notifications.append({
            'icon': 'fas fa-lightbulb',
            'color_class': 'yellow',
            'type': 'Motivasyon',
            'msg': motivation_message,
            'timestamp': None,
        })

        notification_count = len(notifications)
        daily_summary = None
        return dict(notifications=notifications, notification_count=notification_count, daily_summary=daily_summary)
    return dict(notifications=[], notification_count=0, daily_summary=None)

@app.route('/next_question/<int:current_id>')
@login_required
def next_question(current_id):
    source = request.args.get('source', 'today')
    category_id_str = request.args.get('category_id')
    category_id = None
    if category_id_str and category_id_str.isdigit():
        category_id = int(category_id_str)

    user_id = current_user.UserId
    today = datetime.now().date()

    if source == 'past':
        questions = Question.query.filter(
            Question.UserId == user_id,
            Question.IsCompleted == False,
            Question.RepeatCount < 3,
            Question.QuestionId != current_id
        ).all()
        def get_active_repeat_date(q):
            if q.RepeatCount == 0:
                return q.Repeat1Date.date() if q.Repeat1Date else None
            elif q.RepeatCount == 1:
                return q.Repeat2Date.date() if q.Repeat2Date else None
            elif q.RepeatCount == 2:
                return q.Repeat3Date.date() if q.Repeat3Date else None
            return None
        filtered = []
        for q in questions:
            ard = get_active_repeat_date(q)
            if ard and ard < today:
                filtered.append(q)
        filtered.sort(key=get_active_repeat_date, reverse=True)
        next_question = filtered[0] if filtered else None
    elif source == 'kategori' and category_id:
        # Önce mevcut sorudan sonraki ilk soruyu bul
        next_question = Question.query.filter(
            Question.UserId == user_id,
            Question.CategoryId == category_id,
            Question.QuestionId > current_id
        ).order_by(Question.QuestionId).first()
        if not next_question:
            # Yoksa en küçük QuestionId'li soruya dön
            next_question = Question.query.filter(
                Question.UserId == user_id,
                Question.CategoryId == category_id
            ).order_by(Question.QuestionId).first()
    else:
        # Bugünün soruları
        query = Question.query.filter(
            Question.UserId == user_id,
            Question.IsCompleted == False,
            Question.IsHidden == False,
            (
                (Question.RepeatCount == 0) & (db.func.cast(Question.Repeat1Date, db.Date) == today)
                |
                (Question.RepeatCount == 1) & (db.func.cast(Question.Repeat2Date, db.Date) == today)
                |
                (Question.RepeatCount == 2) & (db.func.cast(Question.Repeat3Date, db.Date) == today)
            ),
            Question.QuestionId != current_id
        ).order_by(Question.Repeat1Date)
        next_question = query.first()

    if next_question:
        return jsonify({'next_id': next_question.QuestionId})
    else:
        return jsonify({'next_id': None})

if __name__ == '__main__':
    app.run(debug=True)
