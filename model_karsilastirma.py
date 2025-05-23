import pickle
import os
import numpy as np
from sklearn.model_selection import learning_curve, train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import GaussianNB
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    accuracy_score,
    auc,
    classification_report,
    confusion_matrix,
    roc_curve,
)
from sklearn.svm import SVC
import librosa
import matplotlib.pyplot as plt

# Özellik çıkarma fonksiyonu
def load_data():
    DATA_PATH = "C:\\Users\\ASUS\\OneDrive\\Masaüstü\\veri_seti\\"
    features = []
    labels = []
    for emotion_folder in os.listdir(DATA_PATH):
        emotion_path = os.path.join(DATA_PATH, emotion_folder)
        if os.path.isdir(emotion_path):
            for file in os.listdir(emotion_path):
                if file.endswith(".wav"):
                    file_path = os.path.join(emotion_path, file)
                    audio, sr = librosa.load(file_path, sr=22050)
                    mfccs = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=13)
                    features.append(np.mean(mfccs.T, axis=0))
                    labels.append(emotion_folder)
    return np.array(features), np.array(labels)

# Veriyi yükle ve böl
X, y = load_data()
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Modeller
models = {
    "Logistic Regression": LogisticRegression(max_iter=1000),
    "Naive Bayes": GaussianNB(),
    "SVM": SVC(kernel="linear", probability=True),  # SVM için probability=True
}

# Her modelin doğruluk oranını hesapla
for name, model in models.items():
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"{name} Modeli Doğruluğu: {accuracy:.2f}")

# Confusion Matrix
for name, model in models.items():
    y_pred = model.predict(X_test)
    cm = confusion_matrix(y_test, y_pred)
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=np.unique(y))
    disp.plot(cmap=plt.cm.Blues)
    plt.title(f"{name} - Confusion Matrix")
    plt.show()

# ROC-AUC Grafiği
for name, model in models.items():
    if hasattr(model, "predict_proba"):
        y_prob = model.predict_proba(X_test)
    else:
        y_prob = model.decision_function(X_test)
        y_prob = np.expand_dims(y_prob, axis=1)

    fpr, tpr, _ = roc_curve(y_test, y_prob[:, 0], pos_label=1)
    roc_auc = auc(fpr, tpr)

    plt.figure()
    plt.plot(fpr, tpr, color="darkorange", lw=2, label=f"ROC curve (area = {roc_auc:.2f})")
    plt.plot([0, 1], [0, 1], color="navy", lw=2, linestyle="--")
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.title(f"{name} - ROC Curve")
    plt.legend(loc="lower right")
    plt.show()

# Precision, Recall, F1 Score
for name, model in models.items():
    y_pred = model.predict(X_test)
    report = classification_report(y_test, y_pred, target_names=np.unique(y))
    print(f"{name} - Classification Report:")
    print(report)

# Learning Curve
for name, model in models.items():
    train_sizes, train_scores, test_scores = learning_curve(model, X_train, y_train, cv=5)
    train_mean = np.mean(train_scores, axis=1)
    test_mean = np.mean(test_scores, axis=1)

    plt.plot(train_sizes, train_mean, label="Training Score")
    plt.plot(train_sizes, test_mean, label="Validation Score")
    plt.title(f"{name} - Learning Curve")
    plt.xlabel("Training Set Size")
    plt.ylabel("Accuracy")
    plt.legend()
    plt.show()
