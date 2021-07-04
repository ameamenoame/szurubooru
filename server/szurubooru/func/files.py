import logging
import os
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type
from io import BytesIO
import boto3
from botocore.exceptions import ClientError
from PIL import Image

from szurubooru import config, errors

logger = logging.getLogger(__name__)

def delete(path: str) -> None:
    adapter.delete(path)


def has(path: str) -> bool:
    return adapter.has(path)


def scan(path: str) -> List[Any]:
    return adapter.scan(path)


def move(source_path: str, target_path: str) -> None:
    adapter.move(source_path, target_path)


def get(path: str) -> Optional[bytes]:
    return adapter.get(path)


def save(path: str, content: bytes) -> None:
    adapter.save(path, content)


class StorageAdapter(ABC):
    adapters: Dict[str, Type['StorageAdapter']] = {}

    def __init_subclass__(cls, *args, **kwargs):
        super().__init_subclass__(*args, **kwargs)
        name = cls.name()
        if name not in cls.adapters:
            cls.adapters[name] = cls

    @classmethod
    @abstractmethod
    def name(cls) -> str:
        raise NotImplementedError()

    @abstractmethod
    def delete(self, path: str) -> None:
        raise NotImplementedError()

    @abstractmethod
    def has(self, path: str) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def scan(self, path: str) -> List[Any]:
        raise NotImplementedError()

    @abstractmethod
    def move(self, source_path: str, target_path: str) -> None:
        raise NotImplementedError()

    @abstractmethod
    def get(self, path: str) -> Optional[bytes]:
        raise NotImplementedError()

    @abstractmethod
    def save(self, path: str, content: bytes) -> None:
        raise NotImplementedError()

    @classmethod
    def create(cls) -> 'StorageAdapter':
        if 'storage' in config.config:
            storage = config.config['storage']
            storage_type = storage.get('type')
            if storage_type in cls.adapters:
                option = storage.get('option', {})
                return cls.adapters[storage_type](**option)
            else:
                raise errors.ConfigError(
                    '%r is not a valid storage adapter' % storage_type)
        else:
            return LocalStorageAdapter(config.config['data_dir'])


class LocalStorageAdapter(StorageAdapter):
    def __init__(self, data_dir: str):
        self.data_dir = data_dir

    @classmethod
    def name(cls) -> str:
        return 'local'

    def _get_full_path(self, path: str) -> str:
        return os.path.join(self.data_dir, path)

    def delete(self, path: str) -> None:
        full_path = self._get_full_path(path)
        if os.path.exists(full_path):
            os.unlink(full_path)

    def has(self, path: str) -> bool:
        return os.path.exists(self._get_full_path(path))

    def scan(self, path: str) -> List[Any]:
        if self.has(path):
            return list(os.scandir(self._get_full_path(path)))
        return []

    def move(self, source_path: str, target_path: str) -> None:
        os.rename(self._get_full_path(source_path),
                  self._get_full_path(target_path))

    def get(self, path: str) -> Optional[bytes]:
        full_path = self._get_full_path(path)
        if not os.path.exists(full_path):
            return None
        with open(full_path, 'rb') as handle:
            return handle.read()

    def save(self, path: str, content: bytes) -> None:
        full_path = self._get_full_path(path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, 'wb') as handle:
            handle.write(content)

# For path compatibility
class S3Path:
    def __init__(self, s3, full_path):
        self.s3 = s3
        self.path = s3.key
        self.name = s3.key.replace(full_path + '/', '')

    def stat(self):
        return S3Stat(self.s3)

# For path compatibility
class S3Stat:
    def __init__(self, s3):
        self.st_ctime = s3.last_modified.timestamp()


class S3StorageAdapter(StorageAdapter):
    def __init__(self, **kwargs):
        self.s3 = boto3.resource(
            's3',
            region_name=kwargs.get('region_name'),
            endpoint_url=kwargs.get('endpoint_url'),
            aws_access_key_id=kwargs.get('aws_access_key_id'),
            aws_secret_access_key=kwargs.get('aws_secret_access_key')
        )
        self.bucket = self.s3.Bucket(kwargs.get('bucket'))
        self.prefix = kwargs.get('prefix', '')

    @classmethod
    def name(cls) -> str:
        return 's3'

    def _get_full_path(self, path: str) -> str:
        if self.prefix == '':
            return path
        return '%s/%s' % (self.prefix, path)

    def delete(self, path: str) -> None:
        full_path = self._get_full_path(path)
        try:
            obj = self.bucket.Object(full_path)
            obj.delete()
        except ClientError:
            logging.exception('s3 has delete (%s)' % full_path)

    def has(self, path: str) -> bool:
        full_path = self._get_full_path(path)
        try:
            self.bucket.Object(full_path).load()
            return True
        except ClientError:
            return False

    def scan(self, path: str) -> List[Any]:
        full_path = self._get_full_path(path)
        return [S3Path(s3, full_path) for s3 in
                self.bucket.objects.filter(Prefix=full_path)]

    def move(self, source_path: str, target_path: str) -> None:
        source_full_path = self._get_full_path(source_path)
        target_full_path = self._get_full_path(target_path)
        try:
            self.bucket.Object(target_full_path) \
                .copy_from(CopySource=source_full_path)
            self.bucket.Object(source_full_path).delete()
        except ClientError:
            logging.exception('s3 save move (%s > %s)' %
                              (source_full_path, target_full_path))

    def get(self, path: str) -> Optional[bytes]:
        full_path = self._get_full_path(path)
        try:
            obj = self.bucket.Object(full_path)
            return obj.get()['Body'].read()
        except ClientError:
            logging.exception('s3 get fail (%s)' % full_path)
            return None

    def save(self, path: str, content: bytes) -> None:
        full_path = self._get_full_path(path)
        try:
            mime = None
           # MIME is not necessary
           # If you don't set it, S3 will return Content-Type application/octet-stream
            try:
                img = Image.open(BytesIO(content))
                mime = Image.MIME.get(img.format)
            except IOError:
                pass
            self.bucket.Object(full_path)\
                .put(Body=content, ACL='public-read', ContentType=mime)
        except ClientError:
            logging.exception('s3 save fail (%s)' % full_path)
            return None

adapter = StorageAdapter.create()

