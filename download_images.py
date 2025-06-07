import os
import requests

# Görselleri indireceğimiz klasörü kontrol edelim
image_dir = "static/images"
if not os.path.exists(image_dir):
    os.makedirs(image_dir)

# Her kategori için görsel URL'leri
image_urls = {
    "math": "https://images.unsplash.com/photo-1509228468518-180dd4864904?ixlib=rb-4.0.3&q=80&fm=jpg&crop=entropy&cs=tinysrgb&w=600&h=600&fit=crop",
    "physics": "https://images.unsplash.com/photo-1636466497217-26a8cbeaf0aa?ixlib=rb-4.0.3&q=80&fm=jpg&crop=entropy&cs=tinysrgb&w=600&h=600&fit=crop",
    "chemistry": "https://images.unsplash.com/photo-1603126857599-f6e157fa2fe6?ixlib=rb-4.0.3&q=80&fm=jpg&crop=entropy&cs=tinysrgb&w=600&h=600&fit=crop",
    "biology": "https://images.unsplash.com/photo-1530026405186-ed1f139313f8?ixlib=rb-4.0.3&q=80&fm=jpg&crop=entropy&cs=tinysrgb&w=600&h=600&fit=crop",
    "history": "https://images.unsplash.com/photo-1461360370896-922624d12aa1?ixlib=rb-4.0.3&q=80&fm=jpg&crop=entropy&cs=tinysrgb&w=600&h=600&fit=crop",
    "geography": "https://images.unsplash.com/photo-1589519160732-576f165b9aad?ixlib=rb-4.0.3&q=80&fm=jpg&crop=entropy&cs=tinysrgb&w=600&h=600&fit=crop",
    "literature": "https://images.unsplash.com/photo-1457369804613-52c61a468e7d?ixlib=rb-4.0.3&q=80&fm=jpg&crop=entropy&cs=tinysrgb&w=600&h=600&fit=crop"
}

# Görselleri indir
for image_name, url in image_urls.items():
    file_path = os.path.join(image_dir, f"{image_name}.jpg")
    
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()  # Hata kontrolü
        
        with open(file_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        
        print(f"{image_name}.jpg başarıyla indirildi.")
    except Exception as e:
        print(f"{image_name}.jpg indirilirken hata oluştu: {e}")

print("Tüm görseller indirildi!")
