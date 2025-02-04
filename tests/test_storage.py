import os
import pytest
import shutil
import boto3
import json
from pathlib import Path
from moto import mock_s3
from typing import Dict, Any

from src.storage import Storage, LocalStorage, S3Storage
from src.utils.errors import StorageError

@pytest.fixture
def local_storage(tmp_path: Path):
    """创建本地存储实例"""
    config = {
        "enabled": True,
        "path": str(tmp_path / "exports"),
        "max_size": "1GB",
        "cleanup_threshold": "800MB"
    }
    return LocalStorage(config)

@pytest.fixture
def s3_storage():
    """创建S3存储实例"""
    config = {
        "enabled": True,
        "bucket": "test-bucket",
        "prefix": "exports",
        "max_size": "10GB",
        "cleanup_threshold": "8GB",
        "region": "us-east-1",
        "access_key": "test",
        "secret_key": "test"
    }
    return S3Storage(config)

@pytest.fixture
def s3_mock():
    """创建S3模拟环境"""
    with mock_s3():
        s3 = boto3.client(
            "s3",
            region_name="us-east-1",
            aws_access_key_id="test",
            aws_secret_access_key="test"
        )
        s3.create_bucket(Bucket="test-bucket")
        yield s3

class TestLocalStorage:
    """本地存储测试类"""

    async def test_save_file(self, local_storage, tmp_path):
        """测试保存文件"""
        content = b"test content"
        path = await local_storage.save("test.txt", content)
        
        assert path.exists()
        assert path.read_bytes() == content

    async def test_save_file_with_dirs(self, local_storage):
        """测试保存到子目录"""
        content = b"test content"
        path = await local_storage.save("subdir/test.txt", content)
        
        assert path.exists()
        assert path.read_bytes() == content
        assert path.parent.name == "subdir"

    async def test_load_file(self, local_storage):
        """测试加载文件"""
        content = b"test content"
        path = await local_storage.save("test.txt", content)
        
        loaded_content = await local_storage.load("test.txt")
        assert loaded_content == content

    async def test_delete_file(self, local_storage):
        """测试删除文件"""
        content = b"test content"
        path = await local_storage.save("test.txt", content)
        
        await local_storage.delete("test.txt")
        assert not path.exists()

    async def test_list_files(self, local_storage):
        """测试列出文件"""
        await local_storage.save("test1.txt", b"content1")
        await local_storage.save("test2.txt", b"content2")
        await local_storage.save("subdir/test3.txt", b"content3")
        
        files = await local_storage.list()
        assert len(files) == 3
        assert "test1.txt" in files
        assert "test2.txt" in files
        assert "subdir/test3.txt" in files

    async def test_storage_size(self, local_storage):
        """测试存储大小计算"""
        await local_storage.save("test1.txt", b"content1")
        await local_storage.save("test2.txt", b"content2" * 1000)
        
        size = await local_storage.get_size()
        assert size > 0
        assert isinstance(size, int)

    async def test_cleanup(self, local_storage):
        """测试存储清理"""
        # 创建一些测试文件
        old_files = []
        for i in range(5):
            path = await local_storage.save(f"old{i}.txt", b"old content")
            old_files.append(path)
            # 修改文件时间为更早
            os.utime(path, (0, 0))
        
        new_files = []
        for i in range(5):
            path = await local_storage.save(f"new{i}.txt", b"new content")
            new_files.append(path)
        
        # 执行清理
        await local_storage.cleanup()
        
        # 验证旧文件被删除，新文件保留
        for path in old_files:
            assert not path.exists()
        for path in new_files:
            assert path.exists()

    def test_invalid_path(self, tmp_path):
        """测试无效路径配置"""
        config = {
            "enabled": True,
            "path": "/nonexistent/path",
            "max_size": "1GB",
            "cleanup_threshold": "800MB"
        }
        
        with pytest.raises(StorageError):
            LocalStorage(config)

    async def test_file_not_found(self, local_storage):
        """测试文件不存在"""
        with pytest.raises(StorageError):
            await local_storage.load("nonexistent.txt")

class TestS3Storage:
    """S3存储测试类"""

    async def test_save_file(self, s3_storage, s3_mock):
        """测试保存文件"""
        content = b"test content"
        path = await s3_storage.save("test.txt", content)
        
        response = s3_mock.get_object(
            Bucket="test-bucket",
            Key="exports/test.txt"
        )
        assert response["Body"].read() == content

    async def test_load_file(self, s3_storage, s3_mock):
        """测试加载文件"""
        content = b"test content"
        await s3_storage.save("test.txt", content)
        
        loaded_content = await s3_storage.load("test.txt")
        assert loaded_content == content

    async def test_delete_file(self, s3_storage, s3_mock):
        """测试删除文件"""
        content = b"test content"
        await s3_storage.save("test.txt", content)
        
        await s3_storage.delete("test.txt")
        
        with pytest.raises(s3_mock.exceptions.NoSuchKey):
            s3_mock.get_object(
                Bucket="test-bucket",
                Key="exports/test.txt"
            )

    async def test_list_files(self, s3_storage, s3_mock):
        """测试列出文件"""
        await s3_storage.save("test1.txt", b"content1")
        await s3_storage.save("test2.txt", b"content2")
        await s3_storage.save("subdir/test3.txt", b"content3")
        
        files = await s3_storage.list()
        assert len(files) == 3
        assert "test1.txt" in files
        assert "test2.txt" in files
        assert "subdir/test3.txt" in files

    async def test_storage_size(self, s3_storage, s3_mock):
        """测试存储大小计算"""
        await s3_storage.save("test1.txt", b"content1")
        await s3_storage.save("test2.txt", b"content2" * 1000)
        
        size = await s3_storage.get_size()
        assert size > 0
        assert isinstance(size, int)

    async def test_cleanup(self, s3_storage, s3_mock):
        """测试存储清理"""
        # 创建一些测试文件
        old_files = []
        for i in range(5):
            key = f"old{i}.txt"
            await s3_storage.save(key, b"old content")
            old_files.append(key)
            # 设置较早的最后修改时间
            s3_mock.copy_object(
                Bucket="test-bucket",
                CopySource={"Bucket": "test-bucket", "Key": f"exports/{key}"},
                Key=f"exports/{key}",
                MetadataDirective="REPLACE",
                Metadata={"timestamp": "0"}
            )
        
        new_files = []
        for i in range(5):
            key = f"new{i}.txt"
            await s3_storage.save(key, b"new content")
            new_files.append(key)
        
        # 执行清理
        await s3_storage.cleanup()
        
        # 验证旧文件被删除，新文件保留
        for key in old_files:
            with pytest.raises(s3_mock.exceptions.NoSuchKey):
                s3_mock.get_object(
                    Bucket="test-bucket",
                    Key=f"exports/{key}"
                )
        
        for key in new_files:
            response = s3_mock.get_object(
                Bucket="test-bucket",
                Key=f"exports/{key}"
            )
            assert response["Body"].read() == b"new content"

    def test_invalid_config(self):
        """测试无效配置"""
        config = {
            "enabled": True,
            "bucket": "",  # 空bucket名
            "prefix": "exports",
            "max_size": "10GB",
            "cleanup_threshold": "8GB"
        }
        
        with pytest.raises(StorageError):
            S3Storage(config)

    async def test_file_not_found(self, s3_storage, s3_mock):
        """测试文件不存在"""
        with pytest.raises(StorageError):
            await s3_storage.load("nonexistent.txt")

    async def test_bucket_not_found(self, s3_mock):
        """测试bucket不存在"""
        config = {
            "enabled": True,
            "bucket": "nonexistent-bucket",
            "prefix": "exports",
            "max_size": "10GB",
            "cleanup_threshold": "8GB",
            "region": "us-east-1",
            "access_key": "test",
            "secret_key": "test"
        }
        
        storage = S3Storage(config)
        with pytest.raises(StorageError):
            await storage.save("test.txt", b"content") 