import shutil

import dropbox

from common import config

if __name__ == "__main__":
    client = dropbox.Dropbox(
        app_key=config.dropbox["key"],
        app_secret=config.dropbox["secret"],
        oauth2_refresh_token=config.dropbox["refresh_token"],
    )
    destination = "model.zip"
    _, response = client.files_download("/model.zip")
    with open(destination, "wb") as f:
        f.write(response.content)
    shutil.unpack_archive(destination)
