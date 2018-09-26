import os
import json
from datetime import datetime, timezone

from rastervision.filesystem import (FileSystem, LocalFileSystem)
from rastervision.utils.files import make_dir

from .log import Log

def get_local_path(uri, working_dir):
    """
    This method will simply pass along the URI if it is local.
    If the URI is on S3, it will download the data to the working directory,
    in a structure that matches s3, and return the local path.
    If the local path already exists, and the timestamp of the S3 object is at or before
    the local path, the download will be skipped
    """

    fs = FileSystem.get_file_system(uri)
    if fs is LocalFileSystem:
        return uri


    local_path = fs.local_path(uri, working_dir)
    do_copy = True
    if os.path.exists(local_path):
        last_modified = fs.last_modified(uri)
        if last_modified:
            # If thel local file is older than the remote file, download it.
            local_last_modified = datetime.utcfromtimestamp(os.path.getmtime(local_path))
            if local_last_modified.replace(tzinfo=timezone.utc) > last_modified:
                do_copy = False
        else:
            # This FileSystem doesn't support last modified.
            # By default, don't download a new version.
            do_copy = False

    if do_copy:
        dir_name = os.path.dirname(local_path)
        make_dir(dir_name)
        fs.copy_from(uri, local_path)

    return local_path
