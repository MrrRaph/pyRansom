from Crypto.Cipher import AES
from Crypto.Hash import HMAC, SHA256
from Crypto.Util.Padding import unpad, pad

from core import derivative_keys
from utils import getFileSize

CHUNK_SIZE = 2064
SALT_SIZE = 8


def symDecryptFile(inputFile: str, outputFile: str, password: bytes) -> None:
    try:
        with open(outputFile, 'wb') as writer, open(inputFile, 'rb') as reader:
            salt = reader.read(SALT_SIZE)
            iv = reader.read(AES.block_size)

            kc, ki = derivative_keys(password, salt)
            _mac_bytes = HMAC.new(ki, digestmod=SHA256) \
                .update(iv) \
                .update(salt)

            currentCursorPosition = reader.tell()
            fileSize = getFileSize(reader)

            reader.seek(currentCursorPosition, 0)

            decipher = AES.new(kc, AES.MODE_CBC, iv=iv)
            while True:
                remainingBytes = fileSize - reader.tell()
                if remainingBytes - CHUNK_SIZE > SHA256.digest_size:
                    chunk = reader.read(CHUNK_SIZE)
                elif remainingBytes - SHA256.digest_size > SHA256.digest_size:
                    chunk = reader.read(remainingBytes - SHA256.digest_size)
                else:
                    break

                decrypted_bytes = symDecryptBlock(decipher, chunk, AES.block_size)
                writer.write(decrypted_bytes)
                _mac_bytes.update(chunk)
                decipher = AES.new(kc, AES.MODE_CBC, iv=chunk[-AES.block_size:])

            mac = reader.read(SHA256.digest_size)
            _mac_bytes.verify(mac)
    except ValueError as e:
        open(outputFile, 'r+').truncate()
        print("[-]", e)


def symDecryptBlock(decipher, chunk: bytes, block_size: int) -> bytes:
    return unpad(decipher.decrypt(chunk), block_size=block_size)
