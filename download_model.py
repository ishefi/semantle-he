import gdown
import shutil
from common.config import conf

if __name__ == "__main__":
    url = f'https://drive.google.com/uc?id={conf.model_zip_id}'
    destination = "model.zip"
    gdown.download(url, destination, quiet=False)
    shutil.unpack_archive("model.zip")
