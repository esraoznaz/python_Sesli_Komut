import pickle
import numpy as np
import librosa

# Model dosyalarını yükleyin
with open("model.pkl", "rb") as model_file:
    model = pickle.load(model_file)

with open("label_encoder.pkl", "rb") as encoder_file:
    label_encoder = pickle.load(encoder_file)

# Ses dosyasından özellik çıkarımı
def extract_features(file_path):
    audio, sr = librosa.load(file_path, sr=22050)  # Ses dosyasını yükle
    mfccs = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=13)  # MFCC özelliklerini çıkar
    return np.mean(mfccs.T, axis=0)  # MFCC'nin ortalama değerlerini al

# Duygu analizi fonksiyonu
def analyze_emotion(file_path):
    features = extract_features(file_path)  # Özellikleri çıkar
    prediction = model.predict([features])  # Modeli kullanarak tahmin yap
    emotion = label_encoder.inverse_transform(prediction)[0]  # Tahmin edilen etiketi duyguya çevir
    return emotion  # Duygu sonucunu döndür
