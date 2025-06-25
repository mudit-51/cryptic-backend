from umbral import (
    SecretKey,
    PublicKey,
    Signer,
    encrypt,
    generate_kfrags,
    reencrypt,
    decrypt_reencrypted,
)

from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection
from typing import TypedDict


class ClientKeyPair(TypedDict):
    public_key: bytes
    secret_key: bytes
    signing_key: bytes
    verifying_key: bytes
    client_id: str

class ProxyKeyPair(TypedDict):
    public_key: bytes
    verifying_key: bytes
    client_id: str

class EncryptedFile(TypedDict):
    capsule: list[bytes]
    ciphertext: list[bytes]
    client_id: str


uri = "mongodb://localhost:27017/"
client = MongoClient(uri)
file_db = client["cryptic"]
file_collection: Collection[EncryptedFile] = file_db["encrypted_files"]

key_db = client["client-keystore"]
key_collection: Collection[ClientKeyPair] = key_db["client_keypair"]

proxy_db = client["proxy-keystore"]
proxy_collection: Collection[ClientKeyPair] = proxy_db["proxy_public_keylist"]

file_name = input("Enter the file name to encrypt and upload: ")
a_id = input("Enter your client id: ")

a_sk = SecretKey.random()
a_pk = a_sk.public_key()
a_signing = SecretKey.random()
a_verifying = a_signing.public_key()

id_existing = key_collection.find_one({"client_id": a_id})
if id_existing:
    a_sk = SecretKey.from_bytes(id_existing["secret_key"])
    a_pk = PublicKey.from_bytes(id_existing["public_key"])
    a_signing = SecretKey.from_bytes(id_existing["signing_key"])
    a_verifying = PublicKey.from_bytes(id_existing["verifying_key"])

key_collection.update_one(
    filter={"client_id": a_id},
    update={
        "$set": {
            "public_key": bytes(a_pk),
            "secret_key": a_sk.to_secret_bytes(),
            "signing_key": a_signing.to_secret_bytes(),
            "verifying_key": bytes(a_verifying),
            "client_id": a_id,
        }
    },
    upsert=True,
)
if not id_existing:
    proxy_collection.update_one(
        filter={"client_id": a_id},
        update={
            "$set": {
                "public_key": bytes(a_pk),
                "verifying_key": bytes(a_verifying),
                "client_id": a_id,
            }
        },
        upsert=True,
    )

a_signer = Signer(a_signing)

capsules = []
ciphertexts = []
try:
    with open(file_name, "r") as f:
        for line in f:
            capsule, ciphertext = encrypt(a_pk, line.encode())
            capsules.append(capsule.__bytes__())
            ciphertexts.append(ciphertext)
except FileNotFoundError:
    print(f"File {file_name} not found.")
    exit(1)

file_collection.update_one(
    filter={"file_name": file_name, "client_id": a_id},
    update={
        "$set": {
            "capsule": capsules,
            "ciphertext": ciphertexts,
            "client_id": a_id,
        }
    },
    upsert=True,
)

print(f"File {file_name} encrypted and uploaded successfully.")