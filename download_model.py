import shutil

import dropbox

from common import config

if __name__ == "__main__":
    client = dropbox.Dropbox(config.dropbox_token)
    destination = "model.zip"
    _, response = client.files_download("/model.zip")
    with open(destination, "wb") as f:
        f.write(response.content)
    shutil.unpack_archive(destination)
