import base64
import io
import os
import zlib
from Crypto.Cipher import PKCS1_OAEP, AES
from Crypto.PublicKey import RSA

from mail import Mail


def generate_keys():
    key = RSA.generate(2048)

    return key.export_key(), key.publickey().export_key().decode()


def encrypt(pk, data):
    data = bytes(data, encoding='utf-8')

    # create public key object
    key = RSA.import_key(pk)
    sessionKey = os.urandom(16)

    # encrypt the session key with the public key
    cipher = PKCS1_OAEP.new(key)
    encryptedSessionKey = cipher.encrypt(sessionKey)

    # encrypt the data with the session key
    cipher = AES.new(sessionKey, AES.MODE_EAX)
    ciphertext, tag = cipher.encrypt_and_digest(data)

    return base64.b64encode(b"".join([encryptedSessionKey, cipher.nonce, tag, ciphertext]))


def decrypt(pk, data):
    key = RSA.import_key(pk)

    byte_stream = io.BytesIO(base64.b64decode(data))

    encryptedSessionKey = byte_stream.read(key.size_in_bytes())
    nonce = byte_stream.read(16)
    tag = byte_stream.read(16)
    ciphertext = byte_stream.read()

    # decrypt the session key
    cipher = PKCS1_OAEP.new(key)
    sessionKey = cipher.decrypt(encryptedSessionKey)

    # decrypt the data with the session key
    cipher = AES.new(sessionKey, AES.MODE_EAX, nonce)
    return cipher.decrypt_and_verify(ciphertext, tag).decode()

pk = "-----BEGIN RSA PRIVATE KEY-----\nMIIEpAIBAAKCAQEA8GawqAaOWxm3kHeB5NXpmKKTf8gE/FxIuGC3wGj4AMWhdXoN\nx14LnhP0yUodBx4xKn7LDCnKSZhYlaTKElsqq/iO8JoKYl6VvCQzh4jlH+OFdK/F\nmGuitcegNGwEYHqm0dvTAiBao5aFqZV749ocWwLTHFZb9c368QyNYrbUghuq2AiF\nlFW8piOD/YL1UjYK2/nEjEIV2tnYTRZZujCn/1RlGYdhXJHCecS1+V4HI1zkTEP+\n9lozhl7lry7XW6DABDZ8ceZBdU3cipRCiJA9wqQ94GRVCivZTXZzRjAqY+ILQ6YI\n0qF8Oh4ZVk+kRcjC3ZIQwP8b5nISZ4Quyn73iQIDAQABAoIBAGNatYkECKKbCtQQ\nqCT4yY3VJyuo8XKQ+1cEVf0WBOVgyH2CX551fkyrR8BHOp79+ejrtSRGQz3OUlIq\nZH9YoVaop/7FUyRbnfu/ZHKP/84BnN7gZEQ9u+Xv5oSz3c0386kI9njLAVrZs00m\npCjDtHNiw/hSsrfwlNU50FcrY8GPO6QQPMcU9VI/EhIXoEg32n+NFlatEmsYrIxS\noV2UbanvfXzN/Vo08ysSNfRIT5OETDrh3+0kWDFcbweCt86P4fJImhTkFLspiCYF\n3Gi6QXcIzREa7yX7np5VcEgaaI+wr0KM3GbXE5nI/ACcuz7yBDqPGHDRvz0TdE4C\nmEzl4LcCgYEA9EQlo6Eqyf9zJhhGmqXSqhc9MORHFnp1Qvj0r+SIyfmqdMmv9Od8\nszT9X9/Zr8jcKCPgx6EZPG2aacdoWjLptdRcw9Fc/ossyd524AeNvrGUN8xdhtiD\nbALEZoY+W3slOfhdhQibXmYKVg4sQufr/rnkpseEQMXV/4uNJpGyB+MCgYEA+/MD\nNpEMidTcXFpyg0TvWUUEWlgdniH1teTchgaA2CAqHd2WLZkTXUDTBxR9rxbUuU+n\nLejf/6OWAwLXnekmykYhzgLkaAE/+zaKyEvbfiIHxFCyMo5Z+mPD5KuKpdFM1NE5\ni0NwUJDPSJq+GBi3kWStaMP6RZPAWY/ZDIIa5qMCgYEAzleq/BkvjkgOu8WSDx25\nYhoThPOx4Zk86YBpIxUJQKV5iwK9c0MBollHGPB+cfJZmEcGoVzDdrqX0He0/U05\nBHMKkhiQWC61fSpCfWmkIczdCm3HLBxGmL2Vr44Dqz/R6LCYP8NPjGTiomOCnFpS\nj3H1Z7XvUNBOwHrgmA5HuEUCgYAPE+HzWAbaEMUHOdp0hKGWRA0YowFSv1GHCyUv\nWCBJztL2apZcMDb6c7CtUcqbudANLvkgRDlzgQSvNXJV3ugVXtETFRU6LCj6Da+M\ngQ2npL22P+YKJH65/1Jv0tw/RCFG8yZwcR69k4z0GV6a7o+9wbqm9GN72nW+Zl9k\n4jxd5QKBgQDxqPqK1FvI4GkESmrYgwfykENB67rQHk8o9TE8aMwsYqhKLeIpjmF3\njAv1XaNK65PC7pmqftNm6M3HN8pzLmu3iJPqHrxT+MZzqcw21+MWs0XgntmBNTWx\nY9s0TNQHimjh7RkVRj43e6QFI/rHF87IpixKBwoLAzUNH6daDninIg==\n-----END RSA PRIVATE KEY-----"


if __name__ == "__main__":
    print(decrypt(pk, "GHvhZkLLdNDxBg2Do93QhwUlXALNI9c/TRytSFNS/fTcDS/4vOzC/62iyjzrAccW6d6cuqcKg0XCs4i3J8PKPeyrFKXBeKgdYNcPt1A5Z9u46O/CvqaV0WHXJSMmOjMT7AHFHkrEXS5ecBoDHcAUfK/qtoVoNRnv/CxC1AMmoW1O2eFhvdL8gPuH9IkJnrlsflDa9h6AQxXJbowOcAL31GxgdKa+uejmCL83Oblz4Sjqc0/XE9SPTSVCdPJBDBnpqKMX8i9pRtPoJwHfTtNYd4aj7TAw8tN9R+a4aQ0KAchSiVi2qyffR5cfyJv8bh6tV7anWKXvMmeKhV0W+UFuQg=="))