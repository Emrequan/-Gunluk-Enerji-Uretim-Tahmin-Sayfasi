# Weather & Excel Report Web Application

## Proje Hakkında

Bu proje, **Python** ve **Django** kullanılarak geliştirilmiş, iki ana işlevi olan bir web uygulamasıdır:

1. **Hava Durumu Tahmini:**  
   Kullanıcılar, istedikleri bir şehir için güncel ve 4 günlük hava durumu tahminlerini web arayüzü üzerinden görüntüleyebilirler. Tahminler, OpenWeatherMap API’si kullanılarak alınır ve sıcaklık, hava durumu açıklaması, simgeler gibi bilgilerle birlikte sunulur.

2. **Gmail’den Gelen Excel Raporlarının Gösterimi:**  
   Uygulama, Google’ın Gmail API’si ile entegre çalışır. Kullanıcı, kendi Gmail hesabı ile uygulamaya yetki verdiğinde, gelen kutusundaki Excel ekli e-postalar otomatik olarak tespit edilir, ekler indirilir ve pandas kütüphanesi ile işlenir. Sonuçlar, web arayüzünde tablo halinde kullanıcıya sunulur.

## Temel Özellikler

- **Kullanıcı dostu arayüz:** Modern ve anlaşılır bir web arayüzü ile hem hava durumu hem de Excel raporları kolayca görüntülenebilir.
- **Dinamik şehir seçimi:** Hava durumu tahmini için şehir seçimi yapılabilir.
- **Gmail entegrasyonu:** Google OAuth ile güvenli giriş ve otomatik e-posta ekinden veri çekme.
- **Excel dosyası işleme:** pandas ile Excel dosyalarını okuma ve tabloya dönüştürme.
- **Linux ve Windows uyumluluğu:** Proje platformdan bağımsız olarak çalışır.

## Kullanılan Teknolojiler ve Kütüphaneler

- Python
- Django
- requests
- pandas
- google-auth, google-auth-oauthlib, google-api-python-client
- Bootstrap (arayüz için)

## Kurulum ve Çalıştırma

1. **Depoyu klonlayın:**
   ```bash
   git clone https://github.com/kullaniciadi/proje-adi.git
   cd proje-adi
   ```

2. **Gerekli kütüphaneleri yükleyin:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Gizli bilgileri ayarlayın:**
   - Proje köküne bir `.env` dosyası oluşturun ve aşağıdaki gibi doldurun:
     ```
     EMAIL_HOST_USER=your_email@gmail.com
     EMAIL_HOST_PASSWORD=your_app_password
     ```
   - Google API için [Google Cloud Console](https://console.cloud.google.com/) üzerinden bir OAuth istemcisi oluşturun ve `credentials.json` dosyasını proje köküne ekleyin.
   - `.env`, `credentials.json` ve `token.pickle` dosyalarını `.gitignore` dosyasına ekleyin.

4. **Veritabanını oluşturun:**
   ```bash
   python manage.py migrate
   ```

5. **Geliştirme sunucusunu başlatın:**
   ```bash
   python manage.py runserver
   ```

6. **Web arayüzüne erişin:**
   - Hava durumu ve Excel raporlarını görüntülemek için tarayıcınızda `http://localhost:8000/` adresine gidin.

## Güvenlik Notu

- **Gizli bilgileri (şifre, API anahtarı, credentials.json) asla repoya yüklemeyin!**
- `.env`, `credentials.json` ve `token.pickle` dosyalarını `.gitignore` ile hariç tutun.

## Katkı ve Lisans

- Katkıda bulunmak için lütfen bir pull request gönderin.
- Lisans bilgisi için LICENSE dosyasına bakınız. 