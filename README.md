# EyeTracker

**Système d'eye-tracking pour l'enregistrement de sessions longues avec webcam**

Ce projet est basé sur la bibliothèque [GazeFollower](https://github.com/GanchengZhu/GazeFollower), un système d'eye-tracking open-source utilisant des réseaux de neurones profonds pour le suivi du regard via webcam.

## 📋 Prérequis

- **Python 3.10.4** (testé et recommandé)
- **Webcam** fonctionnelle
- **Système d'exploitation:** Windows (les utilisateurs Linux sauront adapter les commandes)

---

## 🚀 Installation (Windows)

### 1. Installer Python 3.10.4

1. Télécharger Python 3.10.4 depuis : https://www.python.org/downloads/windows/
2. **Important:** Cocher "Add Python to PATH" durant l'installation
3. Vérifier l'installation :
   ```bash
   python --version
   ```

### 2. Cloner le projet

```bash
git clone <URL_DU_PROJET> EyeTracker
cd EyeTracker
```

### 3. Créer l'environnement virtuel

```bash
py -3.10 -m venv .venv
```

### 4. Activer l'environnement virtuel

```bash
.\.venv\Scripts\activate
```

### 5. Installer les dépendances

```bash
pip install MNN numpy opencv-python pandas pygame screeninfo
pip install mediapipe==0.10.9
```

---

## ▶️ Utilisation

### Lancer l'application

```bash
# Activer l'environnement virtuel (si pas déjà fait)
.\.venv\Scripts\activate

# Lancer l'eye tracker
python eye_tracker.py
```

### Workflow de l'application

1. **Calibration automatique** au lancement
2. **Enregistrement** avec suivi du regard en temps réel
3. **Sauvegarde automatique** à l'arrêt :
   - Fichier CSV avec les données de tracking
   - Images périodiques (1 toutes les 2 secondes)
   - Statistiques de session dans la console

### Structure des données sauvegardées

```
nom_session/
├── nom_session.csv          # Données de tracking (timestamp, position regard, etc.)
└── images/                   # Captures d'écran périodiques
    ├── 0001.jpg
    ├── 0002.jpg
    └── ...
```

---

## 📊 Données enregistrées

Le fichier CSV contient pour chaque échantillon :
- **timestamp** : Horodatage
- **gaze_x, gaze_y** : Position du regard à l'écran
- **status** : État du tracking (actif/perdu)
- **looking_at_screen** : Indique si l'utilisateur regarde l'écran
- **tracking_lost** : Marqueur de perte de tracking

Les images sont sauvegardées toutes les 2 secondes pour une référence visuelle.

---

## 🎯 Caractéristiques

- ✅ **Calibration automatique** avec score de qualité
- ✅ **Enregistrement longue durée** (testé sur 2h+)
- ✅ **Capture continue** même en cas de perte de tracking
- ✅ **Sauvegarde automatique** des données et images
- ✅ **Interface moderne** avec affichage temps réel
- ✅ **Statistiques détaillées** en fin de session

---

## 📝 Notes

- **Sessions longues :** Le système est optimisé pour des sessions de 1 à 2 heures
- **Fréquence d'images :** 1 image toutes les 2 secondes (~1800 images/heure)
- **Format d'images :** JPEG avec qualité 85% pour optimiser l'espace disque

---

## 🔗 Crédits

Ce projet utilise **GazeFollower** développé par Gancheng Zhu et son équipe :

```bibtex
@article{zhu2025gazefollower,
  title={GazeFollower: An open-source system for deep learning-based gaze tracking with web cameras},
  author={Zhu, Gancheng and Duan, Xiaoting and Huang, Zehao and Wang, Rong and Zhang, Shuai and Wang, Zhiguo},
  journal={Proceedings of the ACM on Computer Graphics and Interactive Techniques},
  volume={8},
  number={2},
  pages={1--18},
  year={2025},
  publisher={ACM New York, NY}
}
```

**Dépôt original :** https://github.com/GanchengZhu/GazeFollower

---

## 📄 Licence

Ce projet hérite de la licence de GazeFollower :
[Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0)](https://creativecommons.org/licenses/by-nc-sa/4.0/)

⚠️ **Usage non-commercial uniquement**
