import os
import json

KEY = 0x5A

def encrypt_data(data: bytes) -> bytes:
    return bytes([b ^ KEY for b in data])

def decrypt_data(data: bytes) -> bytes:
    return bytes([b ^ KEY for b in data])

def save_records_encrypted(records: dict, path: str = "records.dat") -> None:
    json_str = json.dumps(records, ensure_ascii=False).encode('utf-8')
    encrypted = encrypt_data(json_str)
    with open(path, "wb") as f:
        f.write(encrypted)

def load_records_encrypted(path: str = "records.dat") -> dict:
    default = {
        "story_score": 0,
        "endless_score": 0,
        "unlocked_characters": ["ars"],
        "disclaimer_shown": False
    }
    if not os.path.exists(path):
        return default
    with open(path, "rb") as f:
        encrypted = f.read()
    try:
        decrypted = decrypt_data(encrypted)
        data = json.loads(decrypted.decode('utf-8'))
        # Добавляем недостающие поля
        for k, v in default.items():
            if k not in data:
                data[k] = v
        return data
    except:
        return default
