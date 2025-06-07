from app import app, db
from models import Category

# Uygulama bağlamı içinde çalıştır
with app.app_context():
    # İngilizce kategorisini bul
    english_category = Category.query.filter_by(Name='İngilizce').first()
    
    if english_category:
        # Kategoriyi sil
        db.session.delete(english_category)
        db.session.commit()
        print("İngilizce kategorisi başarıyla silindi.")
    else:
        print("İngilizce kategorisi bulunamadı.")
