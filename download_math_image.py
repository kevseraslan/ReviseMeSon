import os
import base64
import requests
from io import BytesIO
from PIL import Image

# Görseli indireceğimiz klasörü kontrol edelim
image_dir = "static/images"
if not os.path.exists(image_dir):
    os.makedirs(image_dir)

# Matematik görseli URL'si (paylaşılan görsele benzer bir matematik görseli)
image_url = "https://img.freepik.com/free-vector/hand-drawn-math-elements_23-2147492795.jpg?w=600&t=st=1716748847~exp=1716749447~hmac=8b1a7e3a9b3c3e3a9b3c3e3a9b3c3e3a9b3c3e3a9b3c3e3a9b3c3e3a9b3c3e3a"

try:
    response = requests.get(image_url)
    response.raise_for_status()
    
    # Görseli kaydet
    with open(os.path.join(image_dir, "math_image.jpg"), 'wb') as file:
        file.write(response.content)
    
    print("Matematik görseli başarıyla indirildi!")
except Exception as e:
    print(f"Görsel indirilirken hata oluştu: {e}")
