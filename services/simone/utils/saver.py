from __future__ import annotations

import cv2
import numpy as np
import os


class Saver:
    def __init__(self, frames, scores, output_path):
        self.frames = frames
        self.scores = scores
        self.output_path = output_path

    def save_best_frames(self):
        if self.frames and self.scores and len(self.frames) == len(self.scores):
            scores = np.array(self.scores)
            # Get top 3 frames
            top_indices = np.argsort(scores)[-3:]
            
            # Ensure output directory exists
            os.makedirs(self.output_path, exist_ok=True)

            for idx, i in enumerate(top_indices):
                frame = self.frames[i]
                # Save as PNG with generic name
                file_name = os.path.join(self.output_path, f"screenshot_{idx}.png")
                cv2.imwrite(file_name, frame)
