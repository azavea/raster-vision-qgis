import os
import json
from datetime import datetime, timezone

from urllib.parse import urlparse

from .log import Log

class UnsupportedException(Exception):
    pass

class S3Exception(Exception):
    pass

def s3_client(profile_name=None):
    import boto3

    if profile_name:
        session = boto3.Session(profile_name=profile_name)
        s3 = session.client('s3')
    else:
        s3 = boto3.client('s3')

    return s3


def get_local_path(uri, working_dir, profile_name=None):
    """
    This method will simply pass along the URI if it is local.
    If the URI is on S3, it will download the data to the working directory,
    in a structure that matches s3, and return the local path.
    If the local path already exists, and the timestamp of the S3 object is at or before
    the local path, the download will be skipped
    """

    parsed_uri = urlparse(uri)
    if parsed_uri.scheme == '':
        path = uri
        if not os.path.exists(path):
            Log.log_warning("File Util: File does not exists - {}".format(path))
            return None
    elif parsed_uri.scheme == 's3':
        import botocore

        bucket = parsed_uri.netloc
        key = parsed_uri.path.strip("/")

        s3 = s3_client(profile_name=profile_name)

        path = os.path.join(
            working_dir, 's3', parsed_uri.netloc, parsed_uri.path[1:])

        def _do_download():
            try:
                s3.download_file(bucket, key, path)
            except botocore.exceptions.ClientError as e:
                Log.log_warning("File Util: Could not read of {}. {}".format(uri, e))
                return None
                # raise S3Exception("Could not read of {}".format(uri)) from e

        if os.path.exists(path):
            try:
                head_data = s3.head_object(Bucket=bucket,
                                           Key=key)

                s3_last_modified = head_data['LastModified']
                local_last_modified = datetime.utcfromtimestamp(os.path.getmtime(path))

                if local_last_modified.replace(tzinfo=timezone.utc) <= s3_last_modified:
                    _do_download()
            except botocore.exceptions.ClientError as e:
                # TODO: Is this right?
                # raise S3Exception("Could not read of {}".format(uri)) from e
                Log.log_warning("File Util: Could not read HEAD data for existing: {}. {}".format(uri, e))
                return None
        else:
            local_dir = os.path.dirname(path)

            if not os.path.exists(local_dir):
                os.makedirs(local_dir)

            path = _do_download()
    else:
        raise UnsupportedException("Unsupported scheme: {}".format(parssed_uri.scheme))

    return path
