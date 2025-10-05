import os
import zipfile
import shutil
from typing import Optional

class FileService:
    
    @staticmethod
    def create_zip(source_dir: str, zip_path: str) -> bool:
        try:
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(source_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, source_dir)
                        zipf.write(file_path, arcname)
            return True
        except Exception as e:
            print(f"Error creating zip: {e}")
            return False
    
    @staticmethod
    def cleanup_directory(directory: str) -> None:
        try:
            if os.path.exists(directory):
                shutil.rmtree(directory)
        except Exception as e:
            print(f"Error cleaning up directory {directory}: {e}")
    
    @staticmethod
    def ensure_static_dir() -> None:
        os.makedirs("app/static", exist_ok=True)
