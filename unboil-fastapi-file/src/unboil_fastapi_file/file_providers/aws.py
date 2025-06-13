import aioboto3
from botocore.exceptions import ClientError
from typing import IO
from io import BytesIO
from unboil_fastapi_file.file_providers import FileProvider


class AWSFileProvider(FileProvider):

    def __init__(
        self, bucket_name: str, aws_access_key_id: str, aws_secret_access_key: str
    ):
        self.bucket_name = bucket_name
        self.session = aioboto3.Session(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
        )

    async def list_keys(self, prefix: str) -> list[str]:
        async with self.session.client("s3") as client:    
            response = await client.list_objects_v2(Bucket=self.bucket_name, Prefix=prefix)
            return [
                key for obj in response.get("Contents", []) if (key := obj.get("Key", None))
            ]

    async def object_exists(self, key: str) -> bool:
        try:
            async with self.session.client("s3") as client:
                await client.head_object(Bucket=self.bucket_name, Key=key)
        except ClientError as e:
            if e.response.get("Error", {}).get("Code", None) == "404":
                return False
        return True

    async def copy_object(self, source_key: str, target_key: str) -> None:
        async with self.session.client("s3") as client:
            await client.copy_object(
                Bucket=self.bucket_name,
                CopySource={"Bucket": self.bucket_name, "Key": source_key},
                Key=target_key,
            )

    async def upload_object(self, key: str, file: IO) -> None:
        async with self.session.client("s3") as client:
            await client.upload_fileobj(file, self.bucket_name, key)

    async def download_object(self, key: str) -> IO:
        async with self.session.client("s3") as client:
            response = await client.get_object(Bucket=self.bucket_name, Key=key)
            return BytesIO(await response["Body"].read())

    async def delete_object(self, key: str):
        async with self.session.client("s3") as client:
            await client.delete_object(Bucket=self.bucket_name, Key=key)

    async def delete_objects(self, keys: list[str]):
        async with self.session.client("s3") as client:
            await client.delete_objects(
                Bucket=self.bucket_name, Delete={"Objects": [{"Key": key} for key in keys]}
            )
