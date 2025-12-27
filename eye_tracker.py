import pygame
import sys
from gazefollower import GazeFollower
from enum import Enum
import time
import csv
import cv2
import numpy as np
from PIL import Image
import os
from datetime import datetime


class AppState(Enum):
    IDLE = 0
    CALIBRATED = 1
    RECORDING = 2
    STOPPED = 3


class EyeTrackerApp:
    def __init__(self):
        pygame.init()

        # Initialisation de GazeFollower
        self.gaze_follower = GazeFollower()

        # Configuration de l'écran en plein écran
        screen_size = self.gaze_follower.screen_size.tolist()
        self.screen = pygame.display.set_mode(screen_size, pygame.FULLSCREEN)
        pygame.display.set_caption("Eye Tracker - Projet OraDys 3TT\nUniversité Paris 8 - Laboratoire Paragraphe")

        # État de l'application
        self.state = AppState.IDLE

        # Statistiques
        self.recording_start_time = None
        self.recording_end_time = None
        self.gaze_data = []
        self.session_name = ""

        # Sauvegarde d'images
        self.session_dir = None
        self.images_dir = None
        self.last_image_save_time = 0
        self.image_save_interval = 2.0  # Sauvegarder 1 image toutes les 2 secondes (~1800 images/heure)
        self.image_counter = 0

        # Debug: compteur de frames pour vérifier que le callback continue
        self.frame_count = 0
        self.last_frame_log_time = 0
        self.gaze_data_count = 0
        self.last_gaze_log_time = 0

        # Flag pour quitter l'application proprement
        self.should_quit = False

        # Dimensions de l'écran
        self.screen_width = screen_size[0]
        self.screen_height = screen_size[1]

        # Données de visualisation en temps réel
        self.current_frame = None
        self.current_gaze_x = None
        self.current_gaze_y = None

        # Score de calibration
        self.calibration_score = None
        self.calibration_quality = None

        # Interface - Polices
        self.font_title = pygame.font.Font(None, 64)
        self.font_large = pygame.font.Font(None, 48)
        self.font_medium = pygame.font.Font(None, 36)
        self.font_small = pygame.font.Font(None, 28)

        # Couleurs modernes
        self.BG_COLOR = (15, 23, 42)  # Bleu foncé moderne
        self.CARD_BG = (30, 41, 59)  # Gris-bleu pour les cartes
        self.ACCENT_PRIMARY = (59, 130, 246)  # Bleu vif
        self.ACCENT_SUCCESS = (34, 197, 94)  # Vert
        self.ACCENT_WARNING = (251, 146, 60)  # Orange
        self.ACCENT_DANGER = (239, 68, 68)  # Rouge
        self.TEXT_PRIMARY = (248, 250, 252)  # Blanc cassé
        self.TEXT_SECONDARY = (148, 163, 184)  # Gris clair
        self.BORDER_COLOR = (51, 65, 85)  # Bordure subtile

        # Boutons avec positions relatives
        self.setup_buttons()

    def setup_buttons(self):
        """Configure les positions des boutons"""
        button_width = 280
        button_height = 80
        button_spacing = 30
        center_x = self.screen_width // 2
        center_y = self.screen_height // 2

        # Bouton CALIBRER - centré horizontalement et verticalement (état IDLE)
        self.calibrate_button = pygame.Rect(
            center_x - button_width // 2,
            center_y - button_height // 2,
            button_width,
            button_height
        )

        # Boutons principaux (START/STOP) - centrés horizontalement
        self.start_button = pygame.Rect(
            center_x - button_width - button_spacing // 2,
            int(self.screen_height * 0.70),
            button_width,
            button_height
        )
        self.stop_button = pygame.Rect(
            center_x + button_spacing // 2,
            int(self.screen_height * 0.70),
            button_width,
            button_height
        )

        # Bouton recalibrer - centré
        self.recalibrate_button = pygame.Rect(
            center_x - button_width // 2,
            int(self.screen_height * 0.58),
            button_width,
            button_height
        )

        # Boutons fin de session - alignés
        self.new_session_same_calib_button = pygame.Rect(
            center_x - button_width - button_spacing // 2,
            int(self.screen_height * 0.72),
            button_width,
            button_height
        )
        self.new_session_new_calib_button = pygame.Rect(
            center_x + button_spacing // 2,
            int(self.screen_height * 0.72),
            button_width,
            button_height
        )
        self.quit_button = pygame.Rect(
            center_x - button_width // 2,
            int(self.screen_height * 0.85),
            button_width,
            button_height
        )

    def draw_rounded_rect(self, surface, color, rect, radius=15):
        """Dessine un rectangle avec coins arrondis"""
        pygame.draw.rect(surface, color, rect, border_radius=radius)

    def draw_button(self, rect, text, color, enabled=True, icon=None):
        """Dessine un bouton moderne avec effet hover"""
        if not enabled:
            color = self.BORDER_COLOR

        # Effet d'ombre
        shadow_rect = rect.copy()
        shadow_rect.y += 4
        self.draw_rounded_rect(self.screen, (0, 0, 0, 100), shadow_rect, 12)

        # Bouton principal
        self.draw_rounded_rect(self.screen, color, rect, 12)

        # Bordure
        pygame.draw.rect(self.screen, self.BORDER_COLOR if enabled else (80, 80, 80), rect, 2, border_radius=12)

        # Texte
        text_color = self.TEXT_PRIMARY if enabled else self.TEXT_SECONDARY
        text_surf = self.font_medium.render(text, True, text_color)
        text_rect = text_surf.get_rect(center=rect.center)
        self.screen.blit(text_surf, text_rect)

    def draw_card(self, x, y, width, height, title=None):
        """Dessine une carte avec titre optionnel"""
        card_rect = pygame.Rect(x, y, width, height)
        self.draw_rounded_rect(self.screen, self.CARD_BG, card_rect, 15)
        pygame.draw.rect(self.screen, self.BORDER_COLOR, card_rect, 2, border_radius=15)

        if title:
            title_surf = self.font_medium.render(title, True, self.TEXT_PRIMARY)
            self.screen.blit(title_surf, (x + 25, y + 20))
            # Ligne de séparation sous le titre
            pygame.draw.line(
                self.screen,
                self.BORDER_COLOR,
                (x + 20, y + 55),
                (x + width - 20, y + 55),
                1
            )
            return y + 75  # Retourne la position Y après le titre avec plus d'espace
        return y + 25

    def draw_calibration_quality(self):
        """Affiche le score de qualité de calibration avec indicateur visuel"""
        if self.calibration_score is None:
            return

        # Déterminer la qualité
        if self.calibration_score < 0.05:
            quality = "EXCELLENT"
            color = self.ACCENT_SUCCESS
            quality_text = "La calibration est excellente !"
        elif self.calibration_score < 0.10:
            quality = "BONNE"
            color = self.ACCENT_PRIMARY
            quality_text = "La calibration est bonne."
        elif self.calibration_score < 0.20:
            quality = "MOYENNE"
            color = self.ACCENT_WARNING
            quality_text = "Calibration acceptable. Recalibrer recommandé."
        else:
            quality = "FAIBLE"
            color = self.ACCENT_DANGER
            quality_text = "Calibration faible. Veuillez recalibrer."

        # Carte de calibration
        card_y = int(self.screen_height * 0.28)
        card_height = 220
        start_y = self.draw_card(
            self.screen_width // 2 - 350,
            card_y,
            700,
            card_height,
            "Qualité de la Calibration"
        )

        # Score avec plus d'espacement
        score_text = f"Score: {self.calibration_score:.3f}"
        score_surf = self.font_large.render(score_text, True, color)
        score_rect = score_surf.get_rect(center=(self.screen_width // 2, start_y + 15))
        self.screen.blit(score_surf, score_rect)

        # Qualité
        quality_surf = self.font_medium.render(quality, True, color)
        quality_rect = quality_surf.get_rect(center=(self.screen_width // 2, start_y + 55))
        self.screen.blit(quality_surf, quality_rect)

        # Description
        desc_surf = self.font_small.render(quality_text, True, self.TEXT_SECONDARY)
        desc_rect = desc_surf.get_rect(center=(self.screen_width // 2, start_y + 90))
        self.screen.blit(desc_surf, desc_rect)

        # Seuils de référence avec plus de padding en bas
        ref_text = "Seuils: <0.05 Excellent | 0.05-0.10 Bon | 0.10-0.20 Moyen | >0.20 Faible"
        ref_surf = self.font_small.render(ref_text, True, self.TEXT_SECONDARY)
        ref_rect = ref_surf.get_rect(center=(self.screen_width // 2, start_y + 120))
        self.screen.blit(ref_surf, ref_rect)

    def draw_ui(self):
        """Dessine l'interface utilisateur moderne"""
        self.screen.fill(self.BG_COLOR)

        # En-tête avec beaucoup de padding
        header_height = 160
        pygame.draw.rect(self.screen, self.CARD_BG, (0, 0, self.screen_width, header_height))
        pygame.draw.line(self.screen, self.ACCENT_PRIMARY, (0, header_height), (self.screen_width, header_height), 3)

        # Titre avec BEAUCOUP de padding au-dessus
        title_text = "Eye Tracker - Projet OraDys 3TT"
        title_surf = self.font_title.render(title_text, True, self.TEXT_PRIMARY)
        title_rect = title_surf.get_rect(center=(self.screen_width // 2, 55))
        self.screen.blit(title_surf, title_rect)

        # Sous-titre avec BEAUCOUP de padding en dessous
        subtitle_text = "Université Paris 8 - Laboratoire Paragraphe | Jean Jacques SEROUL"
        subtitle_surf = self.font_small.render(subtitle_text, True, self.TEXT_SECONDARY)
        subtitle_rect = subtitle_surf.get_rect(center=(self.screen_width // 2, 110))
        self.screen.blit(subtitle_surf, subtitle_rect)

        # Afficher la qualité de calibration si calibré (mais PAS en état STOPPED)
        if self.state in [AppState.CALIBRATED, AppState.RECORDING]:
            self.draw_calibration_quality()

        # Badge "Enregistrement en cours" sous la carte de calibration avec padding
        if self.state == AppState.RECORDING:
            state_y = int(self.screen_height * 0.28) + 220 + 50  # Après la carte + padding
            state_text = "ENREGISTREMENT EN COURS"
            state_color = self.ACCENT_DANGER

            badge_width = 450
            badge_height = 60
            badge_rect = pygame.Rect(
                self.screen_width // 2 - badge_width // 2,
                state_y,
                badge_width,
                badge_height
            )
            self.draw_rounded_rect(self.screen, self.CARD_BG, badge_rect, 30)
            pygame.draw.rect(self.screen, state_color, badge_rect, 3, border_radius=30)

            state_surf = self.font_medium.render(state_text, True, state_color)
            state_rect = state_surf.get_rect(center=badge_rect.center)
            self.screen.blit(state_surf, state_rect)

        # Boutons selon l'état
        if self.state == AppState.IDLE:
            self.draw_button(self.calibrate_button, "CALIBRER", self.ACCENT_PRIMARY, True)
        elif self.state == AppState.CALIBRATED:
            self.draw_button(self.start_button, "DÉMARRER", self.ACCENT_SUCCESS, True)
            self.draw_button(self.recalibrate_button, "RECALIBRER", self.ACCENT_WARNING, True)
        elif self.state == AppState.RECORDING:
            self.draw_button(self.start_button, "DÉMARRER", self.ACCENT_SUCCESS, False)
            self.draw_button(self.stop_button, "ARRÊTER", self.ACCENT_DANGER, True)
        elif self.state == AppState.STOPPED:
            self.draw_button(self.new_session_same_calib_button, "CONTINUER", self.ACCENT_PRIMARY, True)
            self.draw_button(self.new_session_new_calib_button, "RECALIBRER", self.ACCENT_WARNING, True)
            self.draw_button(self.quit_button, "QUITTER", self.ACCENT_DANGER, True)

        # Affichage pendant l'enregistrement
        if self.state == AppState.RECORDING:
            # Webcam
            if self.current_frame is not None:
                self.draw_webcam_feed()

            # Curseur de regard
            if self.current_gaze_x is not None and self.current_gaze_y is not None:
                self.draw_gaze_cursor(self.current_gaze_x, self.current_gaze_y)

            # Indicateur de tracking
            self.draw_tracking_status()

        # Statistiques si terminé
        if self.state == AppState.STOPPED and self.recording_end_time:
            self.show_statistics()

        pygame.display.flip()

    def draw_tracking_status(self):
        """Affiche le statut du tracking en bas de l'écran"""
        # Statut du tracking
        is_tracking = self.current_gaze_x is not None and self.current_gaze_y is not None

        status_width = 340
        status_height = 70
        status_rect = pygame.Rect(
            25,
            self.screen_height - status_height - 25,
            status_width,
            status_height
        )

        if is_tracking:
            status_color = self.ACCENT_SUCCESS
            status_text = "✓ Tracking actif"
            pos_text = f"Position: ({self.current_gaze_x:.0f}, {self.current_gaze_y:.0f})"
        else:
            status_color = self.ACCENT_DANGER
            status_text = "✗ Tracking perdu"
            pos_text = "En attente..."

        self.draw_rounded_rect(self.screen, self.CARD_BG, status_rect, 12)
        pygame.draw.rect(self.screen, status_color, status_rect, 3, border_radius=12)

        text_surf = self.font_small.render(status_text, True, status_color)
        self.screen.blit(text_surf, (status_rect.x + 20, status_rect.y + 12))

        pos_surf = self.font_small.render(pos_text, True, self.TEXT_SECONDARY)
        self.screen.blit(pos_surf, (status_rect.x + 20, status_rect.y + 40))

    def draw_webcam_feed(self):
        """Affiche le flux vidéo de la webcam"""
        if self.current_frame is None:
            return

        display_width = 320
        display_height = 240

        try:
            # Redimensionner
            frame_resized = cv2.resize(self.current_frame, (display_width, display_height))

            # Flip horizontal pour effet miroir
            frame_flipped = cv2.flip(frame_resized, 1)

            # UTILISER LA VERSION BRUT (sans conversion de couleur)
            # GazeFollower donne déjà les frames dans le bon format
            pil_image = Image.fromarray(frame_flipped)

            # Convertir PIL vers pygame
            mode = pil_image.mode
            size = pil_image.size
            data = pil_image.tobytes()

            frame_surface = pygame.image.fromstring(data, size, mode)

            x_pos = self.screen_width - display_width - 30
            y_pos = 150

            # Cadre pour la vidéo
            video_rect = pygame.Rect(x_pos - 5, y_pos - 5, display_width + 10, display_height + 10)
            self.draw_rounded_rect(self.screen, self.CARD_BG, video_rect, 10)
            pygame.draw.rect(self.screen, self.ACCENT_PRIMARY, video_rect, 3, border_radius=10)

            self.screen.blit(frame_surface, (x_pos, y_pos))
        except Exception as e:
            print(f"Erreur affichage webcam: {e}")
            import traceback
            traceback.print_exc()

    def draw_gaze_cursor(self, x, y):
        """Dessine un curseur en croix moderne"""
        cross_size = 25
        thickness = 4
        color = self.ACCENT_DANGER

        # Croix avec effet de glow
        for offset in [(0, 0), (1, 1), (-1, -1), (1, -1), (-1, 1)]:
            alpha = 100 if offset != (0, 0) else 255
            glow_color = (*color, alpha)

            # Ligne horizontale
            pygame.draw.line(self.screen, color,
                           (int(x - cross_size + offset[0]), int(y + offset[1])),
                           (int(x + cross_size + offset[0]), int(y + offset[1])),
                           thickness if offset == (0, 0) else 2)
            # Ligne verticale
            pygame.draw.line(self.screen, color,
                           (int(x + offset[0]), int(y - cross_size + offset[1])),
                           (int(x + offset[0]), int(y + cross_size + offset[1])),
                           thickness if offset == (0, 0) else 2)

        # Cercle central
        pygame.draw.circle(self.screen, color, (int(x), int(y)), 8, thickness)
        pygame.draw.circle(self.screen, self.BG_COLOR, (int(x), int(y)), 4)

    def calibrate(self):
        """Lance la calibration puis démarre automatiquement l'enregistrement"""
        print("Lancement de la calibration...")

        # Créer l'UI de calibration
        from gazefollower.ui import CalibrationUI
        calibration_ui = CalibrationUI(win=self.screen, backend_name="pygame")

        while True:
            # Nouvelle session
            self.gaze_follower._new_calibration_session()
            self.gaze_follower._calibration_controller.new_session()
            calibration_ui.new_session()

            # SKIP draw_guidance - on va directement à la calibration

            # Démarrer la calibration
            self.gaze_follower.camera.start_calibrating()

            # Dessiner les points de calibration
            calibration_ui.draw(self.gaze_follower._calibration_controller)

            # Afficher les résultats avec le score
            user_response = calibration_ui.draw_cali_result(
                self.gaze_follower._calibration_controller,
                self.gaze_follower.config.model_fit_instruction
            )

            self.gaze_follower.camera.stop_calibrating()

            if user_response:
                break

        # Récupérer le score de calibration
        self.calibration_score = self.gaze_follower._calibration_controller.mean_euclidean_error
        print(f"Score de calibration: {self.calibration_score:.2f} pixels")
        print("Calibration terminée!")

        # Passer directement à l'enregistrement
        self.state = AppState.CALIBRATED
        self.start_recording()

    def start_recording(self):
        """Démarre l'enregistrement"""
        print("Démarrage de l'enregistrement...")
        self.state = AppState.RECORDING
        self.recording_start_time = time.time()
        self.gaze_data = []

        # Réinitialiser la sauvegarde d'images
        self.last_image_save_time = time.time()
        self.image_counter = 0

        # Réinitialiser les données de visualisation
        self.current_frame = None
        self.current_gaze_x = None
        self.current_gaze_y = None

        # Wrapper callback pour capturer les frames
        self.original_camera_callback = self.gaze_follower.camera.callback_func
        self.original_camera_args = self.gaze_follower.camera.callback_args
        self.original_camera_kwargs = self.gaze_follower.camera.callback_kwargs

        def wrapped_callback(state, timestamp, frame):
            # PARTIE 1: Capture de frame (TOUJOURS exécutée, indépendante de GazeFollower)
            try:
                if self.state == AppState.RECORDING and frame is not None:
                    # Capturer IMMÉDIATEMENT la frame avant tout traitement
                    self.current_frame = frame.copy()
                    self.frame_count += 1

                    # Logger toutes les 5 secondes pour vérifier que ça tourne
                    current_time = time.time()
                    if current_time - self.last_frame_log_time >= 5.0:
                        print(f"✓ Callback actif - {self.frame_count} frames capturées")
                        self.last_frame_log_time = current_time

                    # Sauvegarder une image périodiquement (toutes les 2 secondes)
                    if current_time - self.last_image_save_time >= self.image_save_interval:
                        try:
                            self._save_frame_image(frame, timestamp)
                            self.last_image_save_time = current_time
                        except Exception as e:
                            print(f"⚠️ Erreur sauvegarde image: {e}")
            except Exception as e:
                print(f"❌ Erreur capture frame: {e}")
                import traceback
                traceback.print_exc()

            # PARTIE 2: Appel du callback GazeFollower (séparé pour éviter qu'un crash bloque tout)
            try:
                if self.original_camera_callback:
                    self.original_camera_callback(state, timestamp, frame, *self.original_camera_args, **self.original_camera_kwargs)
            except Exception as e:
                print(f"❌ Erreur dans process_frame GazeFollower: {e}")
                print("⚠️ Le tracking peut être perturbé mais la vidéo continue")
                import traceback
                traceback.print_exc()

        self.gaze_follower.camera.set_on_image_callback(wrapped_callback)
        self.gaze_follower.add_subscriber(self.collect_gaze_data)
        self.gaze_follower.start_sampling()

    def get_session_name(self):
        """Demande le nom de la session à l'utilisateur - UNE SEULE FOIS"""
        user_text = ""
        print("\n📝 Saisie du nom de session...")

        while True:  # Boucle infinie - on sort avec return
            self.screen.fill(self.BG_COLOR)

            # Titre
            title_surf = self.font_large.render("Nom de la session", True, self.TEXT_PRIMARY)
            title_rect = title_surf.get_rect(center=(self.screen_width // 2, self.screen_height // 2 - 100))
            self.screen.blit(title_surf, title_rect)

            # Champ de texte
            input_box = pygame.Rect(self.screen_width // 2 - 300, self.screen_height // 2, 600, 60)
            self.draw_rounded_rect(self.screen, self.CARD_BG, input_box, 10)
            pygame.draw.rect(self.screen, self.ACCENT_PRIMARY, input_box, 3, border_radius=10)

            text_surf = self.font_medium.render(user_text + "_", True, self.TEXT_PRIMARY)
            self.screen.blit(text_surf, (input_box.x + 15, input_box.y + 15))

            # Instruction
            inst_surf = self.font_small.render("Appuyez sur ENTRÉE pour valider", True, self.TEXT_SECONDARY)
            inst_rect = inst_surf.get_rect(center=(self.screen_width // 2, self.screen_height // 2 + 100))
            self.screen.blit(inst_surf, inst_rect)

            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "session"
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                        # SORTIR IMMÉDIATEMENT avec return
                        final_name = user_text.strip() if user_text.strip() else f"session_{int(time.time())}"
                        print(f"✓ ENTRÉE détectée - Retour immédiat avec: '{final_name}'")
                        return final_name  # SORTIE IMMÉDIATE!
                    elif event.key == pygame.K_BACKSPACE:
                        user_text = user_text[:-1]
                    else:
                        # Limiter à des caractères alphanumériques et underscore
                        if event.unicode.isalnum() or event.unicode in ['-', '_', ' ']:
                            user_text += event.unicode

    def _save_frame_image(self, frame, timestamp):
        """Sauvegarde une frame dans le répertoire images"""
        # Créer le répertoire images si nécessaire (lazy initialization)
        if self.images_dir is None:
            # Créer un nom temporaire basé sur le timestamp
            temp_session_name = f"session_{int(self.recording_start_time)}"
            self.session_dir = os.path.join(os.getcwd(), temp_session_name)
            self.images_dir = os.path.join(self.session_dir, "images")

            # Créer les répertoires
            os.makedirs(self.images_dir, exist_ok=True)
            print(f"Répertoire de session créé: {self.session_dir}")

        # Incrémenter le compteur et sauvegarder
        self.image_counter += 1
        image_filename = f"{self.image_counter:04d}.jpg"
        image_path = os.path.join(self.images_dir, image_filename)

        # GazeFollower donne les frames en RGB, mais cv2.imwrite attend du BGR
        # On inverse les canaux pour sauvegarder correctement
        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        cv2.imwrite(image_path, frame_bgr, [cv2.IMWRITE_JPEG_QUALITY, 85])

        if self.image_counter % 30 == 0:  # Afficher tous les 30 images (~1 minute)
            print(f"📸 {self.image_counter} images sauvegardées")

    def stop_recording(self):
        """Arrête l'enregistrement"""
        print("\n🛑 Arrêt de l'enregistrement...")
        self.gaze_follower.stop_sampling()
        self.gaze_follower.remove_subscriber(self.collect_gaze_data)

        # Restaurer le callback original
        if hasattr(self, 'original_camera_callback'):
            self.gaze_follower.camera.set_on_image_callback(
                self.original_camera_callback,
                self.original_camera_args,
                self.original_camera_kwargs
            )

        self.current_frame = None
        self.current_gaze_x = None
        self.current_gaze_y = None

        self.recording_end_time = time.time()

        # Demander le nom de la session
        self.session_name = self.get_session_name()
        print(f"✓ Nom de session reçu: {self.session_name}")

        # Renommer le répertoire temporaire avec le vrai nom de session
        if self.session_dir is not None:
            # Nouveau nom de répertoire
            new_session_dir = os.path.join(os.getcwd(), self.session_name)

            # Renommer si le répertoire temporaire existe
            if os.path.exists(self.session_dir):
                # Si le répertoire cible existe déjà, ajouter un suffixe
                if os.path.exists(new_session_dir):
                    suffix = 1
                    while os.path.exists(f"{new_session_dir}_{suffix}"):
                        suffix += 1
                    new_session_dir = f"{new_session_dir}_{suffix}"

                os.rename(self.session_dir, new_session_dir)
                self.session_dir = new_session_dir
                self.images_dir = os.path.join(self.session_dir, "images")
                print(f"Répertoire renommé: {self.session_dir}")
        else:
            # Créer le répertoire si aucune image n'a été sauvegardée
            self.session_dir = os.path.join(os.getcwd(), self.session_name)
            os.makedirs(self.session_dir, exist_ok=True)

        # Sauvegarder le CSV dans le répertoire de session
        csv_filename = f"{self.session_name}.csv"
        csv_path = os.path.join(self.session_dir, csv_filename)
        print(f"💾 Sauvegarde du CSV...")
        self.gaze_follower.save_data(csv_path)
        print(f"✓ CSV sauvegardé: {csv_path}")
        print(f"✓ {self.image_counter} images dans: {self.images_dir if self.images_dir else 'aucun répertoire'}")

        # Calculer et afficher les statistiques dans la console
        print(f"\n📊 Calcul des statistiques...")
        self.calculate_statistics()

        # FERMETURE FORCÉE IMMÉDIATE - Sans passer par la boucle principale
        print("\n👋 Fermeture FORCÉE de l'application...")
        print("=" * 60)

        # Nettoyer GazeFollower
        try:
            self.gaze_follower.release()
        except:
            pass

        # Fermer pygame
        pygame.quit()

        # SORTIE FORCÉE IMMÉDIATE
        print("✓ Application fermée avec succès!")
        print("=" * 60)
        os._exit(0)  # Sortie FORCÉE sans nettoyage supplémentaire

    def collect_gaze_data(self, face_info, gaze_info):
        """Collecte les données de regard - Continue même si tracking perdu"""
        try:
            # Toujours collecter, même si le tracking est perdu
            gaze_x = None
            gaze_y = None
            looking_at_screen = False
            tracking_status = False

            if gaze_info and gaze_info.status:
                tracking_status = True
                if gaze_info.filtered_gaze_coordinates is not None:
                    gaze_x = gaze_info.filtered_gaze_coordinates[0]
                    gaze_y = gaze_info.filtered_gaze_coordinates[1]

                    # Mettre à jour la position actuelle
                    self.current_gaze_x = gaze_x
                    self.current_gaze_y = gaze_y

                    # Vérifier si dans les limites de l'écran
                    if 0 <= gaze_x <= self.screen_width and 0 <= gaze_y <= self.screen_height:
                        looking_at_screen = True
            else:
                # Tracking perdu - on réinitialise la position actuelle
                # Mais on CONTINUE à collecter les données
                self.current_gaze_x = None
                self.current_gaze_y = None

            # Enregistrer les données (même si tracking perdu)
            self.gaze_data.append({
                'timestamp': gaze_info.timestamp if gaze_info else time.time(),
                'gaze_x': gaze_x,
                'gaze_y': gaze_y,
                'status': tracking_status,
                'looking_at_screen': looking_at_screen,
                'tracking_lost': not tracking_status
            })
        except Exception as e:
            # Ne PAS crasher si erreur - juste logger
            print(f"Erreur collecte données: {e}")

    def calculate_statistics(self):
        """Calcule les statistiques de regard"""
        if not self.gaze_data:
            print("Aucune donnée collectée")
            return

        total_duration = self.recording_end_time - self.recording_start_time

        # Échantillons regardant l'écran
        samples_looking_at_screen = [d for d in self.gaze_data if d.get('looking_at_screen', False)]

        # Échantillons avec tracking perdu
        samples_tracking_lost = [d for d in self.gaze_data if d.get('tracking_lost', False)]

        # Échantillons valides
        valid_samples = [d for d in self.gaze_data if d['status'] and d['gaze_x'] is not None]

        # Calculs temporels
        if len(self.gaze_data) > 0:
            time_looking_at_screen = (len(samples_looking_at_screen) / len(self.gaze_data)) * total_duration
            time_tracking_lost = (len(samples_tracking_lost) / len(self.gaze_data)) * total_duration
        else:
            time_looking_at_screen = 0
            time_tracking_lost = 0

        self.statistics = {
            'total_duration': total_duration,
            'time_looking_at_screen': time_looking_at_screen,
            'time_tracking_lost': time_tracking_lost,
            'percentage_looking': (time_looking_at_screen / total_duration * 100) if total_duration > 0 else 0,
            'percentage_lost': (time_tracking_lost / total_duration * 100) if total_duration > 0 else 0,
            'total_samples': len(self.gaze_data),
            'valid_samples': len(valid_samples),
            'screen_samples': len(samples_looking_at_screen),
            'lost_samples': len(samples_tracking_lost)
        }

        print("\n=== STATISTIQUES ===")
        print(f"Durée totale: {total_duration:.2f} secondes")
        print(f"Temps de regard sur l'écran: {time_looking_at_screen:.2f}s ({self.statistics['percentage_looking']:.1f}%)")
        print(f"Temps tracking perdu: {time_tracking_lost:.2f}s ({self.statistics['percentage_lost']:.1f}%)")
        print(f"Échantillons: {self.statistics['screen_samples']} écran / {self.statistics['lost_samples']} perdus / {self.statistics['total_samples']} total")
        print("===================\n")

    def show_statistics(self):
        """Affiche les statistiques sur l'écran"""
        if not hasattr(self, 'statistics'):
            return

        # Carte des statistiques avec plus d'espace
        card_width = 800
        card_height = 260
        card_x = self.screen_width // 2 - card_width // 2
        card_y = int(self.screen_height * 0.38)

        start_y = self.draw_card(card_x, card_y, card_width, card_height, "Statistiques de la Session")

        stats_data = [
            (f"Durée totale: {self.statistics['total_duration']:.1f}s", self.TEXT_PRIMARY),
            (f"Temps regardant l'écran: {self.statistics['time_looking_at_screen']:.1f}s ({self.statistics['percentage_looking']:.1f}%)",
             self.ACCENT_SUCCESS),
            (f"Temps tracking perdu: {self.statistics['time_tracking_lost']:.1f}s ({self.statistics['percentage_lost']:.1f}%)",
             self.ACCENT_WARNING),
            (f"Échantillons: {self.statistics['screen_samples']} écran / {self.statistics['lost_samples']} perdus / {self.statistics['total_samples']} total",
             self.TEXT_SECONDARY)
        ]

        y_offset = start_y + 5
        for text, color in stats_data:
            text_surf = self.font_medium.render(text, True, color)
            text_rect = text_surf.get_rect(center=(self.screen_width // 2, y_offset))
            self.screen.blit(text_surf, text_rect)
            y_offset += 45

    def handle_click(self, pos):
        """Gère les clics de souris"""
        if self.calibrate_button.collidepoint(pos):
            if self.state == AppState.IDLE:
                self.calibrate()

        elif self.start_button.collidepoint(pos):
            if self.state == AppState.CALIBRATED:
                self.start_recording()

        elif self.stop_button.collidepoint(pos):
            if self.state == AppState.RECORDING:
                self.stop_recording()

        elif self.recalibrate_button.collidepoint(pos):
            if self.state == AppState.CALIBRATED:
                self.calibrate()

        elif self.new_session_same_calib_button.collidepoint(pos):
            if self.state == AppState.STOPPED:
                # Nouvelle session avec la même calibration
                self.state = AppState.CALIBRATED
                self.recording_start_time = None
                self.recording_end_time = None
                self.gaze_data = []

        elif self.new_session_new_calib_button.collidepoint(pos):
            if self.state == AppState.STOPPED:
                # Nouvelle session avec recalibration
                self.calibrate()

        elif self.quit_button.collidepoint(pos):
            if self.state == AppState.STOPPED:
                self.cleanup_and_quit()

    def cleanup_and_quit(self):
        """Nettoie et quitte l'application"""
        if self.state == AppState.RECORDING:
            self.stop_recording()
        self.gaze_follower.release()
        pygame.quit()
        sys.exit()

    def run(self):
        """Boucle principale de l'application"""
        clock = pygame.time.Clock()
        running = True

        while running:
            # Vérifier le flag de sortie
            if self.should_quit:
                print("🔄 Flag de sortie détecté - Arrêt de la boucle principale")
                running = False
                break

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.handle_click(event.pos)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if self.state == AppState.STOPPED:
                            running = False
                        else:
                            # Confirmation avant de quitter en cours d'enregistrement
                            print("Appuyez sur ESCAPE à nouveau pour quitter")

            self.draw_ui()
            clock.tick(30)

        print("🔧 Nettoyage et fermeture...")
        self.cleanup_and_quit()


if __name__ == "__main__":
    app = EyeTrackerApp()
    app.run()
