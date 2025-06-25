from umbral import (
    SecretKey,
    PublicKey,
    Signer,
    VerifiedCapsuleFrag,
    encrypt,
    generate_kfrags,
    reencrypt,
    decrypt_reencrypted,
    Capsule,
)

from pymongo import MongoClient
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


class AccessRequest(TypedDict):
    file_name: str
    client_id: str
    recipient_id: str

class GrantedFile(TypedDict):
    file_name: str
    client_id: str
    requester_id: str
    cfrags: list[bytes]



uri = "mongodb://localhost:27017/"
client = MongoClient(uri)
file_db = client["cryptic"]
file_collection: Collection[EncryptedFile] = file_db["encrypted_files"]
granted_files_collection: Collection[GrantedFile] = file_db["granted_files"]

key_db = client["client-keystore"]
key_collection: Collection[ClientKeyPair] = key_db["client_keypair"]

proxy_db = client["proxy-keystore"]
proxy_collection: Collection[ClientKeyPair] = proxy_db["proxy_public_keylist"]

# Prompt for file and user info
file_name = "requirements.txt"
owner_id = "pwnd"
r_id = "client2"

# Fetch keys from DB
owner_keys = proxy_collection.find_one({"client_id": owner_id})

r_keys = key_collection.find_one({"client_id": r_id})

if not r_keys:
    print("Keys for decryption not found. Exiting...")
    exit(0)

if not r_id:
    print("Client ID cannot be empty.")
    exit(1)
if not owner_keys:
    print("Owner or receiver keys not found.")
    exit(1)


enc_file = file_collection.find_one({"file_name": file_name, "client_id": owner_id})
if not enc_file:
    print("Encrypted file not found.")
    exit(1)

granted_file = granted_files_collection.find_one({"file_name": file_name, "client_id": owner_id, "requester_id": r_id})
if not granted_file:
    print("Decryption target not found")
    exit(0)
    
decrypted_lines = []
for idx, (capsule_bytes, ciphertext) in enumerate(zip(enc_file["capsule"], enc_file["ciphertext"])):
    capsule = Capsule.from_bytes(capsule_bytes)
    
    cfrag = VerifiedCapsuleFrag.from_verified_bytes(granted_file["cfrags"][idx])
    cleartext = decrypt_reencrypted(
        receiving_sk=SecretKey.from_bytes(r_keys["secret_key"]),
        delegating_pk=PublicKey.from_bytes(owner_keys["public_key"]),
        capsule=capsule,
        verified_cfrags=[cfrag],
        ciphertext=ciphertext,
    )
    decrypted_lines.append(cleartext.decode())

print("Decrypted file content:")
print("".join(decrypted_lines))
