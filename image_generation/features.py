import os
import cv2
import numpy as np
import io
from PIL import Image
from rembg import remove, new_session
from tqdm import tqdm
from pathlib import Path

class ImageProcessor:
    VALID_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.webp')

    def __init__(self, input_dir="data/raw", output_dir="data/processed", model_name="u2net"):
        self.input_dir = input_dir
        self.output_dir = output_dir
        
        print(f"Loading rembg model: {model_name}...")
        self.session = new_session(model_name)
        
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)

    def letterbox_image(self, image, size=(256, 256)):
        """Resizes image maintaining aspect ratio and pads with black to reach target size."""
        ih, iw = image.shape[:2]
        w, h = size
        
        scale = min(w/iw, h/ih)
        nw, nh = int(iw * scale), int(ih * scale)
        image_resized = cv2.resize(image, (nw, nh), interpolation=cv2.INTER_AREA)
        canvas = np.zeros((h, w, 3), dtype=np.uint8)
        
        dx = (w - nw) // 2
        dy = (h - nh) // 2

        canvas[dy:dy+nh, dx:dx+nw] = image_resized
        return canvas

    def process_and_resize(self, file_name, target_size=(256, 256)):
        """Full Pipeline: Remove BG -> Black BG -> Letterbox Resize."""
        input_path = os.path.join(self.input_dir, file_name)
        output_path = os.path.join(self.output_dir, file_name)

        try:
            # Background Removal (PIL)
            with Image.open(input_path) as img:
                img = img.convert("RGBA")
                no_bg = remove(img, session=self.session)
   
                canvas_pil = Image.new("RGBA", no_bg.size, (0, 0, 0, 255))
                canvas_pil.alpha_composite(no_bg)
                
                open_cv_image = np.array(canvas_pil.convert("RGB"))
                open_cv_image = open_cv_image[:, :, ::-1].copy() 

            final_img = self.letterbox_image(open_cv_image, size=target_size)
            
            cv2.imwrite(output_path, final_img)

        except Exception as e:
            print(f"\n[Error] Failed to process {file_name}: {e}")

    def run_batch(self, target_size=(256, 256)):
        """Orchestrates the batch processing."""
        images = [f for f in os.listdir(self.input_dir) 
                  if f.lower().endswith(self.VALID_EXTENSIONS)]
        
        if not images:
            print(f"No images found in {self.input_dir}")
            return

        print(f"Processing {len(images)} images to {target_size}...")
        for file_name in tqdm(images, desc="Pipeline", unit="img"):
            self.process_and_resize(file_name, target_size=target_size)
            
        print(f"\nWorkflow complete. Results saved in: {self.output_dir}")

# --- Execution ---
if __name__ == "__main__":
    processor = ImageProcessor(
        input_dir="data/raw", 
        output_dir="data/processed",
    )
    processor.run_batch(target_size=(256, 256))