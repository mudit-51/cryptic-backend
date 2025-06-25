from contextlib import asynccontextmanager
from fastapi import FastAPI
from pymongo import MongoClient
from pymongo.collection import Collection
from typing import TypedDict
from umbral import (
    Capsule,
    SecretKey,
    PublicKey,
    Signer,
    encrypt,
    generate_kfrags,
    reencrypt,
    decrypt_reencrypted,
)


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


@asynccontextmanager
async def lifespan(app: FastAPI):
    uri = "mongodb://localhost:27017/"
    app.state.mongoclient = MongoClient(uri)
    yield
    app.state.mongoclient.close()


app = FastAPI(lifespan=lifespan)


@app.get("/filelist")
async def get_file_list(client_id: str = ""):
    if not client_id:
        return {"error": "Client ID is required."}
    file_db = app.state.mongoclient["cryptic"]
    file_collection: Collection[EncryptedFile] = file_db["encrypted_files"]

    temp = file_collection.find({"client_id": client_id})
    file_list = list(
        file_collection.find({"client_id": client_id}, {"_id": 0, "file_name": 1})
    )
    return {"files": file_list}


@app.post("/accessrequest")
async def access_request(file_name: str, client_id: str, requester_id: str):
    if not file_name or not client_id or not requester_id:
        return {"error": "File name, client ID, and requester ID are required."}

    key_db = app.state.mongoclient["client-keystore"]
    key_collection: Collection[ClientKeyPair] = key_db["client_keypair"]
    proxy_db = app.state.mongoclient["proxy-keystore"]
    proxy_collection: Collection[ProxyKeyPair] = proxy_db["proxy_public_keylist"]
    proxy_access_collection: Collection[AccessRequest] = proxy_db["access_requests"]

    a_sk = SecretKey.random()
    a_pk = a_sk.public_key()
    a_signing = SecretKey.random()
    a_verifying = a_signing.public_key()

    id_existing = key_collection.find_one({"client_id": requester_id})
    if id_existing:
        a_sk = SecretKey.from_bytes(id_existing["secret_key"])
        a_pk = PublicKey.from_bytes(id_existing["public_key"])
        a_signing = SecretKey.from_bytes(id_existing["signing_key"])
        a_verifying = PublicKey.from_bytes(id_existing["verifying_key"])

    key_collection.update_one(
        filter={"client_id": requester_id},
        update={
            "$set": {
                "public_key": bytes(a_pk),
                "secret_key": a_sk.to_secret_bytes(),
                "signing_key": a_signing.to_secret_bytes(),
                "verifying_key": bytes(a_verifying),
                "client_id": requester_id,
            }
        },
        upsert=True,
    )
    if not id_existing:
        proxy_collection.update_one(
            filter={"client_id": requester_id},
            update={
                "$set": {
                    "public_key": bytes(a_pk),
                    "verifying_key": bytes(a_verifying),
                    "client_id": requester_id,
                }
            },
            upsert=True,
        )

    existing_request = proxy_access_collection.find_one(
        {"file_name": file_name, "client_id": client_id, "recipient_id": requester_id}
    )
    if existing_request:
        return {"message": "Access request already exists."}
    proxy_access_collection.insert_one(
        {
            "file_name": file_name,
            "client_id": client_id,
            "recipient_id": requester_id,
        }
    )
    return {"message": "Access request submitted successfully."}


@app.post("/accesscontrol")
async def grant_access(file_name: str, owner_id: str, requester_id: str, grant: bool):
    if not file_name or not owner_id or not requester_id:
        return {"error": "File name, owner ID, and requester ID are required."}

    file_db = app.state.mongoclient["cryptic"]
    file_collection: Collection[EncryptedFile] = file_db["encrypted_files"]
    granted_file_collection: Collection[GrantedFile] = file_db["granted_files"]
    key_db = app.state.mongoclient["client-keystore"]
    key_collection: Collection[ClientKeyPair] = key_db["client_keypair"]
    proxy_db = app.state.mongoclient["proxy-keystore"]
    proxy_key_collection: Collection[ProxyKeyPair] = proxy_db["proxy_public_keylist"]
    access_request_collection: Collection[AccessRequest] = proxy_db["access_requests"]

    if not grant:
        access_request_collection.delete_one(
            {
                "file_name": file_name,
                "client_id": owner_id,
                "recipient_id": requester_id,
            }
        )
        return {"message": "Access has been denied"}

    access_request = access_request_collection.find_one(
        {"file_name": file_name, "client_id": owner_id, "recipient_id": requester_id}
    )
    if not access_request:
        return {"error": "Access request not found."}

    access_check = granted_file_collection.find_one(
        {"file_name": file_name, "client_id": owner_id, "requester_id": requester_id}
    )
    if access_check:
        return {"message": "Access already granted for this file."}

    owner_keys = key_collection.find_one({"client_id": owner_id})
    if not owner_keys:
        return {"error": "Owner keys not found."}

    enc_file = file_collection.find_one({"file_name": file_name, "client_id": owner_id})
    if not enc_file:
        return {"error": "Encrypted file not found."}

    owner_sk = SecretKey.from_bytes(owner_keys["secret_key"])
    owner_signer = Signer(owner_sk)

    requester_keys = proxy_key_collection.find_one({"client_id": requester_id})
    if not requester_keys:
        return {"error": "Requester keys not found."}

    requester_pk = PublicKey.from_bytes(requester_keys["public_key"])

    capsules = enc_file["capsule"]

    kfrags = generate_kfrags(
        delegating_sk=owner_sk,
        receiving_pk=requester_pk,
        signer=owner_signer,
        threshold=1,
        shares=1,
    )
    cfrags: list[bytes] = []
    for capsule in capsules:
        cfrag = reencrypt(capsule=Capsule.from_bytes(capsule), kfrag=kfrags[0])
        cfrags.append(cfrag.__bytes__())

    granted_file_collection.insert_one(
        {
            "file_name": file_name,
            "client_id": owner_id,
            "requester_id": requester_id,
            "cfrags": cfrags,
        }
    )
    return {
        "message": "Access granted successfully.",
    }
