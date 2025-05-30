#!/usr/bin/python3
# Bu satır, Linux/Unix sistemlerinde (Raspberry Pi'nin işletim sistemi gibi) bu betiğin 'python3' yorumlayıcısı ile çalıştırılması gerektiğini belirtir.
# Bu sayede dosyayı doğrudan çalıştırılabilir hale getirebiliriz (örneğin: ./dontlooktoname.py).

import serial
# 'serial' kütüphanesi (pySerial), Raspberry Pi'nin USB portlarına bağlı Arduino gibi seri cihazlarla iletişim kurmak için kullanılır.
# Robotun motor, sensör ve pompa kontrolörleriyle veri alışverişi yapmasını sağlar.

import json
# 'json' kütüphanesi, JavaScript Object Notation (JSON) formatındaki verileri Python sözlüklerine ve listelerine dönüştürmek (parse etmek) ve tersine çevirmek için kullanılır.
# Sensör modülünden gelen karmaşık veriler genellikle JSON formatında olduğu için bu kütüphane kritik öneme sahiptir.

import time
# 'time' kütüphanesi, zamanla ilgili işlevleri sağlar.
# Özellikle 'time.sleep()' fonksiyonu, belirli bir süre boyunca programın duraklatılması (beklemesi) için kullanılır, bu da döngüleri ve zamanlamaları kontrol etmek için önemlidir.

import threading
# 'threading' kütüphanesi, program içinde birden fazla iş parçacığı (thread) oluşturmayı ve yönetmeyi sağlar.
# Bu, robotun aynı anda birden fazla görevi (sensör okuma, web arayüzü sunma, motor mantığını yürütme) eş zamanlı olarak yapabilmesini mümkün kılar.

import RPi.GPIO as GPIO
# 'RPi.GPIO' kütüphanesi, Raspberry Pi'nin Genel Amaçlı Giriş/Çıkış (GPIO) pinlerini kontrol etmek için özel olarak tasarlanmıştır.
# Ultrasonik sensörler gibi doğrudan GPIO pinlerine bağlı donanımların tetiklenmesi ve veri okunması için kullanılır.

import requests
# 'requests' kütüphanesi, HTTP istekleri yapmak için popüler ve kullanımı kolay bir kütüphanedir.
# Robotun internet üzerinden IP adresi tabanlı konum bilgisi almak için harici bir web servisine (API) istek göndermesini sağlar.

# import openai
# 'openai' kütüphanesi, OpenAI'ın yapay zeka modelleriyle etkileşime girmek için kullanılır.
# Mevcut kodda, daha önceki sürümlerdeki yapay zeka analiz fonksiyonu kaldırıldığı için bu satır yorum satırı yapılmıştır ve aktif olarak kullanılmamaktadır.
# Eğer AI özelliklerini tekrar eklemeyecekseniz bu satırı tamamen silebilirsiniz.

import sys
# 'sys' kütüphanesi, sistemle ilgili parametreler ve fonksiyonlar sağlar.
# Örneğin, programdan çıkış yapmak için 'sys.exit()' veya standart giriş/çıkış akışlarına erişmek için kullanılır.

import traceback
# 'traceback' kütüphanesi, bir hata (istisna) meydana geldiğinde, bu hatanın çağrı yığınını (call stack) yazdırmak için kullanılır.
# Bu, kodda hataların nerede meydana geldiğini tespit etmek ve ayıklamak (debug) için çok değerlidir.

import logging
# 'logging' kütüphanesi, uygulamanın çalışması sırasında olayları (bilgiler, uyarılar, hatalar, hata ayıklama mesajları) kaydetmek için esnek bir sistem sunar.
# Bu, robotun ne yaptığını, hangi sorunlarla karşılaştığını anlamak için hayati öneme sahiptir.

import os
# 'os' kütüphanesi, işletim sistemiyle etkileşime girmek için işlevsellik sağlar.
# Dosya yolları, dizin işlemleri ve ortam değişkenleri gibi görevler için kullanılır.

import psutil
# 'psutil' (process and system utilities) kütüphanesi, sistemdeki çalışan işlemler ve sistem kaynakları (CPU, RAM, disk kullanımı) hakkında bilgi almak için kullanılır.
# Robotun sistem sağlığını izlemek ve web arayüzünde göstermek için önemlidir.

from flask import Flask, render_template_string, jsonify, url_for, request
# 'Flask' kütüphanesi, Python ile hafif bir web uygulaması (micro-framework) oluşturmak için kullanılır.
# 'Flask': Web uygulamasının ana sınıfı.
# 'render_template_string': HTML şablonlarını doğrudan bir dizeden oluşturmaya olanak tanır.
# 'jsonify': Python sözlüklerini ve listelerini JSON formatına dönüştürüp HTTP yanıtı olarak göndermek için kullanılır.
# 'url_for': Belirli bir fonksiyon için URL oluşturmaya yardımcı olur.
# 'request': Gelen HTTP isteklerindeki verilere (örneğin, POST verileri) erişmek için kullanılır.

import math
# 'math' kütüphanesi, matematiksel işlemleri ve sabitleri (örneğin, sinüs, kosinüs, karekök) sağlar.
# Özellikle GPS koordinatları arasındaki mesafeyi ve yönü hesaplamak için Haversine formülünde kullanılır.

from logging.handlers import RotatingFileHandler
# 'logging.handlers.RotatingFileHandler', 'logging' kütüphanesinin bir parçasıdır.
# Log dosyalarının belirli bir boyuta ulaştığında otomatik olarak yeni bir dosyaya geçmesini (rotasyon yapmasını) sağlar.
# Bu, log dosyalarının çok büyümesini ve disk alanını doldurmasını engeller.

# --- YAPILANDIRMA AYARLARI ---
# Bu bölüm, robotun çeşitli çalışma parametrelerini içeren bir Python sözlüğüdür.
# Kodun kolayca ayarlanabilmesi ve değiştirilebilmesi için tüm kritik ayarlar burada toplanmıştır.
config = {
    "serial_ports": {
        "motor": "/dev/ttyUSB2", # Motor kontrol kartının bağlı olduğu seri portun adı.
        "sensor": "/dev/ttyUSB0", # Sensör modülünün bağlı olduğu seri portun adı (su seviyesi, GPS).
        "pump": "/dev/ttyUSB1",   # Pompa kontrolörünün bağlı olduğu seri portun adı.
        "motor_baud_rate": 9600,  # Motor seri portu için baud hızı (veri iletim hızı).
        "sensor_baud_rate": 115200, # Sensör seri portu için baud hızı.
        "pump_baud_rate": 9600,   # Pompa seri portu için baud hızı.
        "timeout": 1              # Seri port okumaları için zaman aşımı süresi (saniye).
    },
    "gpio_pins": {
        "trig_front": 23, # Ön ultrasonik sensörün tetikleme (Trigger) pini (BCM numaralandırması).
        "echo_front": 24, # Ön ultrasonik sensörün yankı (Echo) pini.
        "trig_rear": 25,  # Arka ultrasonik sensörün tetikleme (Trigger) pini.
        "echo_rear": 8    # Arka ultrasonik sensörün yankı (Echo) pini.
    },
    # "openai_api_key": "sk-XXXXXXX", # Kendi OpenAI API anahtarınızı girin - OpenAI kullanımı kaldırıldığı için bu satır pasifize edilmiştir.
    "manual_override_duration_seconds": 10, # Manuel kontrol aktif edildiğinde, bu süre (saniye) sonra otomatik olarak pasifize olur.
    "log_file": "robot.log", # Robotun ana log dosyası adı.
    "log_level": "DEBUG",    # Loglama seviyesi (DEBUG, INFO, WARNING, ERROR, CRITICAL). DEBUG en detaylı olanıdır.
    "app_host": "0.0.0.0",   # Flask web uygulamasının dinleyeceği IP adresi (0.0.0.0 tüm arayüzlerden erişilebilir demektir).
    "app_port": 5000,        # Flask web uygulamasının dinleyeceği port numarası.
    "navigation_settings": {
        "target_reached_threshold_meters": 5.0, # Hedefe ulaşıldı sayılması için hedefe olan maksimum mesafe (metre).
        "water_discharge_duration_seconds": 15, # Su boşaltma süresi (saniye). (Şu an aktif değil)
        "obstacle_threshold_nav_cm": 40, # Navigasyon sırasında engelden kaçınma eşiği (santimetre). (Şu an aktif değil)
    },
    "water_level_settings": {
        "water1_full_threshold": 300,          # Su tankı 1'in dolu kabul edilmesi için gereken değer.
        "water2_source_ready_threshold": 600,  # Su kaynağı 2'nin hazır kabul edilmesi için gereken değer.
    },
    # YENİ: Otonom hareket için mesafeler
    "autonomous_movement_thresholds": {
        "rear_obstacle_cm": 25,   # Arka mesafenin bu değerin altındaysa engelden kaçınma başlar (santimetre).
        "rear_clear_cm": 30,      # Arka mesafe bu değerin üstündeyse geri gitmeye devam edebilir (santimetre).
        "turn_duration": 0.5,     # Engelden kaçınmak için dönüş süresi (saniye).
        "move_duration_short": 0.2, # Kısa hareket süresi (saniye).
        "move_duration_long": 1.0, # Normal hareket süresi (saniye).
        "default_safe_move_duration": 0.5 # Sensörler arızalıyken veya geçersiz veri dönerken varsayılan güvenli hareket süresi (saniye).
    },
    "ip_location_update_interval_seconds": 60 # Eğer GPS sensörü aktif değilse, IP tabanlı konumu kaç saniyede bir güncelleyeceğini belirler.
}

# --- LOGLAMA KURULUMU ---
# Bu bölüm, uygulamanın nasıl loglama yapacağını yapılandırır.
log_file = config.get('log_file', 'robot.log') # Yapılandırmadan log dosyasının adını alır, yoksa 'robot.log' kullanır.
log_level_str = config.get('log_level', 'INFO').upper() # Yapılandırmadan log seviyesini alır ve büyük harfe çevirir.
log_level = getattr(logging, log_level_str, logging.INFO) # String log seviyesini (örn. "DEBUG") gerçek logging seviyesi sabitine (örn. logging.DEBUG) dönüştürür.

# Ana log dosyası için RotatingFileHandler oluşturulur.
# Bu handler, log dosyasının 'maxBytes' (5MB) boyutuna ulaştığında yeni bir dosya oluşturur ve 'backupCount' (5) kadar eski dosyayı saklar.
handler = RotatingFileHandler(log_file, maxBytes=1024*1024*5, backupCount=5)
# Log mesajlarının formatını belirler (zaman, seviye, thread adı, mesaj).
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(threadName)s - %(message)s')
handler.setFormatter(formatter) # Oluşturulan formatlayıcıyı handlera atar.

logger = logging.getLogger(__name__) # Bu modül için bir logger nesnesi oluşturur.
logger.setLevel(log_level) # Logger'ın seviyesini ayarlar. Sadece bu seviye ve üstündeki mesajlar işlenir.
logger.addHandler(handler) # Oluşturulan RotatingFileHandler'ı logger'a ekler, böylece loglar dosyaya yazılır.
# Konsol çıktısı için de handler ekleyebilirsiniz (isteğe bağlı, kaldırıldı):
# logger.addHandler(logging.StreamHandler(sys.stdout))

werkzeug_logger = logging.getLogger('werkzeug') # Flask'ın kullandığı dahili Werkzeug web sunucusunun log'larını alır.
werkzeug_logger.setLevel(logging.ERROR) # Werkzeug log seviyesini ERROR'a ayarlar, böylece sadece kritik hatalar konsola/dosyaya yazılır ve gereksiz çıktılar engellenir.

# openai.api_key = config['openai_api_key'] # OpenAI API anahtarını ayarlar - kullanımı kaldırıldığı için bu satır pasifize edilmiştir.

# GPIO pinlerini başlatır.
GPIO.setmode(GPIO.BCM) # GPIO pin numaralandırma şemasını BCM (Broadcom chip-specific) moduna ayarlar.
GPIO.setup(config['gpio_pins']['trig_front'], GPIO.OUT) # Ön ultrasonik sensörün tetikleme pinini çıkış olarak ayarlar.
GPIO.setup(config['gpio_pins']['echo_front'], GPIO.IN)  # Ön ultrasonik sensörün yankı pinini giriş olarak ayarlar.
GPIO.setup(config['gpio_pins']['trig_rear'], GPIO.OUT)   # Arka ultrasonik sensörün tetikleme pinini çıkış olarak ayarlar.
GPIO.setup(config['gpio_pins']['echo_rear'], GPIO.IN)    # Arka ultrasonik sensörün yankı pinini giriş olarak ayarlar.

app = Flask(__name__) # Yeni bir Flask web uygulaması örneği oluşturur. '__name__' uygulamayı tanımlar.

class RobotSystem:
    # Bu sınıf, robotun tüm ana işlevlerini (seri iletişim, sensör okuma, motor kontrolü, navigasyon, durum yönetimi) kapsar.
    def __init__(self):
        # Sınıfın yapıcı metodu. Bir RobotSystem nesnesi oluşturulduğunda ilk çalışacak kısımdır.
        logger.info("Robot sistemi başlatılıyor...") # Loglama ile başlatma bilgisini kaydeder.

        # Seri portları başlatır. Eğer portlar başlatılamazsa programdan çıkar.
        self.motor_serial = self._init_serial_port('motor')
        self.sensor_serial = self._init_serial_port('sensor')
        self.pump_serial = self._init_serial_port('pump')

        self.running = True # Robotun ana döngülerinin çalışıp çalışmadığını kontrol eden bir bayrak. True ise çalışır.
        self.sensor_data = {} # Seri porttan okunan su seviyesi ve diğer sensör verilerini depolamak için boş bir sözlük.
        self.distances = {"front": 0, "rear": 0} # Ön ve arka ultrasonik sensör mesafelerini depolamak için sözlük (cm cinsinden).
        self.gps_location = None # Mevcut GPS konumunu depolamak için değişken (başlangıçta yok).
        self.last_ip_location_update_time = 0 # IP tabanlı konumun en son ne zaman güncellendiğini tutar.
        self.current_motor_command = "dur" # Robotun şu anki motor komutunu (örn. "ileri", "geri", "dur") tutar.
        self.manual_override_active = False # Manuel kontrolün aktif olup olmadığını belirten boolean bayrak.
        self.manual_override_timer = None # Manuel kontrol süresini takip eden zamanlayıcı nesnesi.
        self.manual_override_duration = config['manual_override_duration_seconds'] # Manuel kontrolün varsayılan süresi (konfigürasyondan alınır).
        self.system_info = {"cpu_percent": 0, "ram_percent": 0, "disk_percent": 0} # CPU, RAM, Disk kullanım bilgilerini depolamak için sözlük.
        self.last_error_message = "" # Web arayüzünde gösterilecek son hata mesajını tutar.

        self.nav_config = config.get("navigation_settings") # Navigasyonla ilgili yapılandırma ayarlarını yükler.
        self.auto_move_config = config.get("autonomous_movement_thresholds") # Otonom hareket eşiklerini yükler.
        self.target_gps_location = {"lat": None, "lon": None} # Robotun gideceği hedef GPS konumunu tutar.
        self.navigation_active = False # Navigasyon modunun aktif olup olmadığını gösteren bayrak.
        self.navigation_stage = "IDLE" # Navigasyonun mevcut aşamasını belirtir (örneğin "IDLE", "NAVIGATING", "DISCHARGING_WATER").
        self.distance_to_target = 0.0 # Hedefe olan mesafeyi metre cinsinden tutar.
        self.bearing_to_target = 0.0 # Hedefe olan yönü derece cinsinden tutar.
        self.discharge_start_time = None # Su boşaltma işleminin başladığı zamanı tutar.

        self.water_config = config.get("water_level_settings") # Su seviyesiyle ilgili yapılandırma ayarlarını yükler.
        self.pump_in_state = "OFF"  # 'IN' pompasının mevcut durumunu (ON/OFF) tutar.
        self.pump_out_state = "OFF" # 'OUT' pompasının mevcut durumunu (ON/OFF) tutar.


        global robot_instance # 'robot_instance' global değişkenini tanımlar.
        robot_instance = self # Mevcut RobotSystem nesnesini global 'robot_instance' değişkenine atar, böylece Flask rotaları ona erişebilir.
        logger.info("Robot sistemi başlatma tamamlandı.") # Başlatma işleminin tamamlandığını loglar.

    def _init_serial_port(self, device_type):
        # Belirtilen 'device_type' (motor, sensör, pompa) için seri portu başlatmaya çalışır.
        port_config = config['serial_ports'] # Seri port yapılandırmasını alır.
        port_name = port_config.get(device_type) # Cihaz tipine göre port adını alır.
        baud_rate = port_config.get(f'{device_type}_baud_rate') # Cihaz tipine göre baud hızını alır.
        timeout = port_config.get('timeout') # Seri port zaman aşımını alır.
        
        if not port_name or baud_rate is None:
            # Eğer port adı veya baud hızı eksikse kritik hata loglar ve programdan çıkar.
            logger.critical(f"KRİTİK HATA: '{device_type}' için seri port veya baud rate yapılandırması eksik.")
            sys.exit(1) # Programı hata koduyla sonlandırır.

        try:
            ser = serial.Serial(port_name, baud_rate, timeout=timeout) # Seri portu belirtilen ayarlarla açmaya çalışır.
            logger.info(f"Seri port '{device_type}' ({port_name}, {baud_rate} baud) başarıyla başlatıldı.") # Başarılı başlatmayı loglar.
            return ser # Açılan seri port nesnesini döndürür.
        except serial.SerialException as e:
            # Seri portla ilgili bir hata oluşursa (örn. port bulunamadı), kritik hata loglar ve programdan çıkar.
            logger.critical(f"KRİTİK HATA: Seri port '{device_type}' ({port_name}) başlatılamadı: {e}. Lütfen port adını ve bağlantıyı kontrol edin.")
            sys.exit(1) # Programı hata koduyla sonlandırır.
        except Exception as e:
            # Diğer genel hatalar için kritik hata loglar ve programdan çıkar.
            logger.critical(f"KRİTİK HATA: Seri port başlatma hatası: {e}", exc_info=True) # exc_info=True hata izini loglar.
            sys.exit(1) # Programı hata koduyla sonlandırır.

    def read_ultrasonic(self, trig, echo):
        # Ultrasonik sensörden mesafe okuma işlevini gerçekleştirir.
        # 'trig': Tetikleme (Trigger) pini numarası.
        # 'echo': Yankı (Echo) pini numarası.
        try:
            # Sensörü sıfırlamak ve yeni bir ölçüm için hazırlamak için tetikleme pinini kısa bir süre düşük tutar.
            GPIO.output(trig, False)
            time.sleep(0.000002) # Datasheet'e göre en az 2 mikrosaniye düşük kalmalı.

            # Tetikleme sinyalini gönderir: 10 mikrosaniye yüksek (HIGH).
            GPIO.output(trig, True)
            time.sleep(0.00001) # 10 mikrosaniye bekler.
            GPIO.output(trig, False) # Tetikleme pinini tekrar düşük (LOW) çeker.

            pulse_start = time.time() # Yankı sinyalinin başlamasını beklemek için başlangıç zamanı.
            pulse_end = time.time()   # Yankı sinyalinin bitmesini beklemek için bitiş zamanı.

            # Timeout için maksimum bekleme süresi (25 milisaniye) belirlenir. Bu, sensör yanıt vermezse sonsuz döngüyü önler.
            timeout_max_duration = 0.025 # 25 milisaniye (yaklaşık 4.2 metre mesafeye denk gelir).

            # ECHO pini HIGH olana kadar bekler (pulse_start).
            timeout_entry_time = time.time() # Timeout kontrolü için zamanı kaydeder.
            while GPIO.input(echo) == 0: # ECHO pini LOW iken döngüye devam et.
                pulse_start = time.time() # pulse_start'ı güncel tut.
                if time.time() - timeout_entry_time > timeout_max_duration:
                    # Eğer belirlenen timeout süresi aşılırsa, sensör yanıt vermiyor demektir.
                    logger.debug(f"Ultrasonik (TRIG:{trig}) - ECHO HIGH beklenirken timeout.") # Hata ayıklama logu.
                    return 999 # Geçersiz/çok uzak mesafe olarak 999 döndürür.
            
            # ECHO pini LOW olana kadar bekler (pulse_end).
            timeout_entry_time = time.time() # Timeout süresini bu döngü için sıfırla.
            while GPIO.input(echo) == 1: # ECHO pini HIGH iken döngüye devam et.
                pulse_end = time.time() # pulse_end'i güncel tut.
                if time.time() - timeout_entry_time > timeout_max_duration:
                    # Eğer belirlenen timeout süresi aşılırsa, sensör sinyalini bırakmıyor demektir.
                    logger.debug(f"Ultrasonik (TRIG:{trig}) - ECHO LOW beklenirken timeout.") # Hata ayıklama logu.
                    return 999 # Geçersiz/çok uzak mesafe olarak 999 döndürür.

            duration = pulse_end - pulse_start # Yankı sinyalinin süresini hesaplar.
            
            # Sürenin negatif veya çok küçük olması durumunda hata kontrolü.
            if duration <= 0:
                logger.debug(f"Ultrasonik (TRIG:{trig}) - Negatif veya sıfır süre: {duration}") # Hata ayıklama logu.
                return 999 # Geçersiz mesafe olarak 999 döndürür.

            # Mesafeyi hesaplar: (Süre * Sesin Hızı (cm/s)) / 2 (çünkü sinyal gidip gelir).
            # Sesin hızı yaklaşık 34300 cm/s olduğu için 34300 / 2 = 17150 kullanılır.
            distance = round(duration * 17150, 2) 

            # Geçerli aralık kontrolü. HC-SR04 genellikle 2cm'den az ve 400cm'den fazlası için güvenilir değildir.
            # 0.4 veya 0.7 gibi saçma değerler bu alt limit tarafından filtrelenecektir.
            if 2 <= distance < 400: 
                return distance # Geçerli mesafeyi döndürür.
            else:
                logger.debug(f"Ultrasonik (TRIG:{trig}) - Geçersiz mesafe: {distance} cm (aralık dışı).") # Hata ayıklama logu.
                return 999 # Geçersiz veya çok uzak/yakın mesafe olarak 999 döndürür.

        except Exception as e:
            # Ultrasonik okuma sırasında herhangi bir hata oluşursa, loglar ve 999 döndürür.
            logger.error(f"Ultrasonik okuma hatası (TRIG:{trig}, ECHO:{echo}): {e}", exc_info=True)
            return 999

    def update_sensors(self):
        # Robotun tüm sensör verilerini sürekli olarak okuyan bir iş parçacığı fonksiyonu.
        while self.running: # Program çalıştığı sürece döngüye devam et.
            try:
                # Hem ön hem de arka ultrasonik sensörden mesafe okur (UI'da göstermek için).
                self.distances["front"] = self.read_ultrasonic(config['gpio_pins']['trig_front'], config['gpio_pins']['echo_front'])
                self.distances["rear"] = self.read_ultrasonic(config['gpio_pins']['trig_rear'], config['gpio_pins']['echo_rear'])

                # Seri porttan (sensör modülü) veri okumayı dener.
                if self.sensor_serial and self.sensor_serial.in_waiting: # Seri portta okunacak veri varsa.
                    line = self.sensor_serial.readline().decode(errors='ignore').strip() # Bir satır oku, decode et ve boşlukları temizle.
                    if line: # Eğer okunan satır boş değilse.
                        try:
                            self.sensor_data = json.loads(line) # JSON satırını Python sözlüğüne dönüştürür (water1, water2 vb. içerir).
                            # Gelen JSON verilerini "isim.log" dosyasına ekler.
                            with open("isim.log", "a") as log_file:
                                log_file.write(line + "\n")
                            
                            gps_from_sensor = self.sensor_data.get("gps") # Sensör verisinden GPS bölümünü alır.
                            if isinstance(gps_from_sensor, dict) and "lat" in gps_from_sensor and "lon" in gps_from_sensor:
                                # Eğer sensörden geçerli GPS verisi geldiyse.
                                try:
                                    self.gps_location = {
                                        "lat": float(gps_from_sensor["lat"]),
                                        "lon": float(gps_from_sensor["lon"])
                                    } # GPS koordinatlarını float'a çevirip kaydeder.
                                except (ValueError, TypeError):
                                    # GPS verisi formatı hatalıysa.
                                    logger.warning(f"GPS verisi formatı hatalı: {gps_from_sensor}. IP tabanlı konuma geçiliyor.")
                                    # Eğer GPS verisi hatalıysa veya yoksa ve yeterli süre geçtiyse IP'den konum almayı dener.
                                    if time.time() - self.last_ip_location_update_time > config["ip_location_update_interval_seconds"]:
                                        self.gps_location = self.get_location_by_ip()
                                        self.last_ip_location_update_time = time.time()
                            elif not self.gps_location: 
                                # Eğer seri porttan hiç GPS verisi gelmiyorsa ve yeterli süre geçtiyse IP'den konum almayı dener.
                                if time.time() - self.last_ip_location_update_time > config["ip_location_update_interval_seconds"]:
                                    self.gps_location = self.get_location_by_ip()
                                    self.last_ip_location_update_time = time.time()
                            
                        except json.JSONDecodeError:
                            # Seri porttan gelen veri geçerli bir JSON değilse.
                            logger.warning(f"Geçersiz JSON alındı: '{line}'")
                else: 
                     # Eğer sensör seri portundan hiç veri gelmiyorsa ve yeterli süre geçtiyse IP'den konum almayı dener.
                    if time.time() - self.last_ip_location_update_time > config["ip_location_update_interval_seconds"]:
                        self.gps_location = self.get_location_by_ip()
                        self.last_ip_location_update_time = time.time()

                self.update_system_info() # Sistem CPU, RAM, disk bilgilerini günceller.
            except serial.SerialException as e:
                # Sensör seri portunda hata oluşursa.
                logger.error(f"Sensör seri port hatası: {e}. Yeniden bağlanmayı deniyor...", exc_info=True)
                self.sensor_serial = self._init_serial_port('sensor') # Seri portu yeniden başlatmaya çalışır.
            except Exception as e:
                # Sensör veri okuma döngüsünde beklenmeyen bir hata oluşursa.
                logger.error(f"Sensör veri okuma döngüsü hatası: {e}", exc_info=True)
            time.sleep(0.2) # Sensör okumaları arasında kısa bir bekleme süresi.

    def update_system_info(self):
        # Sistem kaynak kullanım bilgilerini (CPU, RAM, Disk) günceller.
        try:
            self.system_info["cpu_percent"] = psutil.cpu_percent(interval=0.1) # CPU kullanım yüzdesini alır.
            self.system_info["ram_percent"] = psutil.virtual_memory().percent # RAM kullanım yüzdesini alır.
            self.system_info["disk_percent"] = psutil.disk_usage('/').percent # Kök dizin (/) disk kullanım yüzdesini alır.
        except Exception as e:
            logger.error(f"Sistem bilgisi alınamadı: {e}", exc_info=True)

    def get_location_by_ip(self):
        # IP adresi üzerinden yaklaşık konum bilgisi (enlem ve boylam) almaya çalışır.
        try:
            res = requests.get("http://ip-api.com/json/", timeout=3) # ip-api.com'a HTTP GET isteği gönderir.
            data = res.json() # Gelen JSON yanıtını Python sözlüğüne dönüştürür.
            if data and data.get("status") == "success":
                # Eğer istek başarılıysa konum bilgilerini loglar ve döndürür.
                logger.info(f"IP tabanlı konum alındı: {data.get('lat')}, {data.get('lon')}")
                return {"lat": data.get("lat"), "lon": data.get("lon")}
            else:
                # İstek başarısız olursa uyarı loglar.
                logger.warning(f"IP tabanlı konum alınamadı: {data.get('message', 'Bilinmeyen hata')}")
                return None # Konum bilgisi yoksa None döndürür.
        except requests.exceptions.RequestException as e:
            # HTTP isteği sırasında ağ hatası oluşursa uyarı loglar.
            logger.warning(f"IP konum isteği başarısız oldu: {e}")
            return None

    def send_motor(self, command):
        # Motor kontrol kartına hareket komutları gönderir.
        if not self.motor_serial or not self.motor_serial.is_open:
            # Seri port açık değilse hata loglar ve komut göndermez.
            logger.error("Motor seri portu başlatılamadığı veya kapalı olduğu için komut gönderilemedi.")
            self.current_motor_command = "PORT_HATASI" # Durum bilgisini günceller.
            return
        try:
            self.motor_serial.write(f"{command}\n".encode()) # Komutu string olarak gönderir, sonuna yeni satır ekler ve byte'a çevirir.
            self.current_motor_command = command # Anlık motor komutunu günceller.
            logger.info(f"[MOTOR KOMUT] → {command}") # Komutu loglar.
        except serial.SerialException as e:
            # Seri portla iletişim hatası oluşursa.
            logger.error(f"Motor seri portuyla iletişim hatası: {e}. Yeniden bağlanmayı deniyor...", exc_info=True)
            self.current_motor_command = "SERIAL_HATA" # Durum bilgisini günceller.
            self.motor_serial = self._init_serial_port('motor') # Seri portu yeniden başlatmaya çalışır.
        except Exception as e:
            # Diğer genel hatalar oluşursa.
            logger.error(f"Motor komutu gönderilemedi: {e}", exc_info=True)
            self.current_motor_command = "GENEL_HATA" # Durum bilgisini günceller.
            self.last_error_message = f"Motor hatası: {str(e)[:100]}..." # UI'da gösterilecek hata mesajını günceller.

    def send_pump(self, pump_id, state): # state: "ON" veya "OFF"
        # Pompa kontrolörüne komut gönderir.
        if not self.pump_serial or not self.pump_serial.is_open:
            # Seri port açık değilse hata loglar ve komut göndermez.
            logger.error("Pompa seri portu başlatılamadığı veya kapalı olduğu için komut gönderilemedi.")
            return
        try:
            pump_id_upper = pump_id.upper() # Pompa ID'sini büyük harfe çevirir (IN/OUT).
            state_upper = state.upper()     # Durumu büyük harfe çevirir (ON/OFF).
            msg = f"PUMP_{pump_id_upper}_{state_upper}\n" # Gönderilecek mesajı oluşturur.
            self.pump_serial.write(msg.encode()) # Mesajı byte'a çevirip seri porttan gönderir.
            logger.info(f"[POMPA KOMUT] → {msg.strip()}") # Komutu loglar.

            # Pompa durumlarını günceller.
            if pump_id_upper == "IN":
                self.pump_in_state = state_upper
            elif pump_id_upper == "OUT":
                self.pump_out_state = state_upper
        except serial.SerialException as e:
            # Seri portla iletişim hatası oluşursa.
            logger.error(f"Pompa seri portuyla iletişim hatası: {e}. Yeniden bağlanmayı deniyor...", exc_info=True)
            self.pump_serial = self._init_serial_port('pump') # Seri portu yeniden başlatmaya çalışır.
        except Exception as e:
            # Diğer genel hatalar oluşursa.
            logger.error(f"Pompa komutu hatası: {e}", exc_info=True)
            self.last_error_message = f"Pompa hatası: {str(e)[:100]}..." # UI'da gösterilecek hata mesajını günceller.

    # REMOVED: analyze_with_ai function is removed as it's no longer used.
    # Bu fonksiyon OpenAI entegrasyonu için kullanılıyordu ve kaldırıldığı için burada bulunmuyor.

    def set_manual_override(self, active):
        # Manuel kontrol modunu ayarlar.
        self.manual_override_active = active # Manuel kontrol durumunu ayarlar.
        if active:
            self.navigation_active = False # Manuel kontrol aktifken navigasyonu devre dışı bırakır.
            self.navigation_stage = "IDLE" # Navigasyon aşamasını boşta olarak ayarlar.
            if self.manual_override_timer:
                self.manual_override_timer.cancel() # Önceki zamanlayıcıyı iptal eder (eğer varsa).
            # Belirlenen süre sonunda manuel kontrolü temizleyecek yeni bir zamanlayıcı başlatır.
            self.manual_override_timer = threading.Timer(self.manual_override_duration, self.clear_manual_override)
            self.manual_override_timer.start()
            logger.info(f"[MANUEL KONTROL] {self.manual_override_duration} saniye boyunca aktif edildi.")
            self.last_error_message = "" # Hata mesajını temizler.
        else:
            logger.info("[MANUEL KONTROL] Devre dışı bırakıldı.") # Manuel kontrolün devre dışı bırakıldığını loglar.

    def clear_manual_override(self):
        # Manuel kontrol süresi dolduğunda veya iptal edildiğinde çağrılır.
        self.manual_override_active = False # Manuel kontrolü pasifize eder.
        self.manual_override_timer = None # Zamanlayıcıyı sıfırlar.
        logger.info("[MANUEL KONTROL] Süresi doldu, otonom moda dönülüyor.")
        self.send_motor("dur") # Robotu durdurur.

    def _haversine(self, lat1, lon1, lat2, lon2):
        # İki coğrafi koordinat arasındaki büyük daire mesafesini (metre cinsinden) Haversine formülü ile hesaplar.
        R = 6371000 # Dünya'nın ortalama yarıçapı (metre).
        phi1 = math.radians(lat1) # Enlem 1'i radyana çevirir.
        phi2 = math.radians(lat2) # Enlem 2'yi radyana çevirir.
        delta_phi = math.radians(lat2 - lat1) # Enlem farkını radyana çevirir.
        delta_lambda = math.radians(lon2 - lon1) # Boylam farkını radyana çevirir.
        a = math.sin(delta_phi / 2)**2 + \
            math.cos(phi1) * math.cos(phi2) * \
            math.sin(delta_lambda / 2)**2 # Haversine formülünün 'a' bileşeni.
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)) # Haversine formülünün 'c' bileşeni.
        return R * c # Mesafeyi metre cinsinden döndürür.

    def _calculate_bearing(self, lat1, lon1, lat2, lon2):
        # İki GPS noktası arasındaki yönü (pusula yönü, derece cinsinden) hesaplar.
        lat1_rad = math.radians(lat1) # Enlem 1'i radyana çevirir.
        lon1_rad = math.radians(lon1) # Boylam 1'i radyana çevirir.
        lat2_rad = math.radians(lat2) # Enlem 2'yi radyana çevirir.
        lon2_rad = math.radians(lon2) # Boylam 2'yi radyana çevirir.
        
        delta_lon = lon2_rad - lon1_rad # Boylam farkını hesaplar.
        
        x = math.sin(delta_lon) * math.cos(lat2_rad) # Yön hesaplaması için x bileşeni.
        y = math.cos(lat1_rad) * math.sin(lat2_rad) - \
            math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(delta_lon) # Yön hesaplaması için y bileşeni.
        
        initial_bearing = math.atan2(x, y) # Radyan cinsinden başlangıç yönünü hesaplar.
        initial_bearing_degrees = math.degrees(initial_bearing) # Dereceye çevirir.
        compass_bearing = (initial_bearing_degrees + 360) % 360 # Pusula yönünü (0-360 derece) ayarlar.
        return compass_bearing # Pusula yönünü döndürür.

    def set_target_gps_and_navigate(self, lat, lon):
        # Hedef GPS koordinatlarını ayarlar ve navigasyonu aktif olarak işaretler (ancak otomatik olarak başlatmaz).
        try:
            self.target_gps_location = {"lat": float(lat), "lon": float(lon)} # Hedef koordinatları float olarak kaydeder.
            self.navigation_active = True # Navigasyonun aktif olduğunu işaretler (UI geri bildirimi için).
            self.navigation_stage = "NAVIGATING" # Navigasyon aşamasını 'NAVIGATING' olarak ayarlar.
            self.manual_override_active = False # Manuel kontrolü devre dışı bırakır.
            if self.manual_override_timer:
                self.manual_override_timer.cancel() # Manuel kontrol zamanlayıcısını iptal eder.
            logger.info(f"NAV: Yeni hedef ayarlandı: {self.target_gps_location}. NOT: Depo boşverildiği için navigasyon şu an tetiklenmeyecek.")
            self.last_error_message = "" # Hata mesajını temizler.
            return True # Başarılı olduğunu döndürür.
        except ValueError:
            # Koordinatlar geçerli sayılara dönüştürülemezse hata loglar.
            logger.error(f"NAV: Geçersiz hedef koordinatları: lat={lat}, lon={lon}")
            self.last_error_message = "Geçersiz hedef koordinatları."
            return False # Başarısız olduğunu döndürür.

    def _execute_autonomous_decision(self, is_navigating=False):
        # Robotun otonom hareket kararlarını verir (arka sensör verisine göre).
        # 'is_navigating': Robotun şu anda GPS navigasyonunda olup olmadığını belirtir (şimdilik kullanılmıyor).

        rear_dist = self.distances.get("rear", 999) # Arka sensör mesafesini alır, yoksa 999 (geçersiz) kabul eder.
        front_dist = self.distances.get("front", 999) # Ön sensör mesafesini alır, yoksa 999 (geçersiz) kabul eder.
        rear_obstacle_threshold = self.auto_move_config["rear_obstacle_cm"] # Arka engel eşiğini alır.
        rear_clear_threshold = self.auto_move_config["rear_clear_cm"]       # Arka yol açık eşiğini alır.
        turn_duration = self.auto_move_config["turn_duration"]               # Dönüş süresini alır.
        move_duration_short = self.auto_move_config["move_duration_short"]   # Kısa hareket süresini alır.
        move_duration_long = self.auto_move_config["move_duration_long"]     # Normal hareket süresini alır.
        default_safe_move_duration = self.auto_move_config["default_safe_move_duration"] # Varsayılan güvenli hareket süresini alır.

        # Arka sensör 999 (arıza/çok uzak) ise veya çok yakınsa (ultrasonik hata durumları)
        if rear_dist == 999:
            logger.warning(f"OTONOM KARAR: Arka sensörden geçersiz veri veya timeout (999). Varsayılan güvenli hareket: Yavaşça Geri.")
            # Eğer arka sensör çalışmıyorsa veya çok uzak bir değer dönüyorsa (999),
            # robotun tamamen durması yerine yavaşça geri gitmesini sağlayalım.
            # Ancak önünde de engel varsa ileri-sağa dönsün.
            if front_dist < rear_obstacle_threshold: # Önünde engel varsa (arka sensör yok sayıldı).
                logger.warning(f"OTONOM KARAR: Arka sensör arızalı, önde engel ({front_dist} cm). İleri-Sağ kaçınma.")
                self.send_motor("ileri") # İleri git.
                time.sleep(move_duration_short) # Kısa süre bekle.
                self.send_motor("sag") # Sağa dön.
                time.sleep(turn_duration) # Dönüş süresi kadar bekle.
            else: # Önü açıksa veya ön sensör de arızalıysa, genel olarak geri git.
                self.send_motor("geri") # Geriye doğru ilerle.
                time.sleep(default_safe_move_duration) # Varsayılan güvenli hareket süresi kadar bekle.
        elif rear_dist < rear_obstacle_threshold:
            # Arka tarafta engel algılandıysa (eşikten küçükse), kaçınma hareketi yapar.
            logger.warning(f"OTONOM KARAR: Arkada engel algılandı ({rear_dist} cm). Kaçınma hareketi.")
            self.send_motor("ileri") # İleri git.
            time.sleep(move_duration_short) # Kısa süre bekle.
            self.send_motor("sag") # Sağa dön.
            time.sleep(turn_duration) # Dönüş süresi kadar bekle.
            self.send_motor("dur") # Dur.
            
        elif rear_dist >= rear_clear_threshold:
            # Arka yol açık ise, varsayılan hareket: Geriye doğru ilerle.
            logger.info(f"OTONOM KARAR: Arka yol açık ({rear_dist} cm). Geriye doğru ilerle.")
            self.send_motor("geri") # Geriye doğru ilerle.
            if not is_navigating: # Eğer navigasyon modunda değilse (süre yönetimini ana mantık yapar).
                time.sleep(move_duration_long) # Uzun hareket süresi kadar bekle.
        else:
            # Arka mesafe belirsiz veya eşiğe yakınsa, durur.
            logger.info(f"OTONOM KARAR: Arka mesafe belirsiz veya eşiğe yakın ({rear_dist} cm). Dur.")
            self.send_motor("dur") # Dur.
            time.sleep(move_duration_short) # Kısa süre bekle.

        self.send_motor("dur") # Hareket tamamlandığında motorları durdurur.

    def perform_navigation_step(self):
        # Bu fonksiyon, GPS navigasyon adımlarını yürütür.
        # Ancak, mevcut yapılandırmada su seviyesi önceliği devre dışı bırakıldığı için,
        # bu fonksiyon ana 'handle_logic' döngüsünden otomatik olarak çağrılmaz.
        # Sadece UI'daki 'nav-distance' gibi alanlar için hesaplamalar yapar.
        logger.debug("NAV: perform_navigation_step çağrıldı ancak su seviyesi önceliği devre dışı.")
        if not self.gps_location or self.gps_location.get("lat") is None:
            # Mevcut GPS konumu yoksa navigasyonu duraklatır.
            logger.warning("NAV: Mevcut GPS konumu yok, navigasyon duraklatıldı.")
            self.send_motor("dur")
            self.last_error_message = "NAV: Mevcut GPS konumu yok."
            return

        if self.target_gps_location.get("lat") is None:
            # Hedef GPS konumu ayarlanmamışsa navigasyonu durdurur.
            logger.warning("NAV: Hedef GPS konumu ayarlanmamış.")
            self.navigation_active = False
            self.send_motor("dur")
            return

        current_lat = self.gps_location["lat"] # Mevcut enlemi alır.
        current_lon = self.gps_location["lon"] # Mevcut boylamı alır.
        target_lat = self.target_gps_location["lat"] # Hedef enlemi alır.
        target_lon = self.target_gps_location["lon"] # Hedef boylamı alır.

        self.distance_to_target = self._haversine(current_lat, current_lon, target_lat, target_lon) # Hedefe olan mesafeyi hesaplar.
        self.bearing_to_target = self._calculate_bearing(current_lat, current_lon, target_lat, target_lon) # Hedefe olan yönü hesaplar.

        logger.debug(f"NAV DURUM: Stage: {self.navigation_stage}, Hedef: {target_lat:.4f},{target_lon:.4f}, Mevcut: {current_lat:.4f},{current_lon:.4f} Uzaklık: {self.distance_to_target:.2f}m, Yön (Bilgi): {self.bearing_to_target:.1f}°")

        # Hedefe yaklaşıldıysa (eşik değerinin altına inildiyse).
        if self.distance_to_target < self.nav_config['target_reached_threshold_meters']:
            logger.info(f"NAV: Hedefe ulaşıldı ({self.distance_to_target:.2f}m). Su boşaltma aşamasına geçiliyor (şu an devre dışı).")
            self.navigation_stage = "DISCHARGING_WATER" # UI için aşamayı günceller.
            self.send_motor("dur") # Robotu durdurur.
            return

        self.navigation_stage = "NAVIGATING" # Navigasyon aşamasını 'NAVIGATING' olarak ayarlar.
        rear_dist = self.distances.get("rear", 999) # Arka mesafe bilgisini alır.

        # Navigasyon sırasında engelden kaçınma veya ilerleme mantığı (şu an aktif değil, sadece bilgi olarak duruyor).
        if rear_dist < self.nav_config['obstacle_threshold_nav_cm']:
            logger.info(f"NAV: Arkada engel var ({rear_dist}cm < {self.nav_config['obstacle_threshold_nav_cm']}cm). (Navigasyon modunda değil.)")
            # self._execute_autonomous_decision(is_navigating=True) # Bu çağrı artık handle_logic'te yapılacak
        else: 
            logger.info(f"NAV: Yol açık ({rear_dist}cm). (Navigasyon modunda değil.)") 
            # self.send_motor("geri") # Bu çağrı artık handle_logic'te yapılacak

    def handle_logic(self):
        # Robotun ana otonom mantık döngüsünü yürütür.
        logger.info("Ana mantık döngüsü başlatıldı.")
        while self.running: # Program çalıştığı sürece döngüye devam et.
            try:
                # 1. MANUEL KONTROL ÖNCELİKLİ
                if self.manual_override_active:
                    time.sleep(0.1) # Manuel kontrol aktifken CPU'yu boşuna yormamak için kısa bir bekleme.
                    continue # Döngünün başına dön, otonom mantığı atla.

                # 2. DEPONUN ÖNEMİNİ KALDIRDIK:
                # Depo seviyesi kontrolü kaldırıldığı için, robot doğrudan genel otonom hareket moduna geçer.
                logger.debug("OTOMASYON: Depo önceliği kaldırıldı. Genel otonom hareket başlatılıyor.")
                self._execute_autonomous_decision(is_navigating=False) # Otonom hareket kararını yürütür.
                time.sleep(0.3) # Otonom hareket adımları arasında kısa bir bekleme süresi.
                
                # GPS navigasyonu ve pompa kontrolü mantığı artık ana loop'ta otomatik olarak tetiklenmiyor.
                # Sadece eğer manuel olarak tetiklenirse veya eski kodda olduğu gibi GPS hedefi ayarlanırsa 
                # (ancak otomatik navigasyon başlama koşulları yok) çalışır.
                # UI'daki GPS hedefi ayarlandığında sadece hedef bilgisi güncellenir,
                # robot otomatik olarak hedefe gitmez.
                
            except Exception as e:
                # Ana mantık döngüsünde beklenmeyen bir hata oluşursa.
                logger.error(f"[LOOP HATASI] Ana mantık döngüsünde beklenmeyen hata: {e}", exc_info=True)
                self.last_error_message = f"Ana mantık hatası: {str(e)[:100]}..." # UI'da gösterilecek hata mesajını günceller.
                self.send_motor("dur") # Robotu durdurur.
                time.sleep(2) # Hata durumunda 2 saniye bekler.

    def start(self):
        # Robot sistemini başlatan ana fonksiyon. Tüm iş parçacıklarını başlatır.
        logger.info("Robot sistemi başlatma süreci başladı: Thread'ler oluşturuluyor.")

        # Sensör verilerini güncelleyen iş parçacığını başlatır.
        sensor_thread = threading.Thread(target=self.update_sensors, name="SensorThread", daemon=True)
        sensor_thread.start()

        # Flask web uygulamasını başlatan iş parçacığını başlatır.
        # 'debug=False' ve 'use_reloader=False' üretim ortamında güvenli ve stabil çalışmayı sağlar.
        flask_thread = threading.Thread(target=lambda: app.run(host=config['app_host'], 
                                                                port=config['app_port'], 
                                                                debug=False, use_reloader=False), 
                                       name="FlaskThread", daemon=True)
        flask_thread.start()

        # Robotun ana otonom mantığını yürüten iş parçacığını başlatır.
        logic_thread = threading.Thread(target=self.handle_logic, name="LogicThread", daemon=True)
        logic_thread.start()
        
        logger.info("Tüm thread'ler başlatıldı. Robot çalışıyor.")
        while self.running:
            time.sleep(1) # Ana thread'in kapanmasını engellemek için 1 saniye aralıklarla bekle.

    def cleanup(self):
        # Program kapanırken robotun kaynaklarını serbest bırakan temizleme fonksiyonu.
        logger.info("Robot sistemi kapatılıyor...")
        self.running = False # Tüm döngülerin durmasını sağlar.
        if self.manual_override_timer:
            self.manual_override_timer.cancel() # Manuel kontrol zamanlayıcısını iptal eder.
        
        # Motor seri portunu kapatır ve robotu durdurur.
        if self.motor_serial and self.motor_serial.is_open:
            try: self.send_motor("dur") # Robotu durdurmaya çalışır.
            except: pass # Hata olursa yoksay.
            self.motor_serial.close() # Seri portu kapatır.
            logger.info("Motor seri portu kapatıldı.")
        
        # Sensör seri portunu kapatır.
        if self.sensor_serial and self.sensor_serial.is_open:
            self.sensor_serial.close()
            logger.info("Sensör seri portu kapatıldı.")
        
        # Pompa seri portunu kapatır ve pompaları kapatır.
        if self.pump_serial and self.pump_serial.is_open:
            try: 
                self.send_pump("IN", "OFF") # IN pompasını kapatır.
                self.send_pump("OUT", "OFF") # OUT pompasını kapatır.
            except: pass # Hata olursa yoksay.
            self.pump_serial.close()
            logger.info("Pompa seri portu kapatıldı.")
        
        GPIO.cleanup() # GPIO pinlerini varsayılan durumlarına döndürür ve kaynakları serbest bırakır.
        logger.info("GPIO kaynakları serbest bırakıldı.")
        logger.info("Robot sistemi kapatma tamamlandı.")

# --- Flask Rotaları ---
# Bu bölüm, web arayüzüne gelen HTTP isteklerini işleyen Flask route fonksiyonlarını içerir.
robot_instance = None # Global robot_instance değişkeni (başlangıçta None).

@app.route('/')
def index():
    # Kök URL'e ('/') yapılan bir GET isteğine yanıt verir.
    # HTML içeriğini doğrudan bir dize olarak döndürür (Flask'ın render_template_string fonksiyonu ile).
    # Bu HTML, robotun durumunu gösteren ve kontrol düğmeleri içeren bir web paneli sağlar.
    html_content = """
    <!DOCTYPE html>
    <html lang="tr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Robot Durum ve Kontrol Paneli</title>
        <style>
            /* CSS stilleri burada yer alır. Sayfanın görünümünü, renklerini, düzenini vb. belirler. */
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f0f2f5; margin: 0; padding: 20px; display: flex; flex-direction: column; align-items: center; min-height: 100vh; }
            .logo-container { text-align: center; margin-bottom: 20px; }
            .logo-container img { max-width: 120px; height: auto; border-radius: 8px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
            .container { background-color: #ffffff; border-radius: 12px; box-shadow: 0 6px 20px rgba(0, 0, 0, 0.1); padding: 25px; width: 100%; max-width: 700px; box-sizing: border-box; margin-top: 10px; }
            h1 { color: #333; text-align: center; margin-bottom: 20px; font-size: 1.8em; }
            .data-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; margin-bottom: 25px; }
            .data-item { background-color: #e9f0f7; padding: 15px; border-radius: 8px; text-align: center; box-shadow: inset 0 1px 3px rgba(0,0,0,0.05); }
            .data-item strong { display: block; margin-bottom: 6px; color: #555; font-size: 1em; }
            .data-item span { font-size: 1.4em; font-weight: bold; color: #007bff; }
            .status-section p { font-size: 1em; color: #444; margin-bottom: 10px; }
            #motor-command { font-size: 1.5em; font-weight: bold; color: #28a745; text-transform: uppercase; }
            #error-message { color: red; font-weight: bold; margin-top: 15px; padding: 8px; border: 1px solid red; background-color: #ffe0e0; border-radius: 5px; display: none; }
            .loading { color: #888; }
            .control-section, .nav-section, .pump-section { text-align: center; margin-top: 25px; padding-top: 15px; border-top: 1px solid #eee; }
            .control-section h2, .nav-section h2, .pump-section h2 { color: #333; margin-bottom: 15px; font-size: 1.3em; }
            .control-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; max-width: 280px; margin: 0 auto 15px auto; }
            .control-button, .action-button {
                padding: 12px; font-size: 1em; font-weight: bold; border: none; border-radius: 8px; cursor: pointer;
                background-color: #007bff; color: white; transition: background-color 0.2s ease; box-shadow: 0 3px 6px rgba(0,0,0,0.1);
            }
            .control-button:hover, .action-button:hover { background-color: #0056b3; }
            .control-button.stop { background-color: #dc3545; }
            .control-button.stop:hover { background-color: #c82333; }
            .control-button.empty { visibility: hidden; }
            .pump-controls button { margin: 5px; background-color: #17a2b8; }
            .pump-controls button:hover { background-color: #117a8b; }
            .manual-status { margin-top: 8px; font-weight: bold; font-size: 1em; }
            .system-status, .nav-status-display { font-size: 0.9em; color: #666; margin-top: 15px; }
            .system-status div, .nav-status-display div { margin-bottom: 4px; }
            #nav-status-text { font-weight: bold; }
            .active-nav { color: #28a745; }
            .idle-nav { color: #6c757d; }
            .water-status { margin-top: 10px; font-size: 0.9em; color: #333;}
            .water-status strong {color: #17a2b8;}
        </style>
    </head>
    <body>
        <div id="splash-screen" style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; z-index: 9999; background-color: black; display: flex; justify-content: center; align-items: center;">
            <video id="splash-video" width="80%" height="80%" autoplay muted playsinline>
                <source src="/static/1.mp4" type="video/mp4">
                Tarayıcınız video etiketini desteklemiyor.
            </video>
        </div>
        <script>
            // Açılış videosunu (splash screen) yöneten JavaScript kodu.
            const splashVideo = document.getElementById("splash-video");
            const splashScreen = document.getElementById("splash-screen");
            if (splashVideo && splashScreen) {
                // Video bittiğinde splash ekranı gizle.
                splashVideo.onended = () => { splashScreen.style.display = "none"; };
                // 5 saniye içinde video bitmezse yine de splash ekranı gizle (güvenlik önlemi).
                setTimeout(() => { 
                    if (splashScreen.style.display !== "none") splashScreen.style.display = "none"; 
                }, 5000); 
            } else {
                 // Video veya splash ekran elemanı yoksa, splash ekranı direkt gizle.
                 if(splashScreen) splashScreen.style.display = "none"; 
            }
        </script>

        <div class="logo-container">
            <img src="/static/1.png" alt="Robot Logosu">
        </div>
        <div class="container">
            <h1>Robot Durum ve Kontrol Paneli</h1>
            
            <div class="data-grid">
                <div class="data-item"><strong>Ön Mesafe</strong><span id="front-distance" class="loading">...</span></div>
                <div class="data-item"><strong>Arka Mesafe</strong><span id="rear-distance" class="loading">...</span></div>
                <div class="data-item"><strong>Su Seviyesi 1 (Tank)</strong><span id="water-level1" class="loading">...</span></div>
                <div class="data-item"><strong>Su Seviyesi 2 (Kaynak)</strong><span id="water-level2" class="loading">...</span></div>
                <div class="data-item"><strong>Anlık GPS</strong><span id="gps-coords" class="loading">...</span></div>
                <div class="data-item"><strong>Pompa IN Durumu</strong><span id="pump-in-status" class="loading">...</span></div>
            </div>


            <div class="status-section" style="text-align:center;">
                <p>Mevcut Motor Komutu: <span id="motor-command" class="loading">...</span></p>
                <p id="manual-status" class="manual-status"></p>
            </div>
            <div id="error-message"></div>

            <div class="nav-section">
                <h2>Otonom Navigasyon (GPS)</h2>
                <p class="water-status">Su seviyesi önceliği devre dışı bırakıldı. Robot şu an sadece arka sensör verisine göre otonom hareket edecektir. Aşağıdaki hedef ayarlansa bile, robot otomatik olarak buraya gitmeyecektir.</p>
                <div class="nav-inputs">
                    <input type="number" id="target-lat" step="any" placeholder="Hedef Enlem (örn: 40.7128)">
                    <input type="number" id="target-lon" step="any" placeholder="Hedef Boylam (örn: -74.0060)">
                    <button class="action-button" onclick="setNavigationTarget()">Hedefi AYARLA</button> </div>
                <div class="nav-status-display">
                    <div>Navigasyon Durumu: <span id="nav-status-text" class="idle-nav">Pasif</span></div>
                    <div>Ayarlanan Hedef: <span id="nav-target-coords">Ayarlanmadı</span></div>
                    <div>Hedefe Mesafe: <span id="nav-distance">--</span> m</div>
                    <div>Aşama: <span id="nav-stage">--</span></div>
                </div>
            </div>

            <div class="control-section">
                <h2>Manuel Hareket Kontrolü</h2>
                <div class="control-grid">
                    <button class="control-button empty"></button>
                    <button class="control-button" onclick="sendMotionCommand('ileri')">İleri</button>
                    <button class="control-button empty"></button>
                    <button class="control-button" onclick="sendMotionCommand('sol')">Sol</button>
                    <button class="control-button stop" onclick="sendMotionCommand('dur')">DUR</button>
                    <button class="control-button" onclick="sendMotionCommand('sag')">Sağ</button>
                    <button class="control-button empty"></button>
                    <button class="control-button" onclick="sendMotionCommand('geri')">Geri</button>
                    <button class="control-button empty"></button>
                </div>
            </div>

            <div class="pump-section">
                <h2>Manuel Pompa Kontrolü</h2>
                <div class="pump-controls">
                    <button class="action-button" onclick="sendPumpCommand('IN', 'ON')">Suyu Çek (AÇ)</button>
                    <button class="action-button" onclick="sendPumpCommand('IN', 'OFF')">Suyu Çek (KAPAT)</button>
                    <br>
                    <button class="action-button" onclick="sendPumpCommand('OUT', 'ON')">Suyu Boşalt (AÇ)</button>
                    <button class="action-button" onclick="sendPumpCommand('OUT', 'OFF')">Suyu Boşalt (KAPAT)</button>
                </div>
            </div>

            <div class="system-status">
                <h3>Sistem Kaynakları</h3>
                <div>CPU: <span id="cpu-usage">...</span>%</div>
                <div>RAM: <span id="ram-usage">...</span>%</div>
                <div>Disk: <span id="disk-usage">...</span>%</div>
            </div>
        </div>

        <script>
            // JavaScript kodu: Web arayüzünün dinamik işlevselliğini sağlar.
            function fetchData() {
                // Sunucudan (Flask uygulaması) güncel robot verilerini çeker.
                fetch('/data')
                    .then(response => response.json()) // Yanıtı JSON olarak ayrıştırır.
                    .then(data => {
                        // Gelen verileri HTML elemanlarına yerleştirerek UI'ı günceller.
                        document.getElementById('front-distance').innerText = data.distances.front !== 999 ? data.distances.front + ' cm' : 'N/A';
                        document.getElementById('rear-distance').innerText = data.distances.rear !== 999 ? data.distances.rear + ' cm' : 'N/A';
                        document.getElementById('water-level1').innerText = data.sensor_data.water1 !== undefined ? data.sensor_data.water1 : 'Yok';
                        document.getElementById('water-level2').innerText = data.sensor_data.water2 !== undefined ? data.sensor_data.water2 : 'Yok';
                        document.getElementById('pump-in-status').innerText = data.pump_in_state || 'Bilinmiyor';

                        let gps_text = 'Yok';
                        if (data.gps_location && data.gps_location.lat && data.gps_location.lon) {
                            gps_text = `${parseFloat(data.gps_location.lat).toFixed(5)}, ${parseFloat(data.gps_location.lon).toFixed(5)}`;
                        }
                        document.getElementById('gps-coords').innerText = gps_text;
                        
                        document.getElementById('motor-command').innerText = data.current_motor_command.toUpperCase();
                        
                        const manualStatusElement = document.getElementById('manual-status');
                        if (data.manual_override_active) {
                            manualStatusElement.innerText = 'Manuel Kontrol Aktif!';
                            manualStatusElement.style.color = '#dc3545';
                        } else { 
                            manualStatusElement.innerText = 'Genel Otonom Mod (Arka Sensör Odaklı)';
                            manualStatusElement.style.color = '#28a745';
                        }

                        document.getElementById('cpu-usage').innerText = data.system_info.cpu_percent !== undefined ? data.system_info.cpu_percent.toFixed(1) + '%' : 'N/A';
                        document.getElementById('ram-usage').innerText = data.system_info.ram_percent !== undefined ? data.system_info.ram_percent.toFixed(1) + '%' : 'N/A';
                        document.getElementById('disk-usage').innerText = data.system_info.disk_percent !== undefined ? data.system_info.disk_percent.toFixed(1) + '%' : 'N/A';

                        const navStatusEl = document.getElementById('nav-status-text');
                        if(data.navigation_active && data.target_gps_location.lat !== null){
                            navStatusEl.textContent = "Aktif (Hedef Ayarlandı)";
                            navStatusEl.className = "active-nav";
                        } else {
                            navStatusEl.textContent = "Pasif";
                            navStatusEl.className = "idle-nav";
                        }
                        document.getElementById('nav-target-coords').textContent = data.target_gps_location.lat !== null ? `${parseFloat(data.target_gps_location.lat).toFixed(5)}, ${parseFloat(data.target_gps_location.lon).toFixed(5)}` : 'Ayarlanmadı';
                        document.getElementById('nav-distance').textContent = data.navigation_active && data.distance_to_target !== undefined ? data.distance_to_target.toFixed(2) + ' m' : '--';
                        document.getElementById('nav-stage').textContent = data.navigation_stage || '--';
                        
                        const errorMessageElement = document.getElementById('error-message');
                        if (data.last_error_message) {
                            errorMessageElement.innerText = data.last_error_message;
                            errorMessageElement.style.display = 'block';
                        } else {
                            errorMessageElement.style.display = 'none';
                        }
                    })
                    .catch(error => {
                        // Veri çekme hatası oluşursa konsola yazar ve UI'da hata mesajı gösterir.
                        console.error('Veri çekme hatası:', error);
                        const errorMessageElement = document.getElementById('error-message');
                        errorMessageElement.innerText = 'Hata: Robot verileri alınamıyor.';
                        errorMessageElement.style.display = 'block';
                    });
            }

            function sendMotionCommand(command) {
                // Motor kontrol komutlarını sunucuya gönderir.
                fetch('/control_motion', { 
                    method: 'POST', // POST isteği kullanır.
                    headers: {'Content-Type': 'application/json'}, // JSON veri gönderdiğini belirtir.
                    body: JSON.stringify({ 'command': command }) // Komutu JSON formatında gönderir.
                })
                .then(handleResponse) // Yanıtı işler.
                .catch(handleError); // Hataları işler.
            }

            function setNavigationTarget() {
                // Navigasyon hedefi GPS koordinatlarını sunucuya gönderir.
                const lat = document.getElementById('target-lat').value;
                const lon = document.getElementById('target-lon').value;
                if (!lat || !lon) {
                    alert('Lütfen geçerli enlem ve boylam girin.');
                    return;
                }
                fetch('/set_target', { 
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ 'lat': parseFloat(lat), 'lon': parseFloat(lon) }) 
                })
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        alert('Boşaltma hedefi başarıyla ayarlandı! Robot otomatik gitmeyecektir.');
                        fetchData(); 
                    } else {
                        alert('Hedef ayarlanamadı: ' + data.message);
                    }
                })
                .catch(handleError);
            }

            function sendPumpCommand(pumpId, state) {
                // Pompa kontrol komutlarını sunucuya gönderir.
                fetch('/control_pump', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ 'pump_id': pumpId, 'state': state })
                })
                .then(handleResponse)
                .catch(handleError);
            }
            
            function handleResponse(response) { 
                // Sunucudan gelen genel yanıtları işler.
                response.json().then(data => {
                    if (data.status === 'success') {
                        console.log('Komut başarılı:', data.message);
                        const errorMessageElement = document.getElementById('error-message');
                        if(errorMessageElement.innerText.startsWith('Komut gönderilemedi') || errorMessageElement.innerText.startsWith('Ağ hatası')) {
                             errorMessageElement.style.display = 'none';
                             errorMessageElement.innerText = '';
                        }
                         fetchData(); 
                    } else {
                        console.error('Komut hatası:', data.message);
                        displayError('Komut hatası: ' + data.message);
                    }
                }).catch(err => { 
                    console.error('Yanıt parse edilemedi:', err);
                    displayError('Sunucudan geçersiz yanıt alındı.');
                });
            }

            function handleError(error) {
                // Ağ veya diğer hataları işler ve UI'da gösterir.
                console.error('Network hatası:', error);
                displayError('Ağ hatası: Komut gönderilemedi. Sunucuya ulaşılamıyor.');
            }

            function displayError(message) {
                // UI'da hata mesajını gösterir.
                const errorMessageElement = document.getElementById('error-message');
                errorMessageElement.innerText = message;
                errorMessageElement.style.display = 'block';
            }

            setInterval(fetchData, 1000); // Her 1 saniyede bir 'fetchData' fonksiyonunu çağırır (UI'ı günceller).
            fetchData(); // Sayfa yüklendiğinde hemen ilk veri çekme işlemini başlatır.
        </script>
    </body>
    </html>
    """
    return render_template_string(html_content) # Oluşturulan HTML'i tarayıcıya gönderir.

@app.route('/data')
def get_data():
    # '/data' URL'ine yapılan bir GET isteğine yanıt verir.
    # Robotun mevcut durum verilerini JSON formatında döndürür.
    if robot_instance: # Eğer robot nesnesi oluşturulmuşsa.
        data = {
            "sensor_data": robot_instance.sensor_data, # Su seviyesi ve diğer sensör verileri.
            "distances": robot_instance.distances,     # Ultrasonik mesafe verileri.
            "gps_location": robot_instance.gps_location, # GPS konumu.
            "current_motor_command": robot_instance.current_motor_command, # Mevcut motor komutu.
            "manual_override_active": robot_instance.manual_override_active, # Manuel kontrol aktif mi?
            "system_info": robot_instance.system_info,     # Sistem kaynak bilgileri.
            "last_error_message": robot_instance.last_error_message, # Son hata mesajı.
            "navigation_active": robot_instance.navigation_active,     # Navigasyon aktif mi?
            "target_gps_location": robot_instance.target_gps_location, # Hedef GPS konumu.
            "distance_to_target": robot_instance.distance_to_target,   # Hedefe olan mesafe.
            "bearing_to_target": robot_instance.bearing_to_target,     # Hedefe olan yön.
            "navigation_stage": robot_instance.navigation_stage,       # Navigasyon aşaması.
            "pump_in_state": robot_instance.pump_in_state,             # IN pompasının durumu.
            "pump_out_state": robot_instance.pump_out_state,           # OUT pompasının durumu.
            "water_config": robot_instance.water_config                # Su seviyesi yapılandırması.
        }
        return jsonify(data) # Verileri JSON olarak döndürür.
    return jsonify({"error": "Robot sistemi başlatılmadı"}), 503 # Robot başlatılmamışsa hata döndürür.

@app.route('/control_motion', methods=['POST'])
def handle_motion_control_command(): 
    # '/control_motion' URL'ine gelen POST isteklerini işler (motor komutları).
    if not robot_instance:
        return jsonify({"status": "error", "message": "Robot sistemi başlatılmadı"}), 503 # Robot başlatılmamışsa hata döndürür.
    
    data = request.get_json() # Gelen JSON verilerini alır.
    command = data.get('command') # 'command' alanındaki değeri alır.

    if command in ["ileri", "geri", "sol", "sag", "dur"]: # Geçerli komutları kontrol eder.
        robot_instance.set_manual_override(True) # Manuel kontrolü aktif eder.
        robot_instance.send_motor(command) # Motor komutunu robot sistemine gönderir.
        return jsonify({"status": "success", "message": f"Hareket komutu alındı: {command}"}) # Başarı yanıtı döndürür.
    else:
        return jsonify({"status": "error", "message": "Geçersiz hareket komutu"}), 400 # Geçersiz komutta hata döndürür.

@app.route('/set_target', methods=['POST'])
def set_target():
    # '/set_target' URL'ine gelen POST isteklerini işler (GPS hedefi ayarlama).
    if not robot_instance:
        return jsonify({"status": "error", "message": "Robot sistemi başlatılmadı"}), 503 # Robot başlatılmamışsa hata döndürür.
    data = request.get_json() # Gelen JSON verilerini alır.
    lat = data.get('lat') # Enlem bilgisini alır.
    lon = data.get('lon') # Boylam bilgisini alır.

    if lat is not None and lon is not None: # Enlem ve boylam varsa.
        robot_instance.target_gps_location = {"lat": float(lat), "lon": float(lon)} # Hedef koordinatları günceller.
        robot_instance.navigation_active = True # Navigasyonu aktif olarak işaretler.
        robot_instance.navigation_stage = "IDLE" # Navigasyon aşamasını boşta olarak ayarlar (otomatik tetiklenmez).
        logger.info(f"NAV: Boşaltma hedefi güncellendi: {robot_instance.target_gps_location}. NOT: Depo boşverildiği için navigasyon şu an tetiklenmeyecek.")
        robot_instance.last_error_message = "" # Hata mesajını temizler.
        
        return jsonify({"status": "success", "message": f"Boşaltma hedefi ayarlandı: {lat}, {lon}. Robot otomatik gitmeyecektir."}) # Başarı yanıtı döndürür.
    return jsonify({"status": "error", "message": "Eksik koordinat bilgisi"}), 400 # Eksik bilgi varsa hata döndürür.

@app.route('/control_pump', methods=['POST'])
def handle_pump_control_command():
    # '/control_pump' URL'ine gelen POST isteklerini işler (pompa komutları).
    if not robot_instance:
        return jsonify({"status": "error", "message": "Robot sistemi başlatılmadı"}), 503 # Robot başlatılmamışsa hata döndürür.
    
    data = request.get_json() # Gelen JSON verilerini alır.
    pump_id = data.get('pump_id') # Pompa ID'sini alır (IN/OUT).
    state = data.get('state')     # Pompa durumunu alır (ON/OFF).

    if pump_id in ["IN", "OUT"] and state in ["ON", "OFF"]: # Geçerli pompa ID'si ve durumu kontrol eder.
        robot_instance.send_pump(pump_id, state) # Pompa komutunu robot sistemine gönderir.
        return jsonify({"status": "success", "message": f"Pompa {pump_id} komutu: {state}"}) # Başarı yanıtı döndürür.
    else:
        return jsonify({"status": "error", "message": "Geçersiz pompa komutu"}), 400 # Geçersiz komutta hata döndürür.


if __name__ == "__main__":
    # Bu blok, betik doğrudan çalıştırıldığında (import edildiğinde değil) yürütülür.
    robot = None # Robot nesnesini başlangıçta None olarak ayarlar.
    try:
        robot = RobotSystem() # Bir RobotSystem nesnesi oluşturur.
        robot.start() # Robot sistemini başlatır (thread'leri çalıştırır).
    except KeyboardInterrupt:
        logger.info("\n[!] Kullanıcı tarafından durduruldu (Ctrl+C).") # Kullanıcı Ctrl+C ile çıkarsa loglar.
    except Exception as e:
        logger.critical(f"Ana programda KRİTİK HATA: {e}", exc_info=True) # Diğer kritik hataları loglar.
    finally:
        if robot:
            robot.cleanup() # Program sonlandığında temizleme fonksiyonunu çağırır.
        logger.info("Program sonlandırıldı.") # Programın sonlandığını loglar.

#This code belongs to datadevelopers RPIv5  so this code is copyright 