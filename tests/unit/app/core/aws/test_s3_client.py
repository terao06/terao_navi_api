from app.core.aws.s3_client import S3Client


class TestS3Client:
    def test_get_objects(self, managed_s3_bucket):
        """S3からオブジェクトを取得するテスト"""
        bucket_name = "test-bucket"
        files = {
            "folder1/file1.txt": "file_content_1",
            "folder2/file2.txt": "file_content_2"
        }
        
        object_paths = [
            f"s3://{bucket_name}/folder1/file1.txt",
            f"s3://{bucket_name}/folder2/file2.txt"
        ]

        with managed_s3_bucket(bucket_name, files):
            s3_client = S3Client()
            results = s3_client.get_objects(bucket_name, object_paths)
            
            assert len(results) == 2
            assert results[0] == b"file_content_1"
            assert results[1] == b"file_content_2"
