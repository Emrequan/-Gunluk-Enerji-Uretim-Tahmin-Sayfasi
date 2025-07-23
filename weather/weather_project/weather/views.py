import requests
import pandas as pd
import os
import pickle
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import base64
import tempfile
from django.shortcuts import render
from django.http import HttpResponse
from django.contrib import messages
import shutil

# Create your views here.

def index(request):
    city = request.GET.get('city', 'Isparta')  # Varsayılan şehir: Isparta
    api_key = '258fd9b2512fc1ce081e987ccba838f7'
    url = f'http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={api_key}&units=metric'

    try:
        response = requests.get(url)
        weather_data = response.json()

        if response.status_code == 200:
            # 4 günlük tahmin verilerini işleyin
            forecasts = []
            for forecast in weather_data.get('list', []):
                forecasts.append({
                    'date': forecast.get('dt_txt'),
                    'temperature': forecast.get('main', {}).get('temp', 'N/A'),
                    'description': forecast.get('weather', [{}])[0].get('description', 'No description'),
                    'icon': forecast.get('weather', [{}])[0].get('icon', '01d')  # Varsayılan icon
                })
                # 4 günün tahmini (24 saat x 4 gün = 16 tahmin)
                if len(forecasts) >= 16:
                    break
            
            context = {
                'city': city,
                'forecasts': forecasts
            }
        else:
            context = {
                'city': city,
                'forecasts': [],
                'error': 'Hava durumu verisi alınamadı.'
            }
    except Exception as e:
        context = {
            'city': city,
            'forecasts': [],
            'error': str(e)
        }

    return render(request, 'weather/index.html', context)

def show_excel(request):
    # Üretim tahmini verileriyle şablonu render et
    table = ...  # Burada tahmini üretim tablonuzu oluşturun
    return render(request, 'show_excel_data.html', {'data': data})

# Gmail API için gerekli sabitler
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
CREDENTIALS_FILE = 'credentials.json'
TOKEN_FILE = 'token.pickle'

def get_gmail_service():
    creds = None
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    credentials_path = os.path.join(base_dir, 'credentials.json')
    token_path = os.path.join(base_dir, 'token.pickle')
    
    if not os.path.exists(credentials_path):
        raise Exception("credentials.json dosyası bulunamadı. Lütfen Google Cloud Console'dan indirdiğiniz dosyayı projenin kök dizinine yerleştirin.")
    
    # Token dosyası varsa oku
    if os.path.exists(token_path):
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)
    
    # Credentials geçerli değilse veya yoksa yenile/oluştur
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Token'ı kaydet
        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)
    
    return build('gmail', 'v1', credentials=creds)

def get_latest_excel_from_gmail():
    try:
        service = get_gmail_service()
        print("Gmail servisi başarıyla oluşturuldu.")
        
        # Son 24 saat içindeki e-postaları ara
        time_24h_ago = (datetime.now() - timedelta(days=1)).strftime('%Y/%m/%d')
        query = f'after:{time_24h_ago} has:attachment filename:xls OR filename:xlsx'
        print(f"Arama sorgusu: {query}")
        
        # E-postaları listele
        results = service.users().messages().list(userId='me', q=query).execute()
        messages = results.get('messages', [])
        print(f"Bulunan e-posta sayısı: {len(messages)}")
        
        if not messages:
            print("Son 24 saat içinde Excel eki olan e-posta bulunamadı.")
            return None
            
        # En son e-postayı al
        msg = service.users().messages().get(userId='me', id=messages[0]['id'], format='full').execute()
        print("En son e-posta alındı.")
        
        if 'payload' not in msg:
            print("E-postada payload bulunamadı.")
            return None
            
        parts = msg['payload'].get('parts', [])
        if not parts:
            print("E-postada parts bulunamadı.")
            return None
            
        for part in parts:
            filename = part.get('filename', '')
            if filename.lower().endswith(('.xls', '.xlsx')):
                print(f"Excel dosyası bulundu: {filename}")
                if 'body' in part and 'attachmentId' in part['body']:
                    attachment = service.users().messages().attachments().get(
                        userId='me',
                        messageId=messages[0]['id'],
                        id=part['body']['attachmentId']
                    ).execute()
                    
                    # Eki geçici dosyaya kaydet
                    file_data = base64.urlsafe_b64decode(attachment['data'])
                    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.' + filename.split('.')[-1])
                    temp_file.write(file_data)
                    temp_file.close()
                    print(f"Dosya geçici konuma kaydedildi: {temp_file.name}")
                    return temp_file.name
                else:
                    print("Attachment ID bulunamadı.")
                    
        print("Uygun Excel eki bulunamadı.")
        return None
        
    except Exception as e:
        print(f"Gmail'den dosya alınırken hata oluştu: {str(e)}")
        return None

def show_excel_data(request):
    if request.method == 'POST':
        if 'excel_file' in request.FILES:
            excel_file = request.FILES['excel_file']
            try:
                # Excel dosyasını oku
                df = pd.read_excel(excel_file, header=None)
                print("Excel dosyası başarıyla okundu.")
                print(f"Toplam satır sayısı: {len(df)}")
                print(f"Toplam sütun sayısı: {len(df.columns)}")
                
                # Veriyi hazırla
                data = {}
                
                # Saatleri hazırla
                hours = []
                for i in range(24):
                    hours.append(f"{i:02d}:00-{(i+1):02d}:00")
                data['hours'] = hours

                # Bugünün tarihini al
                today = datetime.now().date()
                print(f"Bugünün tarihi: {today}")

                # Sabit başlangıç pozisyonları
                start_row = 4  # 5. satırdan başla (0-based index)
                target_col = 25  # 26. sütun (üretim değerleri)
                date_col = 1  # 2. sütun (tarih)

                # Her gün için verileri oku
                for day in range(7):
                    current_date = today + timedelta(days=day)
                    data[f'tarih{day + 1}'] = current_date.strftime('%d-%m-%Y')
                    print(f"\nİşlenen tarih: {current_date.strftime('%d-%m-%Y')}")

                    # Excel'deki tarihi bul - Tüm satırları tara
                    found_row = None
                    print(f"Excel'de tarih aranıyor: {current_date}")
                    
                    # Önce tüm tarihleri listele
                    print("Excel'deki tüm tarihler:")
                    for row in range(start_row, min(start_row + 200, len(df))):  # İlk 200 satırı kontrol et
                        try:
                            excel_date = df.iloc[row, date_col]
                            if pd.notnull(excel_date):
                                if isinstance(excel_date, str):
                                    excel_date = pd.to_datetime(excel_date).date()
                                elif isinstance(excel_date, (pd.Timestamp, datetime)):
                                    excel_date = excel_date.date()
                                print(f"Satır {row}: {excel_date}")
                        except Exception as e:
                            continue
                    
                    # Şimdi tarihi ara
                    for row in range(start_row, len(df)):
                        try:
                            excel_date = df.iloc[row, date_col]
                            if pd.notnull(excel_date):
                                if isinstance(excel_date, str):
                                    excel_date = pd.to_datetime(excel_date).date()
                                elif isinstance(excel_date, (pd.Timestamp, datetime)):
                                    excel_date = excel_date.date()
                                
                                print(f"Kontrol edilen satır {row}: Excel tarihi = {excel_date}, Aranan tarih = {current_date}")
                                if excel_date == current_date:
                                    found_row = row
                                    print(f"Eşleşme bulundu! Satır: {found_row}")
                                    break
                        except Exception as e:
                            print(f"Satır {row} tarih okuma hatası: {str(e)}")
                            continue

                    # Bu gün için saatlik verileri al
                    for hour in range(24):
                        cell_index = (day * 24) + hour + 1
                        
                        if found_row is not None:
                            try:
                                value = df.iloc[found_row + hour, target_col]
                                print(f"Saat {hour:02d}:00 - Okunan değer: {value}")
                                
                                if pd.notnull(value):
                                    try:
                                        value = float(str(value).strip().replace(',', '.')) / 1000  # Convert to MWh
                                        print(f"Dönüştürülen değer (MWh): {value}")
                                        
                                        # Renk sınıfını belirle (MWh değerlerine göre)
                                        if value < 10:  # 10 MWh altı
                                            color_class = 'very-low'
                                        elif 10 <= value < 25:  # 10-25 MWh
                                            color_class = 'low'
                                        elif 25 <= value < 40:  # 25-40 MWh
                                            color_class = 'medium'
                                        elif 40 <= value < 60:  # 40-60 MWh
                                            color_class = 'high'
                                        else:  # 60 MWh üstü
                                            color_class = 'very-high'

                                        data[f'cell_m{cell_index}'] = {
                                            'value': f"{value:.2f}",
                                            'color_class': color_class
                                        }
                                        print(f"Hücre {cell_index} için değer kaydedildi")
                                    except ValueError as e:
                                        print(f"Değer dönüştürme hatası: {str(e)}")
                                        data[f'cell_m{cell_index}'] = {
                                            'value': '-',
                                            'color_class': 'no-data'
                                        }
                                else:
                                    print(f"Boş değer")
                                    data[f'cell_m{cell_index}'] = {
                                        'value': '-',
                                        'color_class': 'no-data'
                                    }
                            except Exception as e:
                                print(f"Veri okuma hatası: {str(e)}")
                                data[f'cell_m{cell_index}'] = {
                                    'value': '-',
                                    'color_class': 'no-data'
                                }
                        else:
                            print(f"Bu tarih için veri bulunamadı")
                            data[f'cell_m{cell_index}'] = {
                                'value': '-',
                                'color_class': 'no-data'
                            }

                print("\nTemplate'e gönderilen veri yapısı:")
                print("Tarihler:")
                for i in range(1, 8):
                    print(f"tarih{i}: {data.get(f'tarih{i}')}")
                print("\nÖrnek hücre değerleri:")
                for i in range(1, 25):  # İlk günün verilerini göster
                    cell_key = f'cell_m{i}'
                    if cell_key in data:
                        print(f"{cell_key}: {data[cell_key]}")

                messages.success(request, 'Veriler başarıyla yüklendi.')
                return render(request, 'weather/show_excel_data.html', {'data': data})
            except Exception as e:
                print(f"Genel hata: {str(e)}")
                messages.error(request, f'Dosya okuma hatası: {str(e)}')
        else:
            messages.warning(request, 'Lütfen bir Excel dosyası seçin.')
    
    return render(request, 'weather/show_excel_data.html', {'data': None})

def read_excel_data(file_path):
    try:
        # Excel dosyasını başlıksız oku
        df = pd.read_excel(file_path, header=None)
        print(f"Toplam sütun sayısı: {len(df.columns)}")
        
        # Sabit başlangıç pozisyonları
        START_ROW = 4  # 5. satır (0-based index)
        TARGET_COL = 25  # 26. sütun (0-based index)
        DATE_COL = 1  # 2. sütun (tarih için)
        TOTAL_ROWS = 168  # 7 gün x 24 saat
        
        print(f"Hedef sütun indeksi: {TARGET_COL}")
        
        # Tarihleri al
        dates = []
        current_date = None
        
        # Önce tarihleri topla
        for row in range(START_ROW, START_ROW + TOTAL_ROWS):
            date_val = df.iloc[row, DATE_COL]
            if pd.notnull(date_val) and isinstance(date_val, (pd.Timestamp, datetime)):
                current_date = date_val.strftime('%d-%m-%Y')
                if current_date not in dates:
                    dates.append(current_date)
        
        # Veri sözlüğünü oluştur
        data = {}
        
        # Tarihleri ekle
        for i, date in enumerate(dates[:7], 1):
            data[f'tarih{i}'] = date
        
        # Eksik tarihleri tamamla
        for i in range(len(dates) + 1, 8):
            data[f'tarih{i}'] = f'Gün {i}'
        
        # Saat bilgilerini oluştur
        hours = []
        for i in range(24):
            hours.append(f"{i:02d}:00-{(i+1):02d}:00")
        data['hours'] = hours
        
        # Üretim değerlerini al ve işle
        all_values = []
        for row in range(START_ROW, START_ROW + TOTAL_ROWS):
            try:
                value = df.iloc[row, TARGET_COL]
                print(f"Satır {row + 1}, Sütun {TARGET_COL + 1}, Değer: {value}")
                
                if pd.notnull(value):
                    try:
                        value_str = str(value).strip().replace(',', '.').replace(' ', '')
                        value = float(value_str) / 1000 
                        value = round(value, 2)
                        print(f"Dönüştürülmüş değer (MWh): {value}")
                    except (ValueError, TypeError) as e:
                        print(f"Geçersiz değer (Satır {row + 1}): {value}, Hata: {str(e)}")
                        value = None
                else:
                    value = None
                all_values.append(value)
            except Exception as e:
                print(f"Veri okuma hatası (Satır {row + 1}): {str(e)}")
                all_values.append(None)
        
        # Renk eşikleri
        def get_color_class(value):
            if value is None:
                return 'no-data'
            # Yeni MWh eşikleri
            elif value < 10:  
                return 'very-low'
            elif value < 25:  
                return 'low'
            elif value < 40:  
                return 'medium'
            elif value < 60:  
                return 'high'
            else:  # 60 MWh üstü
                return 'very-high'
        
        # 168 değeri web sayfası formatına dönüştür
        for i, value in enumerate(all_values, 1):
            cell_key = f'cell_m{i}'
            data[cell_key] = {
                'value': f"{value:.2f}" if value is not None else None,
                'color_class': get_color_class(value)
            }
            print(f"{cell_key}: {data[cell_key]}")
        
        return data
        
    except Exception as e:
        print(f"Excel okuma hatası: {str(e)}")
        raise e

def update_from_gmail(request):
    if request.method == 'POST':
        try:
            # Gmail'den en son Excel dosyasını al
            excel_file_path = get_latest_excel_from_gmail()
            
            if excel_file_path:
                try:
                    # Excel dosyasını oku
                    df = pd.read_excel(excel_file_path, header=None)
                    print("\nExcel dosyası başarıyla okundu")
                    print(f"Toplam satır sayısı: {len(df)}")
                    print(f"Toplam sütun sayısı: {len(df.columns)}")
                    
                    # İlk birkaç satırı kontrol et
                    print("\nİlk 10 satır için 2. sütun (tarih) ve 26. sütun (üretim) değerleri:")
                    for i in range(10):
                        try:
                            date_val = df.iloc[i, 1]  # 2. sütun
                            prod_val = df.iloc[i, 25]  # 26. sütun
                            print(f"Satır {i}: Tarih = {date_val}, Üretim = {prod_val}")
                        except:
                            print(f"Satır {i}: Veri okunamadı")
                    
                    # Veriyi hazırla
                    data = {}
                    
                    # Saatleri hazırla
                    hours = []
                    for i in range(24):
                        hours.append(f"{i:02d}:00-{(i+1):02d}:00")
                    data['hours'] = hours

                    # Bugünün tarihini al
                    today = datetime.now().date()
                    print(f"\nBugünün tarihi: {today}")

                    # Sabit başlangıç pozisyonları
                    start_row = 4  # 5. satırdan başla (0-based index)
                    target_col = 25  # 26. sütun (üretim değerleri)
                    date_col = 1  # 2. sütun (tarih)

                    # Her gün için verileri oku
                    for day in range(7):
                        current_date = today + timedelta(days=day)
                        data[f'tarih{day + 1}'] = current_date.strftime('%d-%m-%Y')
                        print(f"\nİşlenen tarih: {current_date.strftime('%d-%m-%Y')}")

                        # Excel'deki tarihi bul
                        found_row = None
                        for row in range(start_row, len(df), 24):
                            try:
                                excel_date = df.iloc[row, date_col]
                                if pd.notnull(excel_date):
                                    if isinstance(excel_date, str):
                                        excel_date = pd.to_datetime(excel_date, dayfirst=True).date()
                                    elif isinstance(excel_date, (pd.Timestamp, datetime)):
                                        excel_date = excel_date.date()
                                    
                                    print(f"Excel'de bulunan tarih: {excel_date}, Aranan tarih: {current_date}")
                                    if excel_date == current_date:
                                        found_row = row
                                        print(f"Eşleşme bulundu! Satır: {found_row}")
                                        break
                            except Exception as e:
                                print(f"Tarih okuma hatası: {str(e)}")
                                continue

                        # Bu gün için saatlik verileri al
                        for hour in range(24):
                            cell_index = (day * 24) + hour + 1
                            
                            if found_row is not None:
                                try:
                                    value = df.iloc[found_row + hour, target_col]
                                    print(f"Saat {hour:02d}:00 - Okunan değer: {value}")
                                    
                                    if pd.notnull(value):
                                        try:
                                            value = float(str(value).strip().replace(',', '.')) / 1000  # Convert to MWh
                                            print(f"Dönüştürülen değer (MWh): {value}")
                                            
                                            # Renk sınıfını belirle (MWh değerlerine göre)
                                            if value < 10:  # 10 MWh altı
                                                color_class = 'very-low'
                                            elif 10 <= value < 25:  # 10-25 MWh
                                                color_class = 'low'
                                            elif 25 <= value < 40:  # 25-40 MWh
                                                color_class = 'medium'
                                            elif 40 <= value < 60:  # 40-60 MWh
                                                color_class = 'high'
                                            else:  # 60 MWh üstü
                                                color_class = 'very-high'

                                            data[f'cell_m{cell_index}'] = {
                                                'value': f"{value:.2f}",
                                                'color_class': color_class
                                            }
                                            print(f"Hücre {cell_index} için değer kaydedildi")
                                        except ValueError as e:
                                            print(f"Değer dönüştürme hatası: {str(e)}")
                                            data[f'cell_m{cell_index}'] = {
                                                'value': '-',
                                                'color_class': 'no-data'
                                            }
                                    else:
                                        print(f"Boş değer")
                                        data[f'cell_m{cell_index}'] = {
                                            'value': '-',
                                            'color_class': 'no-data'
                                        }
                                except Exception as e:
                                    print(f"Veri okuma hatası: {str(e)}")
                                    data[f'cell_m{cell_index}'] = {
                                        'value': '-',
                                        'color_class': 'no-data'
                                    }
                            else:
                                print(f"Bu tarih için veri bulunamadı")
                                data[f'cell_m{cell_index}'] = {
                                    'value': '-',
                                    'color_class': 'no-data'
                                }

                    print("\nTemplate'e gönderilen veri yapısı:")
                    print("Tarihler:")
                    for i in range(1, 8):
                        print(f"tarih{i}: {data.get(f'tarih{i}')}")
                    print("\nÖrnek hücre değerleri:")
                    for i in range(1, 25):  # İlk günün verilerini göster
                        cell_key = f'cell_m{i}'
                        if cell_key in data:
                            print(f"{cell_key}: {data[cell_key]}")
                    
                    # Geçici dosyayı sil
                    os.unlink(excel_file_path)
                    
                    messages.success(request, 'Gmail\'den veriler başarıyla güncellendi.')
                    return render(request, 'weather/show_excel_data.html', {'data': data})
                except Exception as e:
                    print(f"Excel dosyası okuma hatası: {str(e)}")
                    messages.error(request, f'Excel dosyası okuma hatası: {str(e)}')
                finally:
                    # Geçici dosyayı temizlemeye çalış
                    try:
                        if os.path.exists(excel_file_path):
                            os.unlink(excel_file_path)
                    except:
                        pass
            else:
                messages.warning(request, 'Gmail\'de yeni Excel dosyası bulunamadı.')
        except Exception as e:
            print(f"Gmail'den güncelleme hatası: {str(e)}")
            messages.error(request, f'Gmail\'den güncelleme hatası: {str(e)}')
    
    return render(request, 'weather/show_excel_data.html', {'data': None})


