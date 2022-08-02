#!/usr/bin/env python3

"""
AngeCryption from Mitra:
Take a polyglot from mitra,
make the file encrypt to another valid file via AES-CFB with a crafted IV
"""

import binascii
import argparse
from Crypto.Cipher import AES

BLOCKLEN = 16

pad = lambda s: s + b"\0" * (BLOCKLEN - (len(s) % BLOCKLEN)) 
b2a = lambda b: repr(b)[2:-1]

def unhextry(_d):
	try:
		_d = binascii.unhexlify(_d)
	except Exception:
		pass # TypeError: Non-hexadecimal digit found
	return _d


def getOverlap(fnin):
	assert "{" in fnin # is it required ?
	other_hdr = b""
	other_hdr = fnin[fnin.find("{")+1:]
	other_hdr = other_hdr[:other_hdr.find("}")]
	other_hdr = binascii.unhexlify(other_hdr)
	hdr_l = len(other_hdr)
	print(f"Other header read from filename: `{b2a(binascii.hexlify(other_hdr))}`")

	return other_hdr, hdr_l


def getSwap(fnin, hdr_l):
	assert "(" in fnin
	swaps = [int(i, 16) for i in fnin[fnin.find("(") + 1:fnin.find(")")].split("-")]
	assert len(swaps) == 2
	#assert swaps[0] == hdr_l
	assert swaps[1] % BLOCKLEN == 0
	return swaps[1]


if __name__=='__main__':
	parser = argparse.ArgumentParser(
		description="Turn an overlapping polyglot into a file staying valid after AES-CFB encryption.")
	parser.add_argument('polyglot',
		help=r"input polyglot - requires special naming like 'O(6-70){89504E470D0A}.png'.")
	parser.add_argument('output',
		help="generated file.")
	parser.add_argument('-k', '--key', nargs=1, default=b"AngeCryption!!!",
		help="encryption key - default: AngeCryption!!!.")

	args = parser.parse_args()

	fnin = args.polyglot
	fnpoc = args.output
	key = args.key
	key = b"\x01" * 16

	key = unhextry(key)
	key_s = b2a(binascii.hexlify(key))

	exts = fnin[-9:].split(".")[-2:]

	other_hdr, hdr_l = getOverlap(fnin)
	assert hdr_l <= BLOCKLEN
	swap = getSwap(fnin, hdr_l)

	with open(fnin, "rb") as file:
		dIn = file.read()

	# need swapping because Mitra produce parasite polyglots by default
	# and we need the top content parsed in plaintext.
	other_hdr, dIn = dIn[:hdr_l], other_hdr + dIn[hdr_l:]

	plain0 = dIn[:BLOCKLEN]
	# print("first plaintext block", plain0)

	cipher0 = other_hdr + dIn[len(other_hdr):BLOCKLEN]
	# print("other plaintext block:", cipher0)

	ecb_dec = AES.new(key, AES.MODE_ECB)
	# print("Other after decryption:", cipher0)

	# c = p ^ enc(iv) => iv = dec(p ^ c)
	iv = bytearray([cipher0[i] ^ plain0[i] for i in range(BLOCKLEN)])
	iv = ecb_dec.decrypt(iv)
	iv_s = b2a(binascii.hexlify(iv))

	cfb_enc = AES.new(key, AES.MODE_CFB, iv, segment_size=128)
	dOut = cfb_enc.encrypt(dIn[:swap]) + dIn[swap:]

	cfb_dec = AES.new(key, AES.MODE_CFB, iv, segment_size=128)
	dOut = cfb_dec.decrypt(pad(dOut))

	output = "\n".join(
		[
			f"plaintext: {b2a(binascii.hexlify(dOut))}",
			f"key: {b2a(binascii.hexlify(key))}",
			f"iv: {iv_s}",
			f'exts: {" ".join(exts)}',
			f"origin: {fnin}",
		]
	)


	fnoutput = f"{fnpoc}.{exts[0]}"
	print(f"Generated input file: {fnpoc}")
	with open(fnpoc, "wb") as fpoc:
		fpoc.write(output.encode())
		fpoc.close()
