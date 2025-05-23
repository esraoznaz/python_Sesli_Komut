import os
import librosa
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.svm import SVC
import pickle

# Verilerin bulunduğu klasörlerin yolu
DATA_PATH = "C:\\Users\\ASUS\\OneDrive\\Masaüstü\\veri_seti\\"  # Örneğin: veri_kaynaklari/mutlu, veri_kaynaklari/sinirli

# Özellik çıkarma fonksiyonu
def extract_features(file_path):
    audio, sr = librosa.load(file_path, sr=22050)
    mfccs = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=13)
    return np.mean(mfccs.T, axis=0)

# Tüm verileri yükleme ve özellik çıkarma
def load_data(data_path):
    features = []
    labels = []
    for emotion_folder in os.listdir(data_path):
        emotion_path = os.path.join(data_path, emotion_folder)
        if os.path.isdir(emotion_path):
            for file in os.listdir(emotion_path):
                if file.endswith(".wav"):
                    file_path = os.path.join(emotion_path, file)
                    mfccs = extract_features(file_path)
                    features.append(mfccs)
                    labels.append(emotion_folder)
    return np.array(features), np.array(labels)

# Veriyi yükle
X, y = load_data(DATA_PATH)

# Verileri encode et
label_encoder = LabelEncoder()
y_encoded = label_encoder.fit_transform(y)

# Verileri eğitim ve test setlerine ayır
X_train, X_test, y_train, y_test = train_test_split(X, y_encoded, test_size=0.2, random_state=42)

# Modeli eğit
model = SVC(kernel="linear", probability=True)
model.fit(X_train, y_train)

# Model doğruluğunu hesapla
accuracy = model.score(X_test, y_test)
print(f"Model doğruluğu: {accuracy:.2f}")

# 📦 Modeli kaydet
with open("model.pkl", "wb") as model_file:
    pickle.dump(model, model_file)

# 📦 Label encoder'ı kaydet
with open("label_encoder.pkl", "wb") as encoder_file:
    pickle.dump(label_encoder, encoder_file)

print("Model ve label encoder başarıyla kaydedildi.")
