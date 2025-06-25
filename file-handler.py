from umbral import SecretKey, Signer, encrypt, generate_kfrags, reencrypt, decrypt_reencrypted
import sys

a_sk = SecretKey.random()
a_pk = a_sk.public_key()

b_sk = SecretKey.random()
b_pk = b_sk.public_key()

a_signing = SecretKey.random()
a_verifying = a_signing.public_key()

a_signer = Signer(a_signing)

capsules = []
ciphertexts = []
with open("test.txt", "r") as f:
    for line in f:
        capsule, ciphertext = encrypt(a_pk, line.encode())
        capsules.append(capsule)
        ciphertexts.append(ciphertext)
        # print(f"Capsule: {sys.getsizeof(capsule)}")
        # print(f"Ciphertext: {len(ciphertext)}")

kfrag = generate_kfrags(delegating_sk=a_sk,
                         receiving_pk=b_pk,
                         signer=a_signer,
                         threshold=1,
                         shares=1)[0]

cfrags = []
for i in range(len(capsules)):
    cfrags.append(reencrypt(capsule=capsules[i],kfrag= kfrag))
    
for i in range(len(ciphertexts)):
    cleartext = decrypt_reencrypted(receiving_sk=b_sk,
                                    delegating_pk=a_pk,
                                    capsule=capsules[i],
                                    verified_cfrags=[cfrags[i]],
                                    ciphertext=ciphertexts[i],)
    print(cleartext)