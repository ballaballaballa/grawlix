"""
Tests for encryption and decryption functionality.

Critical Priority Tests (CRT-010 to CRT-016):
- AES CBC decryption correctness
- AES CTR decryption with nonce handling
- XOR decryption
- PKCS7 padding removal
- Edge cases (empty data, single/multi-block)
- Error handling with incorrect keys
- Protocol type safety
"""

import pytest
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

from grawlix.encryption import (
    AESEncryption,
    AESCTREncryption,
    XOrEncryption,
    decrypt,
    Encryption,
)


# ============================================================================
# CRT-010: AES CBC Decryption with Known Plaintext/Ciphertext
# ============================================================================

class TestAESCBCDecryption:
    """Test AES CBC mode decryption correctness."""

    def test_aes_cbc_decrypt_simple(self):
        """CRT-010: Basic AES CBC decryption with known plaintext."""
        key = b"0123456789abcdef"  # 16 bytes (AES-128)
        iv = b"fedcba9876543210"   # 16 bytes
        plaintext = b"Hello, World!!!!"  # 16 bytes (1 block)

        # Encrypt with PyCryptodome
        cipher = AES.new(key, AES.MODE_CBC, iv)
        ciphertext = cipher.encrypt(plaintext)

        # Decrypt with our implementation
        encryption = AESEncryption(key=key, iv=iv)
        decrypted = encryption.decrypt(ciphertext)

        assert decrypted == plaintext

    def test_aes_cbc_decrypt_multiple_blocks(self):
        """CRT-010: AES CBC decryption with multiple blocks."""
        key = b"sixteen byte key"
        iv = b"sixteen byte iv!"
        # Create exactly 48 bytes (3 blocks of 16)
        plaintext = b"Block1Block1Blk1" + b"Block2Block2Blk2" + b"Block3Block3Blk3"

        # Ensure plaintext is multiple of 16
        assert len(plaintext) == 48
        assert len(plaintext) % 16 == 0

        # Encrypt
        cipher = AES.new(key, AES.MODE_CBC, iv)
        ciphertext = cipher.encrypt(plaintext)

        # Decrypt
        encryption = AESEncryption(key=key, iv=iv)
        decrypted = encryption.decrypt(ciphertext)

        assert decrypted == plaintext

    def test_aes_cbc_decrypt_with_padding(self):
        """CRT-010: AES CBC with PKCS7 padding (real-world scenario)."""
        key = b"sixteen byte key"
        iv = b"sixteen byte iv!"
        plaintext = b"Unaligned data"  # Not a multiple of 16

        # Encrypt with padding
        cipher = AES.new(key, AES.MODE_CBC, iv)
        padded_plaintext = pad(plaintext, AES.block_size)
        ciphertext = cipher.encrypt(padded_plaintext)

        # Decrypt (returns padded data)
        encryption = AESEncryption(key=key, iv=iv)
        decrypted_padded = encryption.decrypt(ciphertext)

        # The decrypt function returns padded data - caller must unpad
        assert decrypted_padded == padded_plaintext

    def test_aes_cbc_empty_data(self):
        """CRT-014: Empty data should decrypt to empty."""
        key = b"sixteen byte key"
        iv = b"sixteen byte iv!"

        encryption = AESEncryption(key=key, iv=iv)
        decrypted = encryption.decrypt(b"")

        assert decrypted == b""

    def test_aes_cbc_single_block(self):
        """CRT-014: Single block (16 bytes) decryption."""
        key = b"sixteen byte key"
        iv = b"sixteen byte iv!"
        plaintext = b"Exactly 16 bytes"

        # Encrypt
        cipher = AES.new(key, AES.MODE_CBC, iv)
        ciphertext = cipher.encrypt(plaintext)

        # Decrypt
        encryption = AESEncryption(key=key, iv=iv)
        decrypted = encryption.decrypt(ciphertext)

        assert decrypted == plaintext

    def test_aes_cbc_256_key(self):
        """CRT-010: AES-256 (32 byte key) decryption."""
        # Create exactly 32 bytes for AES-256
        key = b"0123456789abcdef0123456789abcdef"  # Exactly 32 bytes
        assert len(key) == 32
        iv = b"sixteen byte iv!"
        plaintext = b"Secret message!!"  # 16 bytes

        # Encrypt
        cipher = AES.new(key, AES.MODE_CBC, iv)
        ciphertext = cipher.encrypt(plaintext)

        # Decrypt
        encryption = AESEncryption(key=key, iv=iv)
        decrypted = encryption.decrypt(ciphertext)

        assert decrypted == plaintext


# ============================================================================
# CRT-011: AES CTR Decryption with Nonce Handling
# ============================================================================

class TestAESCTRDecryption:
    """Test AES CTR mode decryption with proper nonce handling."""

    def test_aes_ctr_decrypt_simple(self):
        """CRT-011: Basic AES CTR decryption."""
        key = b"sixteen byte key"
        nonce = b"12345678"  # 8 bytes
        initial_value = b"87654321"  # 8 bytes
        plaintext = b"Hello, World! This is CTR mode."

        # Encrypt with PyCryptodome
        cipher = AES.new(
            key=key,
            mode=AES.MODE_CTR,
            nonce=nonce,
            initial_value=initial_value
        )
        ciphertext = cipher.encrypt(plaintext)

        # Decrypt with our implementation
        encryption = AESCTREncryption(key=key, nonce=nonce, initial_value=initial_value)
        decrypted = encryption.decrypt(ciphertext)

        assert decrypted == plaintext

    def test_aes_ctr_no_padding_required(self):
        """CRT-011: CTR mode doesn't require padding (stream cipher)."""
        key = b"sixteen byte key"
        nonce = b"nonce123"
        initial_value = b"initval1"
        plaintext = b"Any length works"  # Not aligned to 16 bytes

        # Encrypt
        cipher = AES.new(
            key=key,
            mode=AES.MODE_CTR,
            nonce=nonce,
            initial_value=initial_value
        )
        ciphertext = cipher.encrypt(plaintext)

        # Decrypt
        encryption = AESCTREncryption(key=key, nonce=nonce, initial_value=initial_value)
        decrypted = encryption.decrypt(ciphertext)

        assert decrypted == plaintext
        assert len(decrypted) == len(plaintext)  # No padding added

    def test_aes_ctr_large_data(self):
        """CRT-011: CTR mode with large data (multiple blocks)."""
        key = b"sixteen byte key"
        nonce = b"12345678"
        initial_value = b"87654321"
        plaintext = b"Large data " * 1000  # ~11KB

        # Encrypt
        cipher = AES.new(
            key=key,
            mode=AES.MODE_CTR,
            nonce=nonce,
            initial_value=initial_value
        )
        ciphertext = cipher.encrypt(plaintext)

        # Decrypt
        encryption = AESCTREncryption(key=key, nonce=nonce, initial_value=initial_value)
        decrypted = encryption.decrypt(ciphertext)

        assert decrypted == plaintext

    def test_aes_ctr_empty_data(self):
        """CRT-014: CTR mode with empty data."""
        key = b"sixteen byte key"
        nonce = b"12345678"
        initial_value = b"87654321"

        encryption = AESCTREncryption(key=key, nonce=nonce, initial_value=initial_value)
        decrypted = encryption.decrypt(b"")

        assert decrypted == b""

    def test_aes_ctr_different_nonces_different_output(self):
        """CRT-011: Different nonces should produce different ciphertexts."""
        key = b"sixteen byte key"
        plaintext = b"Same plaintext"

        # Encrypt with nonce1
        cipher1 = AES.new(
            key=key,
            mode=AES.MODE_CTR,
            nonce=b"nonce111",
            initial_value=b"initval1"
        )
        ciphertext1 = cipher1.encrypt(plaintext)

        # Encrypt with nonce2
        cipher2 = AES.new(
            key=key,
            mode=AES.MODE_CTR,
            nonce=b"nonce222",
            initial_value=b"initval1"
        )
        ciphertext2 = cipher2.encrypt(plaintext)

        # Ciphertexts should be different
        assert ciphertext1 != ciphertext2

        # But both should decrypt correctly
        enc1 = AESCTREncryption(key=key, nonce=b"nonce111", initial_value=b"initval1")
        enc2 = AESCTREncryption(key=key, nonce=b"nonce222", initial_value=b"initval1")

        assert enc1.decrypt(ciphertext1) == plaintext
        assert enc2.decrypt(ciphertext2) == plaintext


# ============================================================================
# CRT-012: XOR Decryption
# ============================================================================

class TestXORDecryption:
    """Test XOR encryption/decryption (simple but critical)."""

    def test_xor_decrypt_simple(self):
        """CRT-012: Basic XOR decryption."""
        key = b"secret"
        plaintext = b"Hello, World!"

        # XOR encrypt manually
        ciphertext = bytes([plaintext[i] ^ key[i % len(key)] for i in range(len(plaintext))])

        # Decrypt with our implementation
        encryption = XOrEncryption(key=key)
        decrypted = encryption.decrypt(ciphertext)

        assert decrypted == plaintext

    def test_xor_symmetric_property(self):
        """CRT-012: XOR decryption is same as encryption (symmetric)."""
        key = b"testkey"
        data = b"Some data to encrypt"

        encryption = XOrEncryption(key=key)

        # Encrypt
        encrypted = encryption.decrypt(data)  # decrypt is same as encrypt for XOR

        # Decrypt
        decrypted = encryption.decrypt(encrypted)

        assert decrypted == data

    def test_xor_key_shorter_than_data(self):
        """CRT-012: XOR with key shorter than data (key repeats)."""
        key = b"short"
        plaintext = b"This is a much longer message than the key"

        # XOR encrypt
        ciphertext = bytes([plaintext[i] ^ key[i % len(key)] for i in range(len(plaintext))])

        # Decrypt
        encryption = XOrEncryption(key=key)
        decrypted = encryption.decrypt(ciphertext)

        assert decrypted == plaintext

    def test_xor_key_longer_than_data(self):
        """CRT-012: XOR with key longer than data."""
        key = b"this is a very long key that is longer than the data"
        plaintext = b"Short"

        # XOR encrypt
        ciphertext = bytes([plaintext[i] ^ key[i % len(key)] for i in range(len(plaintext))])

        # Decrypt
        encryption = XOrEncryption(key=key)
        decrypted = encryption.decrypt(ciphertext)

        assert decrypted == plaintext

    def test_xor_single_byte_key(self):
        """CRT-012: XOR with single byte key."""
        key = b"X"
        plaintext = b"Test data"

        # XOR encrypt
        ciphertext = bytes([b ^ key[0] for b in plaintext])

        # Decrypt
        encryption = XOrEncryption(key=key)
        decrypted = encryption.decrypt(ciphertext)

        assert decrypted == plaintext

    def test_xor_empty_data(self):
        """CRT-014: XOR with empty data."""
        key = b"key"
        encryption = XOrEncryption(key=key)

        decrypted = encryption.decrypt(b"")
        assert decrypted == b""

    def test_xor_binary_data(self):
        """CRT-012: XOR with binary data (not just text)."""
        key = b"\x00\xFF\x00\xFF"
        plaintext = b"\x12\x34\x56\x78\x9A\xBC\xDE\xF0"

        # XOR encrypt
        ciphertext = bytes([plaintext[i] ^ key[i % len(key)] for i in range(len(plaintext))])

        # Decrypt
        encryption = XOrEncryption(key=key)
        decrypted = encryption.decrypt(ciphertext)

        assert decrypted == plaintext


# ============================================================================
# CRT-015: Error Handling with Incorrect Keys
# ============================================================================

class TestDecryptionErrorHandling:
    """Test graceful handling of decryption with wrong keys."""

    def test_aes_cbc_wrong_key(self):
        """CRT-015: Decryption with wrong key should not crash."""
        correct_key = b"correct key 1234"
        wrong_key = b"wrong key here!!"
        iv = b"sixteen byte iv!"
        plaintext = b"Secret message!!"

        # Encrypt with correct key
        cipher = AES.new(correct_key, AES.MODE_CBC, iv)
        ciphertext = cipher.encrypt(plaintext)

        # Try to decrypt with wrong key - should not crash
        encryption = AESEncryption(key=wrong_key, iv=iv)
        decrypted = encryption.decrypt(ciphertext)

        # Should decrypt but produce garbage (not crash)
        assert decrypted != plaintext
        assert len(decrypted) == len(plaintext)

    def test_aes_cbc_wrong_iv(self):
        """CRT-015: Decryption with wrong IV should not crash."""
        key = b"correct key 1234"
        correct_iv = b"correct IV here!"
        wrong_iv = b"wrong IV here!!!"
        plaintext = b"Secret message!!"

        # Encrypt with correct IV
        cipher = AES.new(key, AES.MODE_CBC, correct_iv)
        ciphertext = cipher.encrypt(plaintext)

        # Decrypt with wrong IV - should not crash
        encryption = AESEncryption(key=key, iv=wrong_iv)
        decrypted = encryption.decrypt(ciphertext)

        # Should decrypt but first block will be wrong
        assert decrypted != plaintext
        assert len(decrypted) == len(plaintext)

    def test_aes_ctr_wrong_nonce(self):
        """CRT-015: CTR mode with wrong nonce produces garbage (no crash)."""
        key = b"sixteen byte key"
        correct_nonce = b"nonce123"
        wrong_nonce = b"wrong456"
        initial_value = b"initval1"
        plaintext = b"Secret data"

        # Encrypt with correct nonce
        cipher = AES.new(
            key=key,
            mode=AES.MODE_CTR,
            nonce=correct_nonce,
            initial_value=initial_value
        )
        ciphertext = cipher.encrypt(plaintext)

        # Decrypt with wrong nonce - should not crash
        encryption = AESCTREncryption(key=key, nonce=wrong_nonce, initial_value=initial_value)
        decrypted = encryption.decrypt(ciphertext)

        # Should produce garbage
        assert decrypted != plaintext
        assert len(decrypted) == len(plaintext)

    def test_xor_wrong_key(self):
        """CRT-015: XOR with wrong key produces garbage (no crash)."""
        correct_key = b"correct"
        wrong_key = b"wronggg"
        plaintext = b"Secret message"

        # Encrypt with correct key
        ciphertext = bytes([plaintext[i] ^ correct_key[i % len(correct_key)] for i in range(len(plaintext))])

        # Decrypt with wrong key - should not crash
        encryption = XOrEncryption(key=wrong_key)
        decrypted = encryption.decrypt(ciphertext)

        # Should produce garbage
        assert decrypted != plaintext


# ============================================================================
# CRT-016: Protocol Type Safety
# ============================================================================

class TestEncryptionProtocol:
    """Test the Encryption protocol interface."""

    def test_aes_encryption_implements_protocol(self):
        """CRT-016: AESEncryption implements Encryption protocol."""
        key = b"sixteen byte key"
        iv = b"sixteen byte iv!"
        encryption: Encryption = AESEncryption(key=key, iv=iv)

        # Should have decrypt method
        assert hasattr(encryption, 'decrypt')
        assert callable(encryption.decrypt)

    def test_aes_ctr_encryption_implements_protocol(self):
        """CRT-016: AESCTREncryption implements Encryption protocol."""
        encryption: Encryption = AESCTREncryption(
            key=b"sixteen byte key",
            nonce=b"12345678",
            initial_value=b"87654321"
        )

        assert hasattr(encryption, 'decrypt')
        assert callable(encryption.decrypt)

    def test_xor_encryption_implements_protocol(self):
        """CRT-016: XOrEncryption implements Encryption protocol."""
        encryption: Encryption = XOrEncryption(key=b"testkey")

        assert hasattr(encryption, 'decrypt')
        assert callable(encryption.decrypt)

    def test_decrypt_function_accepts_protocol(self):
        """CRT-016: Generic decrypt() function works with any Encryption."""
        key = b"sixteen byte key"
        iv = b"sixteen byte iv!"
        plaintext = b"Test message!!!!"

        # Encrypt
        cipher = AES.new(key, AES.MODE_CBC, iv)
        ciphertext = cipher.encrypt(plaintext)

        # Use generic decrypt function
        encryption: Encryption = AESEncryption(key=key, iv=iv)
        decrypted = decrypt(ciphertext, encryption)

        assert decrypted == plaintext

    def test_decrypt_function_with_all_encryption_types(self):
        """CRT-016: Generic decrypt() works with all encryption types."""
        # Test data
        plaintext = b"Test message!!!!"

        # Test with AES CBC
        aes_key = b"sixteen byte key"
        aes_iv = b"sixteen byte iv!"
        cipher = AES.new(aes_key, AES.MODE_CBC, aes_iv)
        aes_ciphertext = cipher.encrypt(plaintext)
        aes_enc = AESEncryption(key=aes_key, iv=aes_iv)
        assert decrypt(aes_ciphertext, aes_enc) == plaintext

        # Test with AES CTR
        ctr_key = b"sixteen byte key"
        ctr_nonce = b"12345678"
        ctr_iv = b"87654321"
        cipher = AES.new(ctr_key, AES.MODE_CTR, nonce=ctr_nonce, initial_value=ctr_iv)
        ctr_ciphertext = cipher.encrypt(plaintext)
        ctr_enc = AESCTREncryption(key=ctr_key, nonce=ctr_nonce, initial_value=ctr_iv)
        assert decrypt(ctr_ciphertext, ctr_enc) == plaintext

        # Test with XOR
        xor_key = b"secretkey"
        xor_ciphertext = bytes([plaintext[i] ^ xor_key[i % len(xor_key)] for i in range(len(plaintext))])
        xor_enc = XOrEncryption(key=xor_key)
        assert decrypt(xor_ciphertext, xor_enc) == plaintext


# ============================================================================
# Edge Cases and Real-World Scenarios
# ============================================================================

class TestRealWorldScenarios:
    """Test scenarios that might occur with actual ebook files."""

    def test_large_file_decryption_aes(self):
        """Test decrypting data similar to ebook file size."""
        key = b"sixteen byte key"
        iv = b"sixteen byte iv!"

        # Simulate 1MB file
        plaintext = b"Chapter content " * 65536  # ~1MB

        # Pad to AES block size
        from Crypto.Util.Padding import pad
        padded = pad(plaintext, AES.block_size)

        # Encrypt
        cipher = AES.new(key, AES.MODE_CBC, iv)
        ciphertext = cipher.encrypt(padded)

        # Decrypt
        encryption = AESEncryption(key=key, iv=iv)
        decrypted = encryption.decrypt(ciphertext)

        assert decrypted == padded

    def test_epub_like_data_xor(self):
        """Test XOR decryption with EPUB-like binary data."""
        key = b"epub_key"

        # Simulate EPUB (ZIP) file header
        plaintext = b"PK\x03\x04\x14\x00\x00\x00" + b"\x00" * 100

        # Encrypt
        ciphertext = bytes([plaintext[i] ^ key[i % len(key)] for i in range(len(plaintext))])

        # Decrypt
        encryption = XOrEncryption(key=key)
        decrypted = encryption.decrypt(ciphertext)

        assert decrypted == plaintext
        assert decrypted.startswith(b"PK\x03\x04")  # Valid ZIP signature

    def test_mixed_encryption_types_in_sequence(self):
        """Test using different encryption types for different files."""
        plaintext = b"Book content!!!!"

        # File 1: AES CBC
        aes_enc = AESEncryption(key=b"key1" + b"\x00" * 12, iv=b"iv1" + b"\x00" * 13)
        cipher = AES.new(b"key1" + b"\x00" * 12, AES.MODE_CBC, b"iv1" + b"\x00" * 13)
        aes_cipher = cipher.encrypt(plaintext)
        assert aes_enc.decrypt(aes_cipher) == plaintext

        # File 2: XOR
        xor_enc = XOrEncryption(key=b"key2")
        xor_cipher = bytes([plaintext[i] ^ b"key2"[i % 4] for i in range(len(plaintext))])
        assert xor_enc.decrypt(xor_cipher) == plaintext

        # File 3: AES CTR
        ctr_enc = AESCTREncryption(
            key=b"key3" + b"\x00" * 12,
            nonce=b"nonce123",
            initial_value=b"initval1"
        )
        cipher = AES.new(
            b"key3" + b"\x00" * 12,
            AES.MODE_CTR,
            nonce=b"nonce123",
            initial_value=b"initval1"
        )
        ctr_cipher = cipher.encrypt(plaintext)
        assert ctr_enc.decrypt(ctr_cipher) == plaintext
