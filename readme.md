### Instructions

1. `pip install -r requirements.txt`
2.  `fastapi dev`
3. docs accessible at /docs at whatever address you run the server
4. Make sure in all api requests, client/owner_id is 'pwnd' and requester_id is 'client2'

### Flow of API requests

1. Upload using SDK (client-upload.py)
2. User makes access request to file (/accessrequest)
3. File owner accept/reject request (/accesscontrol)
4. If accept, file is downloaded and decrypted using the sdk (client-decrypt.py)