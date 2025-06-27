# Cryptic - Providing data security in a zero-trust cloud storage environment


A secure file sharing system built using **Proxy Re-encryption** (PRE) technology with FastAPI backend and a web frontend. This system enables secure file sharing where files remain encrypted at all times, and access can be granted/revoked without exposing the original data.

<div align="center">
<img src="https://github.com/user-attachments/assets/427ca931-fdcf-4d90-86dd-7d533d0e4df2" alt="Cryptic File Manager Interface" width="800">
</div>

## What is Proxy Re-encryption?

**Proxy Re-encryption** is a cryptographic technique that allows a semi-trusted proxy to transform ciphertexts encrypted under one public key into ciphertexts encrypted under another public key, without the proxy learning anything about the underlying plaintext.

### How it Works:

1. **Key Generation**: Each user has a key pair (public/private keys) and signing keys
2. **Encryption**: Files are encrypted using the owner's public key
3. **Re-encryption Key Generation**: When access is granted, the owner generates a "re-encryption key" (kfrag) that allows transformation from owner's encryption to recipient's encryption
4. **Proxy Re-encryption**: The proxy (server) uses the re-encryption key to transform the ciphertext so it can be decrypted by the recipient
5. **Decryption**: The recipient can decrypt the transformed ciphertext using their private key

### Benefits:
- **Zero-knowledge proxy**: The server never sees the plaintext data
- **Fine-grained access control**: Access can be granted/revoked per file per user
- **No key sharing**: Users never share their private keys
- **Secure delegation**: Access delegation without compromising security

## Project Architecture

### Backend (FastAPI)
- **main.py**: Core API server with endpoints for file management and access control
- **MongoDB**: Three databases store different types of data:
  - `cryptic`: Encrypted files and granted access records
  - `client-keystore`: User key pairs (public/private keys)
  - `proxy-keystore`: Public keys visible to proxy and access requests

### Frontend (Web UI)
- **HTML/CSS/JavaScript** interface for file management
- Three main sections: My Files, Request Access, Grant/Deny Access
- Real-time interaction with the backend API

### Client SDKs
- **client-upload.py**: Upload and encrypt files
- **client-decrypt.py**: Download and decrypt accessible files

## Setup Instructions

### Prerequisites
- Python 3.8+
- MongoDB running on localhost:27017

### Installation
1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Start the backend server**:
   ```bash
   fastapi dev main.py
   ```

3. **Access the application**:
   - API documentation: http://localhost:8000/docs
   - Web frontend: Open `frontend/index.html` in a browser

### Important Notes
- Default owner ID: `pwnd`
- Default requester ID: `client2`
- Make sure MongoDB is running before starting the application

## How the System Works

### 1. File Upload Process
Using `client-upload.py`:
- User specifies a file to encrypt
- System generates/retrieves user's cryptographic keys
- File is encrypted line-by-line using the owner's public key
- Each line produces a `capsule` (metadata) and `ciphertext`
- Encrypted data is stored in MongoDB with metadata

### 2. Access Request Flow
1. **Request Access** (`/accessrequest`):
   - Requester submits a request for a specific file
   - System generates keys for requester if they don't exist
   - Access request is stored with status "pending"

2. **Grant/Deny Access** (`/accesscontrol`):
   - File owner reviews pending requests via web UI
   - If granted, system generates re-encryption keys (kfrags)
   - Original capsules are re-encrypted using kfrags
   - Re-encrypted fragments (cfrags) are stored for the requester

3. **File Access** (using `client-decrypt.py`):
   - Requester downloads the original ciphertext and their cfrags
   - Uses their private key to decrypt the re-encrypted data
   - Original file content is reconstructed

### 3. API Endpoints

#### File Management
- `GET /filelist`: List all files owned by a user
- `DELETE /deletefile`: Delete a file and all associated access

#### Access Control
- `POST /accessrequest`: Request access to a file
- `POST /accesscontrol`: Grant or deny access requests
- `GET /allrequests`: View all access requests for owned files
- `GET /revokeaccess`: Revoke previously granted access

### 4. Security Features

- **End-to-end encryption**: Files are encrypted before upload and remain encrypted in storage
- **Zero-knowledge proxy**: Server performs re-encryption without seeing plaintext
- **Key isolation**: Each user's private keys never leave their device
- **Granular permissions**: Access control per file per user
- **Audit trail**: All access requests and grants are logged

### 5. Database Schema

#### Collections:
- **encrypted_files**: Stores encrypted file data (capsules, ciphertext, metadata)
- **granted_files**: Stores re-encryption fragments for granted access
- **client_keypair**: User private key storage
- **proxy_public_keylist**: Public keys visible to the proxy
- **access_requests**: Pending and processed access requests

## Usage Example

1. **Upload a file**:
   ```bash
   python client-upload.py
   # Enter filename when prompted
   ```

2. **Request access** (via web UI or API):
   - Navigate to "Request Access" section
   - Enter the filename
   - Submit request

3. **Grant access** (via web UI):
   - File owner goes to "Grant/Deny" section
   - Reviews pending requests
   - Clicks "Grant" to allow access

4. **Download and decrypt**:
   ```bash
   python client-decrypt.py
   # Modify the script with correct file_name, owner_id, requester_id
   ```

## Technology Stack

- **Backend**: FastAPI, Python
- **Database**: MongoDB
- **Cryptography**: Umbral Proxy Re-encryption library
- **Frontend**: HTML, CSS, JavaScript
- **Key Libraries**: PyNaCl, cryptography, pymongo

This system demonstrates a practical implementation of proxy re-encryption for secure, scalable file sharing with fine-grained access control.
