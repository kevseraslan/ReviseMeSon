# ReviseMe - Planlayıcı Sistemi Sidebar Yeniden Tasarımı ve Entegrasyonu PRD'si

**Sürüm:** 1.0
**Tarih:** 24 Ekim 2023

## 1. Giriş

Bu doküman, ReviseMe uygulamasının "Planlayıcı Sistemi" bölümündeki mevcut sabit kenar çubuğu (sidebar) yapısının, "Tekrar Sistemi" bölümünde kullanılan açılır/kapanır (hamburger menü kontrollü) sidebar mekanizması ve görsel stiliyle değiştirilmesi için gereksinimleri ve yol haritasını tanımlar. Amaç, uygulama genelinde tutarlı bir kullanıcı deneyimi sağlamak, ekran alanını daha verimli kullanmak ve modern bir görünüm elde etmektir. Bu değişiklik, "Planlayıcı Sistemi" içindeki tüm sekmeler için geçerli olacaktır ve mevcut işlevsellikleri koruyacaktır.

## 2. Mevcut Durum

*   **Tekrar Sistemi (Model Davranış):**
    *   Sidebar, bir hamburger menü ikonu ile açılıp kapanabilir.
    *   **Açık Durum (1. Fotoğraf):** Sidebar geniştir, ikonların yanında metin etiketleri ("Ana Sayfa", "Bildirimler" vb.) görünür. Ana içerik alanı, sidebar'ın genişliğine göre daralır.
    *   **Kapalı Durum (2. Fotoğraf):** Sidebar ya tamamen gizlenir ya da sadece ikonları gösterecek şekilde daralır (fotoğrafta tamamen gizlenmiş ve içerik alanı tam genişlikte görünüyor). Ana içerik alanı, sidebar'ın kapalı durumuna göre genişler.
    *   Sidebar'ın üstünde "Planlayıcıya Geç" gibi bir geçiş butonu bulunur.
    *   Görsel stil: Koyu arka plan, açık renkli metin ve ikonlar, aktif sekme için vurgu.

*   **Planlayıcı Sistemi (Değiştirilecek Bölüm - 3. Fotoğraf):**
    *   Sidebar sabittir ve her zaman açıktır.
    *   İkonların yanında metin etiketleri ("Kitaplarım", "Görevlerim" vb.) görünür.
    *   Sidebar'ın üstünde "Tekrar Sistemine Geç" butonu bulunur.
    *   Görsel stil: Koyu arka plan, açık renkli metin ve ikonlar.
    *   Ana içerik alanı, sidebar'ın varlığına göre sabit bir genişliktedir.

## 3. Hedeflenen Durum (Planlayıcı Sistemi için)

"Planlayıcı Sistemi", "Tekrar Sistemi" ile aynı sidebar davranışına ve görsel stiline sahip olacaktır:

*   **Sidebar Mekanizması:**
    *   Bir hamburger menü ikonu (muhtemelen sol üst köşede veya ana başlık çubuğunda) ile açılıp kapanabilir olacaktır.
    *   **Açık Durum:** Sidebar, "Tekrar Sistemi"ndeki gibi geniş olacak, ikonların yanında "Planlayıcı Sistemi"ne ait metin etiketleri ("Kitaplarım", "Görevlerim", "Listening", "Günlük Raporu Gör") görünecektir. "Tekrar Sistemine Geç" butonu mevcut konumunda (veya stil uyumuyla) kalacaktır. Ana içerik alanı buna göre daralacaktır.
    *   **Kapalı Durum:** Sidebar, "Tekrar Sistemi"ndeki gibi ya tamamen gizlenecek ya da sadece ikonları gösterecek şekilde daralacak. Ana içerik alanı tam genişliğe veya sidebar'ın dar durumuna göre genişleyecektir.
*   **Görsel Stil:**
    *   Sidebar'ın arka plan rengi, metin renkleri, ikon stilleri ve aktif sekme vurgusu "Tekrar Sistemi" ile birebir aynı olacaktır.
    *   Ana içerik alanının mevcut görsel stili (arka plan, renkler vb.) korunacaktır; değişiklik sadece sidebar ve içerik alanının sidebar durumuna göre genişlemesi/daralması ile ilgilidir.
*   **İşlevsellik:**
    *   "Planlayıcı Sistemi" içindeki tüm sekmeler ("Kitaplarım", "Görevlerim" vb.) mevcut işlevlerini eksiksiz olarak yerine getirmeye devam edecektir. Sekmelere tıklandığında ilgili içerik doğru şekilde yüklenecektir.
    *   "Tekrar Sistemine Geç" butonu işlevsel kalacaktır.

## 4. Kapsam

Bu değişiklikler, "Planlayıcı Sistemi" bölümünün ana düzenini (layout) etkileyecek ve bu bölüm altındaki **tüm mevcut ve gelecekte eklenecek sekmeler** için geçerli olacaktır.

## 5. Yapılacaklar (Teknik Detaylar)

### 5.1. Sidebar Bileşeni ve Mekanizması (Planlayıcı Sistemi için)
*   **[x] Hamburger Menü İkonu Entegrasyonu:** "Planlayıcı Sistemi" ana görünümüne hamburger menü ikonu eklenecek.
*   **[x] Sidebar Durum Yönetimi:** Sidebar'ın açık/kapalı durumunu yönetecek bir state (React, Vue, Angular state veya vanilla JS ile) mekanizması implemente edilecek.
*   **[x] Açılır/Kapanır Animasyon:** Sidebar'ın açılıp kapanması sırasında pürüzsüz bir geçiş animasyonu eklenecek (isteğe bağlı ama önerilir).
*   **[x] Koşullu Görüntüleme:**
    *   **Açık Durum:** İkonlar ve metin etiketleri birlikte gösterilecek.
    *   **Kapalı Durum:** Sadece ikonlar gösterilecek veya sidebar tamamen gizlenecek (bu karara göre stil ayarlanacak).

### 5.2. İçerik Alanı Düzenlemesi
*   **[x] Dinamik Genişlik/Kenar Boşluğu:** Ana içerik alanının CSS'i, sidebar'ın açık/kapalı durumuna göre `width` veya `margin-left` değerlerini dinamik olarak değiştirecek şekilde güncellenecek.
*   **[x] İçerik Kayması Önleme:** Sidebar durumu değiştiğinde içerik alanındaki elemanların istenmeyen şekilde kayması veya bozulması engellenecek.

### 5.3. Stil ve Tema Uyumu
*   **[x] CSS Stillerinin Aktarılması/Uyarlanması:** "Tekrar Sistemi" sidebar'ında kullanılan CSS sınıfları ve stilleri (renkler, fontlar, boşluklar, aktif sekme vurgusu) "Planlayıcı Sistemi" sidebar'ına uygulanacak.
*   **[x] İkon ve Metin Hizalaması:** Açık ve (eğer varsa) kapalı durumda ikonların ve metinlerin doğru hizalanması sağlanacak.
*   **[x] "Tekrar Sistemine Geç" Buton Stili:** Bu butonun da genel sidebar stiliyle uyumlu olması sağlanacak.

### 5.4. Tüm Sekmelere Uygulama
*   **[x] Ana Layout Entegrasyonu:** Yeni sidebar yapısı, "Planlayıcı Sistemi"nin ana layout bileşenine entegre edilecek, böylece tüm alt sekmeler bu yapıdan otomatik olarak faydalanacak.
*   **[x] Sekme Bağlantılarının Korunması:** Sidebar'daki her bir linkin ("Kitaplarım", "Görevlerim" vb.) doğru sayfaya/bileşene yönlendirdiğinden emin olunacak.

### 5.5. İşlevsellik ve Test
*   **[x] Mevcut İşlevsellik Kontrolü:** "Planlayıcı Sistemi" altındaki her bir sekmenin kendi özel işlevlerinin (veri listeleme, form gönderme, rapor görüntüleme vb.) sidebar değişikliğinden sonra da sorunsuz çalıştığı test edilecek.
*   **[x] Çapraz Tarayıcı ve Cihaz Uyumluluğu:** Yeni sidebar mekanizmasının farklı tarayıcılarda ve ekran boyutlarında (özellikle mobil ve tablet için duyarlı tasarım) doğru çalıştığı kontrol edilecek.

## 6. Prompter (Tasarım ve Geliştirme İpuçları)

*   **Bileşen Yeniden Kullanımı:** Eğer "Tekrar Sistemi"ndeki sidebar bir bileşen (component) olarak geliştirildiyse, bu bileşeni "Planlayıcı Sistemi" için de kullanılabilir hale getirmek (prop'lar aracılığıyla içerik ve başlıkları değiştirerek) en verimli yol olacaktır.
*   **CSS Değişkenleri (Variables):** Uygulama genelinde renkler, boşluklar gibi stil değerleri için CSS değişkenleri kullanılıyorsa, tutarlılığı sağlamak daha kolay olacaktır.
*   **Global State Yönetimi:** Sidebar'ın açık/kapalı durumu, eğer uygulamanın farklı yerlerinden de etkileniyorsa veya bilinmesi gerekiyorsa global bir state yönetim aracı (Redux, Vuex, Context API vb.) ile yönetilebilir.
*   **Kademeli Uygulama:** Önce bir sekme için prototip oluşturulup test edilebilir, ardından tüm sisteme yayılabilir.

## 7. Başarı Metrikleri

*   "Planlayıcı Sistemi" sidebar'ının, "Tekrar Sistemi" sidebar'ı ile görsel ve davranışsal olarak %100 tutarlı olması.
*   Tüm "Planlayıcı Sistemi" sekmelerinin mevcut işlevlerini sorunsuz bir şekilde yerine getirmesi.
*   Kullanıcı geri bildirimlerinde, uygulama genelindeki tutarlılık ve kullanım kolaylığı hakkında olumlu yorumlar.
*   Farklı ekran çözünürlüklerinde ve cihazlarda bozulma olmadan çalışması.