import calendar
import os
import csv
import re
from click import command
import pyautogui 
from spotify_control import next_spotify_song, start_spotify_song, stop_spotify_song
import win32com.client
import screen_brightness_control as sbc
import speech_recognition as sr # type: ignore
import subprocess
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from comtypes import CLSCTX_ALL
from ctypes import cast, POINTER, pythonapi
from flask import Flask, render_template, request, jsonify, redirect, url_for
from datetime import datetime
import pythoncom


from duyguanalizi import analyze_emotion


app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')

# Ses tanıma için fonksiyon
def recognize_speech():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Dinleniyor...")
        # Gürültüden arındırma için ambient noise seviyesini ayarlıyoruz
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)

    try:
        # Google'ın ses tanıma API'sini kullanarak sesin metne çevrilmesi
        command = recognizer.recognize_google(audio, language='tr-TR').lower()
        print(f"Komut: {command}")
        return command
    except sr.UnknownValueError:
        print("Sesi anlayamadım.")
        return None
    except sr.RequestError:
        print("Ses tanıma servisi kullanılamıyor.")
        return None

# Bilgisayar sesini açma
def increase_volume():
    pyautogui.press('volumeup')
    print("Ses açıldı.")

# Bilgisayar sesini kısma
def decrease_volume():
    pyautogui.press('volumedown')
    print("Ses kısıldı.")

#Parlaklık için gelen komutu uygulama
@app.route('/voice-command', methods=['POST'])
def adjust_system_settings():
    try:
        data = request.get_json()  # JSON verisini al
        if data is None:
            return jsonify({'message': 'Geçersiz veya eksik veri!'}), 400
        
        command = data.get('command', '').lower()
        
        if not isinstance(command, str):
            return jsonify({'message': 'Komut geçersiz!'}), 400
        
        current_brightness = sbc.get_brightness(display=0)[0]
        
        if 'parlaklığı arttır' in command:  # 'arttır' komutu
            sbc.set_brightness(current_brightness + 10, display=0)
            return jsonify({'message': 'Parlaklık arttırıldı!'})
        elif 'parlaklığı azalt' in command:  # 'azalt' komutu
            sbc.set_brightness(current_brightness - 10, display=0)
            return jsonify({'message': 'Parlaklık azaltıldı!'})
        elif 'sesi aç' in command:  # 'sesi aç' komutu
            increase_volume()  # Ses açma fonksiyonunu çağır
            return jsonify({'message': 'Ses açıldı!'})
        elif 'sesi kıs' in command:  # 'sesi kıs' komutu
            decrease_volume()  # Ses kısma fonksiyonunu çağır
            return jsonify({'message': 'Ses kısıldı!'})
        else:
            return jsonify({'message': 'Geçersiz komut!'})
    except Exception as e:
        return jsonify({'message': f'Bir hata oluştu: {str(e)}'})




@app.route('/seslikomut')
def sesli_komut_sayfası():
    return render_template('seslikomut.html')

#Ses için gelen komutu uygulam
@app.route('/voice-command', methods=['GET'])
def voice_command():
    command = recognize_speech()

    if command:
        # Küçük harflerle kontrol ederek komutları karşılaştırıyoruz
        command = command.strip()

        if "sesi kıs" in command:
            decrease_volume()
            return jsonify({"message": "Ses kısıldı"}), 200
        elif "sesi aç" in command:
            increase_volume()
            return jsonify({"message": "Ses açıldı"}), 200
        else:
            return jsonify({"message": "Geçersiz komut: " + command}), 400
    return jsonify({"message": "Komut alınamadı"}), 400



@app.route('/duyguanalizi', methods=['GET', 'POST'])
def duygu_analizi():
    emotion = None
    if request.method == 'POST':
        # Dosya yükleme işlemi
        file = request.files['file']
        if file and file.filename.endswith('.wav'):
            file_path = 'uploaded_file.wav'
            file.save(file_path)

            # Duygu analizini yap
            emotion = analyze_emotion(file_path)

    return render_template('duyguanalizi.html', emotion=emotion)


# Etkinlikleri alacak fonksiyon
def get_events():
    events = {}
    try:
        with open('events.csv', mode='r', encoding='utf-8') as file:
            reader = csv.reader(file)
            for row in reader:
                if len(row) == 2:  # Eğer tarih ve etkinlik varsa
                    events[row[0]] = row[1]
    except FileNotFoundError:
        pass  # Eğer dosya yoksa, boş bir sözlük döner
    return events

# Global değişken
voice_event = None

def add_event_with_voice():
    global voice_event
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Lütfen tarihi ve etkinliği söyleyin (örnek: '6 Ocak deneme toplantısı')")
        try:
            audio = recognizer.listen(source)
            text = recognizer.recognize_google(audio, language="tr-TR")
            print(f"Tanımlanan ses: {text}")

            # Metinden tarih ve etkinlik çıkarma
            months = {
                "Ocak": "01", "Şubat": "02", "Mart": "03", "Nisan": "04", "Mayıs": "05", "Haziran": "06",
                "Temmuz": "07", "Ağustos": "08", "Eylül": "09", "Ekim": "10", "Kasım": "11", "Aralık": "12"
            }

            words = text.split()
            print(f"Parçalanan kelimeler: {words}")

            day = int(words[0])
            month_name = words[1]
            month = months.get(month_name, "01")
            event = " ".join(words[2:])

            # Güncel yılı al ve tarih formatına dönüştür
            year = datetime.now().year
            date = f"{year}-{month}-{day:02d}"

            # Konsol çıktısını kontrol et
            print(f"Tarih: {date}, Etkinlik: {event}")

            # Tarih doğrulama
            try:
                datetime.strptime(date, "%Y-%m-%d")
            except ValueError:
                print("Geçersiz tarih formatı!")
                return

            # Sesli komutla alınan tarih ve etkinlik bilgisini global değişkende sakla
            voice_event = {"date": date, "event": event}

            # Etkinliği CSV'ye ekle
            with open('events.csv', mode='a', encoding='utf-8', newline='') as file:
                writer = csv.writer(file)
                writer.writerow([date, event])

            print("Sesle etkinlik başarıyla eklendi.")
        except sr.UnknownValueError:
            print("Ses tanınamadı. Lütfen tekrar deneyin.")
        except sr.RequestError:
            print("Ses hizmeti kullanılamıyor.")


# Takvim sayfası
@app.route('/takvim', methods=['GET', 'POST'])
def takvim():
    events = get_events()
    current_year = 2025
    global voice_event  # Sesli komutla alınan etkinlik bilgilerini kullanacağız

    # Takvim oluşturma
    months = [calendar.month_name[i] for i in range(1, 13)]
    calendar_data = {}
    for month_num in range(1, 13):
        month_days = calendar.monthrange(current_year, month_num)[1]
        first_day_of_month = calendar.monthrange(current_year, month_num)[0]

        month_events = {}
        for day in range(1, month_days + 1):
            date_str = f"{current_year}-{month_num:02d}-{day:02d}"
            event = events.get(date_str, None)
            month_events[day] = event if event else "Etkinlik Yok"

        days_in_week = ['Pazartesi', 'Salı', 'Çarşamba', 'Perşembe', 'Cuma', 'Cumartesi', 'Pazar']
        month_grid = [[] for _ in range(6)]

        current_day = 1
        week_index = 0
        for _ in range(first_day_of_month):
            month_grid[week_index].append(None)

        for day in range(1, month_days + 1):
            if len(month_grid[week_index]) < 7:
                month_grid[week_index].append(day)
            else:
                week_index += 1
                month_grid[week_index].append(day)

        calendar_data[month_num] = {
            "month_name": months[month_num - 1],
            "days_in_week": days_in_week,
            "month_grid": month_grid,
            "month_events": month_events
        }

    # Eğer sesli komutla bir etkinlik eklenmişse, bunu formda göstereceğiz
    if voice_event is not None and isinstance(voice_event, dict):
        date_from_voice = voice_event.get("date", "")
        event_from_voice = voice_event.get("event", "")
    else:
        date_from_voice = ""
        event_from_voice = ""


    if request.method == 'POST':
        if 'date' in request.form and 'event' in request.form:
            date = request.form['date']
            event = request.form['event']
            with open('events.csv', mode='a', encoding='utf-8', newline='') as file:
                writer = csv.writer(file)
                writer.writerow([date, event])
            return redirect(url_for('takvim'))

        # 🎤 Sesle etkinlik ekleme isteği
        if 'voice_event' in request.form:
            add_event_with_voice()
            return redirect(url_for('takvim'))

    return render_template('takvim.html', calendar_data=calendar_data, 
                           date_from_voice=date_from_voice, event_from_voice=event_from_voice)



@app.route('/entegrasyonlar')
def entegrasyonlar():
    return render_template('entegrasyonlar.html')

#spotify şarkıyı başlat
@app.route('/start-song', methods=['GET'])
def start_song():
    start_spotify_song()
    return jsonify({'message': 'Spotify şarkısı başlatıldı!'})

#spotify şarkıyı durdur
@app.route('/pause-song', methods=['GET'])
def pause_song():
    stop_spotify_song()
    return jsonify({'message': 'Spotify şarkısı durduruldu!'})

#spotify şarkıyı değiştir
@app.route('/next-song', methods=['GET'])
def next_song():
    next_spotify_song()
    return jsonify({'message': 'Sonraki şarkıya geçildi!'})

#outlook aç
def execute_command(command):
    if "outlook aç" in command.lower():  # Komut küçük harflerle kontrol ediliyor
        try:
            subprocess.Popen(["start", "outlook"], shell=True)
            return "Outlook uygulaması açıldı."
        except Exception as e:
            return f"Outlook açılırken bir hata oluştu: {e}"
    else:
        return "Komut tanınmadı veya desteklenmiyor."

@app.route('/', methods=["POST"])
def handle_command():
    command = request.form.get('command', '')
    response = execute_command(command)
    return jsonify({"response": response})

@app.route('/open-outlook', methods=["GET"])
def open_outlook():
    try:
        subprocess.Popen(["start", "outlook"], shell=True)
        return jsonify({"message": "Outlook uygulaması açıldı."})
    except Exception as e:
        return jsonify({"message": f"Outlook açılırken bir hata oluştu: {e}"})
    
#mail gönderme 
def send_email(to, subject, body):
    try:
        pythoncom.CoInitialize()  # COM başlatma işlemi
        
        outlook = win32com.client.Dispatch('Outlook.Application')
        mail = outlook.CreateItem(0)  # 0: Mail Item (e-posta)
        mail.To = to
        mail.Subject = subject
        mail.Body = body
        mail.Send()

        pythoncom.CoUninitialize()  # COM başlatma işlemini sonlandırma
        
        return "E-posta başarıyla gönderildi."
    except Exception as e:
        pythoncom.CoUninitialize()  # COM başlatma işlemini sonlandırma
        return f"E-posta gönderilirken bir hata oluştu: {e}"

@app.route('/send-email', methods=["POST"])
def send_email_command():
    # Burada komuttan alınan bilgileri alıyoruz (bu bilgileri daha sonra sesli komuttan alacağız)
    to = request.form.get('to', '')
    subject = request.form.get('subject', '')
    body = request.form.get('body', '')
    
    response = send_email(to, subject, body)
    return jsonify({"response": response})

#e-posta oku
def read_emails():
    try:
        pythoncom.CoInitialize()  # COM başlatma işlemi
        
        outlook = win32com.client.Dispatch('Outlook.Application')
        namespace = outlook.GetNamespace("MAPI")
        
        # Inbox (Gelen Kutusu) klasörüne erişim
        inbox = namespace.GetDefaultFolder(6)  # 6 = Gelen Kutusu
        messages = inbox.Items
        message = messages.GetLast()  # Son e-posta alınıyor
        
        subject = message.Subject
        body = message.Body
        
        pythoncom.CoUninitialize()  # COM sonlandırma işlemi
        
        return f"Başlık: {subject}\nİçerik: {body}"
    
    except Exception as e:
        pythoncom.CoUninitialize()  # COM sonlandırma işlemi
        return f"E-posta okunurken bir hata oluştu: {e}"

@app.route('/read-email', methods=["GET"])
def read_email_command():
    response = read_emails()
    return jsonify({"response": response})

# Görevleri CSV dosyasından okuma fonksiyonu
def read_tasks():
    tasks = []
    try:
        with open('GorevListesi.csv', newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            tasks = [row[0] for row in reader]
    except FileNotFoundError:
        # Eğer dosya yoksa boş liste döner
        pass
    return tasks

# Görevleri CSV dosyasına yazma fonksiyonu
def write_task(task):
    with open('GorevListesi.csv', 'a', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([task])

# Görev Listesi sayfasını görüntüleme
@app.route('/gorevlistesi')
def gorev_listesi():
    tasks = read_tasks()
    return render_template('gorevlistesi.html', tasks=tasks)

# Yeni görev ekleme isteğini işleme
@app.route('/add_task', methods=['POST'])
def add_task():
    task = request.json.get('task')
    if task:
        write_task(task)
        return jsonify({"message": "Görev başarıyla eklendi!"}), 201
    return jsonify({"message": "Geçersiz görev!"}), 400


if __name__ == '__main__':
    app.run(debug=True)
