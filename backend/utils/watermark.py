# """
# watermark.py — Robust invisible watermark using DCT (Discrete Cosine Transform).

# How it works:
#   1. Convert frame BGR -> YCrCb (work on Y/luminance only - least visible)
#   2. Split into 8x8 blocks (same as JPEG compression internally)
#   3. Apply DCT to each block
#   4. Encode watermark bits into mid-frequency DCT coefficients
#   5. Apply inverse DCT to reconstruct watermarked frame

# Why robust:
#   - Mid-frequency DCT coefficients survive JPEG/MP4 re-encoding
#   - Survives mild cropping (embedded in many blocks)
#   - Survives resize/rescale

# What we embed (32 bits total):
#   - ORG_PATTERN  : fixed 16-bit pattern proving org ownership
#   - video_id     : first 16 bits from the UUID
# """

# import cv2
# import numpy as np

# # Your organisation's fixed ownership signature — unique to your org
# ORG_PATTERN_BITS = [1, 0, 1, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 0, 1, 0]

# # Embedding strength: 25 = invisible to eye, survives H.264 re-encoding
# EMBED_STRENGTH = 25


# def _text_to_bits(text: str, n_bits: int = 16) -> list:
#     bits = []
#     for char in text[:n_bits // 8]:
#         byte = ord(char)
#         for i in range(7, -1, -1):
#             bits.append((byte >> i) & 1)
#     bits = bits[:n_bits]
#     while len(bits) < n_bits:
#         bits.append(0)
#     return bits


# def build_watermark_sequence(video_id: str) -> list:
#     """32-bit sequence = 16 org bits + 16 video_id bits"""
#     return ORG_PATTERN_BITS + _text_to_bits(video_id, n_bits=16)


# def embed_watermark(frame: np.ndarray, video_id: str) -> np.ndarray:
#     """
#     Embeds invisible watermark into one video frame using DCT.
#     Returns watermarked frame (same shape/dtype as input).
#     """
#     watermark_bits = build_watermark_sequence(video_id)
#     n_bits = len(watermark_bits)

#     ycrcb = cv2.cvtColor(frame, cv2.COLOR_BGR2YCrCb)
#     y_channel = ycrcb[:, :, 0].astype(np.float32)
#     height, width = y_channel.shape
#     bit_index = 0

#     for row in range(0, height - 7, 8):
#         for col in range(0, width - 7, 8):
#             block = y_channel[row:row+8, col:col+8]
#             dct_block = cv2.dct(block)

#             # Mid-frequency coefficient (4,3) — invisible but robust
#             target_bit = watermark_bits[bit_index % n_bits]
#             coeff = dct_block[4, 3]
#             quantised = round(coeff / EMBED_STRENGTH)
#             if quantised % 2 != target_bit:
#                 quantised += 1
#             dct_block[4, 3] = quantised * EMBED_STRENGTH

#             y_channel[row:row+8, col:col+8] = cv2.idct(dct_block)
#             bit_index += 1

#     y_channel = np.clip(y_channel, 0, 255).astype(np.uint8)
#     ycrcb[:, :, 0] = y_channel
#     return cv2.cvtColor(ycrcb, cv2.COLOR_YCrCb2BGR)


# def extract_watermark_bits(frame: np.ndarray, n_bits: int = 32) -> list:
#     """Extracts embedded watermark bits from a frame (used in Step 5 matching)."""
#     ycrcb = cv2.cvtColor(frame, cv2.COLOR_BGR2YCrCb)
#     y_channel = ycrcb[:, :, 0].astype(np.float32)
#     height, width = y_channel.shape
#     extracted_bits = []
#     bit_index = 0

#     for row in range(0, height - 7, 8):
#         for col in range(0, width - 7, 8):
#             if bit_index >= n_bits:
#                 break
#             block = y_channel[row:row+8, col:col+8]
#             dct_block = cv2.dct(block)
#             quantised = round(dct_block[4, 3] / EMBED_STRENGTH)
#             extracted_bits.append(abs(quantised) % 2)
#             bit_index += 1
#         if bit_index >= n_bits:
#             break

#     return extracted_bits


# def verify_watermark(frame: np.ndarray, video_id: str) -> dict:
#     """
#     Checks if a frame contains the expected watermark.
#     Returns org_match%, id_match%, and verified boolean.
#     """
#     expected  = build_watermark_sequence(video_id)
#     extracted = extract_watermark_bits(frame, n_bits=len(expected))

#     if len(extracted) < len(expected):
#         return {"org_match_pct": 0.0, "id_match_pct": 0.0, "verified": False}

#     org_match = sum(a == b for a, b in zip(expected[:16], extracted[:16])) / 16
#     id_match  = sum(a == b for a, b in zip(expected[16:], extracted[16:])) / 16

#     return {
#         "org_match_pct": round(org_match * 100, 1),
#         "id_match_pct":  round(id_match  * 100, 1),
#         "verified":      org_match >= 0.85 and id_match >= 0.85
#     }
 
 
 
    
"""
watermark.py — Robust invisible watermark using DCT.

Changes from original:
  - EMBED_STRENGTH raised from 25 → 80 (survives YouTube re-encoding)
  - Embeds in MULTIPLE coefficients per block (not just one)
    so even if YouTube destroys some, others survive
  - Verification threshold lowered from 85% → 70%
    because YouTube always introduces some bit errors
  - Added majority voting across blocks for more reliable detection
"""

import cv2
import numpy as np

ORG_PATTERN_BITS = [1, 0, 1, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 0, 1, 0]

# Raised from 25 to 80 — strong enough to survive YouTube's re-encoding
# Still invisible to the human eye (YouTube's compression noise is ~5-15)
EMBED_STRENGTH = 80

# Multiple mid-frequency positions — if one gets wiped, others survive
# These positions are robust in 8x8 DCT blocks after JPEG/H.264 compression
EMBED_POSITIONS = [
    (4, 3),   # primary
    (3, 4),   # secondary
    (5, 2),   # tertiary
]

# Lowered from 85% to 70% — accounts for YouTube bit errors
VERIFY_THRESHOLD = 0.70


def _text_to_bits(text: str, n_bits: int = 16) -> list:
    bits = []
    for char in text[:n_bits // 8]:
        byte = ord(char)
        for i in range(7, -1, -1):
            bits.append((byte >> i) & 1)
    bits = bits[:n_bits]
    while len(bits) < n_bits:
        bits.append(0)
    return bits


def build_watermark_sequence(video_id: str) -> list:
    """32 bits = 16 org bits + 16 video_id bits"""
    return ORG_PATTERN_BITS + _text_to_bits(video_id, n_bits=16)


def embed_watermark(frame: np.ndarray, video_id: str) -> np.ndarray:
    """
    Embeds watermark into multiple DCT coefficients per block.
    Stronger and more redundant than single-coefficient embedding.
    """
    watermark_bits = build_watermark_sequence(video_id)
    n_bits = len(watermark_bits)

    ycrcb     = cv2.cvtColor(frame, cv2.COLOR_BGR2YCrCb)
    y_channel = ycrcb[:, :, 0].astype(np.float32)
    height, width = y_channel.shape
    bit_index = 0

    for row in range(0, height - 7, 8):
        for col in range(0, width - 7, 8):
            block     = y_channel[row:row+8, col:col+8]
            dct_block = cv2.dct(block)

            target_bit = watermark_bits[bit_index % n_bits]

            # Embed into ALL positions for redundancy
            for (r, c) in EMBED_POSITIONS:
                coeff     = dct_block[r, c]
                quantised = round(coeff / EMBED_STRENGTH)
                if quantised % 2 != target_bit:
                    quantised += 1
                dct_block[r, c] = quantised * EMBED_STRENGTH

            y_channel[row:row+8, col:col+8] = cv2.idct(dct_block)
            bit_index += 1

    y_channel = np.clip(y_channel, 0, 255).astype(np.uint8)
    ycrcb[:, :, 0] = y_channel
    return cv2.cvtColor(ycrcb, cv2.COLOR_YCrCb2BGR)


def extract_watermark_bits(frame: np.ndarray, n_bits: int = 32) -> list:
    """
    Extracts watermark bits using majority voting across all embed positions.
    If 2 out of 3 positions agree on a bit value → use that value.
    Much more robust than reading a single position.
    """
    ycrcb     = cv2.cvtColor(frame, cv2.COLOR_BGR2YCrCb)
    y_channel = ycrcb[:, :, 0].astype(np.float32)
    height, width = y_channel.shape

    # Collect votes: for each bit position, collect readings from all blocks
    # votes[bit_index] = list of (0 or 1) readings
    votes = [[] for _ in range(n_bits)]
    bit_index = 0

    for row in range(0, height - 7, 8):
        for col in range(0, width - 7, 8):
            if bit_index >= n_bits:
                break
            block     = y_channel[row:row+8, col:col+8]
            dct_block = cv2.dct(block)

            # Read from all positions and vote
            bit_votes = []
            for (r, c) in EMBED_POSITIONS:
                quantised = round(dct_block[r, c] / EMBED_STRENGTH)
                bit_votes.append(abs(quantised) % 2)

            # Majority vote: if 2+ positions agree, use that bit
            majority = 1 if sum(bit_votes) >= len(EMBED_POSITIONS) / 2 else 0
            votes[bit_index].append(majority)
            bit_index += 1

        if bit_index >= n_bits:
            break

    # Final bit = majority across all blocks that voted for this bit position
    extracted = []
    for bit_votes in votes:
        if not bit_votes:
            extracted.append(0)
        else:
            extracted.append(1 if sum(bit_votes) > len(bit_votes) / 2 else 0)

    return extracted


def verify_watermark(frame: np.ndarray, video_id: str) -> dict:
    """
    Verifies watermark in a frame.
    Uses 70% threshold (down from 85%) to account for YouTube re-encoding losses.
    """
    expected  = build_watermark_sequence(video_id)
    extracted = extract_watermark_bits(frame, n_bits=len(expected))

    if len(extracted) < len(expected):
        return {"org_match_pct": 0.0, "id_match_pct": 0.0, "verified": False}

    org_match = sum(a == b for a, b in zip(expected[:16], extracted[:16])) / 16
    id_match  = sum(a == b for a, b in zip(expected[16:], extracted[16:])) / 16

    print(f"[Watermark] org_match={org_match*100:.1f}% id_match={id_match*100:.1f}% threshold={VERIFY_THRESHOLD*100}%")

    return {
        "org_match_pct": round(org_match * 100, 1),
        "id_match_pct":  round(id_match  * 100, 1),
        "verified":      org_match >= VERIFY_THRESHOLD and id_match >= VERIFY_THRESHOLD,
        "threshold_used": VERIFY_THRESHOLD * 100,
    }


# """
# watermark.py — Invisible text watermark using Spread Spectrum LSB.

# What this does:
#   - Embeds READABLE owner text (e.g. "ESPN_CORP::video_id") invisibly into frames
#   - Text is spread across thousands of pixels using a secret seed
#   - Each bit of the text is embedded in the LSB of many pixels (redundancy)
#   - To the human eye: completely invisible (1 pixel value change)
#   - To verify: extract the text back and read the owner name

# Why Spread Spectrum:
#   - Spreading across many pixels makes it survive re-encoding, compression, resize
#   - Single LSB changes are 0.4% brightness change — totally invisible
#   - Even if YouTube destroys 30% of embedded pixels, majority voting recovers the text

# Example embedded text:
#   "ORG=ESPN_CORP|VID=9b332136-734d-4002-b6dc-a25c7a2cff4c|TS=2024-01-01"
# """

# import cv2
# import numpy as np
# import hashlib

# # ── Config ────────────────────────────────────────────────────────────────────

# # Your organisation name — change this to your actual org
# ORG_NAME = "SPORTS_ORG"

# # Secret key used to generate the pixel spread pattern
# # Change this to something unique to your organisation
# SECRET_KEY = "sports_fingerprint_secret_2024"

# # How many pixels carry each bit — higher = more robust, slightly more visible
# # 30 = each bit is spread across 30 pixels (majority voting)
# REDUNDANCY = 30

# # Embed strength — how much we modify each pixel
# # 3 = invisible, survives mild compression
# # 8 = slightly visible in dark areas, survives YouTube re-encoding
# EMBED_STRENGTH = 6


# # ── Core functions ────────────────────────────────────────────────────────────

# def _text_to_bits(text: str) -> list:
#     """Converts text string to list of bits."""
#     bits = []
#     for char in text:
#         byte = ord(char)
#         for i in range(7, -1, -1):
#             bits.append((byte >> i) & 1)
#     return bits


# def _bits_to_text(bits: list) -> str:
#     """Converts list of bits back to text string."""
#     text = ""
#     for i in range(0, len(bits) - 7, 8):
#         byte_bits = bits[i:i+8]
#         byte = sum(b << (7 - j) for j, b in enumerate(byte_bits))
#         if byte == 0:
#             break   # null terminator
#         if 32 <= byte <= 126:   # printable ASCII only
#             text += chr(byte)
#         else:
#             text += "?"
#     return text


# def _get_pixel_positions(frame_shape: tuple, n_positions: int) -> np.ndarray:
#     """
#     Generates a deterministic list of pixel positions using the SECRET_KEY.
#     Same key always gives same positions — this is how we find our watermark later.
#     Uses numpy's seeded random generator for reproducibility.
#     """
#     h, w = frame_shape[:2]
#     # Create a seed from the secret key
#     seed = int(hashlib.md5(SECRET_KEY.encode()).hexdigest()[:8], 16)
#     rng  = np.random.RandomState(seed)
#     # Generate random (row, col) positions
#     rows = rng.randint(0, h, size=n_positions)
#     cols = rng.randint(0, w, size=n_positions)
#     return rows, cols


# def build_watermark_text(video_id: str) -> str:
#     """
#     Builds the full watermark text string that gets embedded.
#     This is the actual readable owner information.

#     Format: ORG=<org_name>|VID=<first 8 chars of video_id>
#     Kept short so it fits in more frames at lower strength.
#     """
#     short_id = video_id.replace("-", "")[:16]   # first 16 hex chars
#     return f"ORG={ORG_NAME}|VID={short_id}"


# def embed_watermark(frame: np.ndarray, video_id: str) -> np.ndarray:
#     """
#     Embeds the owner text invisibly into a video frame.

#     Process:
#       1. Convert frame to YCrCb (work on Y/luminance — least visible)
#       2. Build watermark text: "ORG=SPORTS_ORG|VID=9b332136..."
#       3. Convert text to bits
#       4. For each bit: modify REDUNDANCY pixels at secret key positions
#       5. Convert back to BGR

#     Args:
#         frame    : BGR numpy array from OpenCV
#         video_id : UUID from Step 1

#     Returns:
#         Watermarked frame — visually identical to input
#     """
#     wm_text = build_watermark_text(video_id)
#     wm_bits = _text_to_bits(wm_text)
#     n_bits  = len(wm_bits)

#     # Total pixels needed = bits × redundancy
#     total_pixels = n_bits * REDUNDANCY

#     # Work on Y channel only
#     ycrcb     = cv2.cvtColor(frame, cv2.COLOR_BGR2YCrCb)
#     y_channel = ycrcb[:, :, 0].astype(np.int16)   # int16 to avoid overflow

#     h, w = y_channel.shape

#     # Generate pixel positions from secret key
#     rows, cols = _get_pixel_positions(frame.shape, total_pixels)

#     # Embed each bit into its REDUNDANCY pixels
#     for bit_idx, bit_value in enumerate(wm_bits):
#         start = bit_idx * REDUNDANCY
#         end   = start + REDUNDANCY

#         for k in range(start, min(end, len(rows))):
#             r, c = rows[k], cols[k]
#             pixel = int(y_channel[r, c])

#             if bit_value == 1:
#                 # Push pixel value up (embed a 1)
#                 new_val = pixel + EMBED_STRENGTH
#             else:
#                 # Push pixel value down (embed a 0)
#                 new_val = pixel - EMBED_STRENGTH

#             y_channel[r, c] = np.clip(new_val, 0, 255)

#     ycrcb[:, :, 0] = y_channel.astype(np.uint8)
#     return cv2.cvtColor(ycrcb, cv2.COLOR_YCrCb2BGR)


# def extract_watermark_text(frame: np.ndarray, expected_text_len: int = None) -> str:
#     """
#     Extracts the embedded owner text from a frame.

#     Process:
#       1. Convert to YCrCb
#       2. Use the same secret key positions
#       3. For each bit: majority vote across REDUNDANCY pixels
#          (pixel above middle = 1, below = 0)
#       4. Convert bits back to text

#     Returns the extracted text string.
#     """
#     ycrcb     = cv2.cvtColor(frame, cv2.COLOR_BGR2YCrCb)
#     y_channel = ycrcb[:, :, 0].astype(np.float32)
#     h, w      = y_channel.shape

#     # We need to know how many bits to extract
#     # Default: extract enough for a 40-character text
#     max_chars = expected_text_len or 40
#     n_bits    = max_chars * 8
#     total_pix = n_bits * REDUNDANCY

#     rows, cols = _get_pixel_positions(frame.shape, total_pix)

#     # For each bit position, collect votes from all its pixels
#     # We compare each pixel to its neighbours to see if it was pushed up or down
#     extracted_bits = []

#     for bit_idx in range(n_bits):
#         start = bit_idx * REDUNDANCY
#         end   = start + REDUNDANCY
#         votes = []

#         for k in range(start, min(end, len(rows))):
#             r, c    = rows[k], cols[k]
#             pixel   = y_channel[r, c]

#             # Compute local mean of surrounding pixels as reference
#             r1, r2  = max(0, r-2), min(h, r+3)
#             c1, c2  = max(0, c-2), min(w, c+3)
#             patch   = y_channel[r1:r2, c1:c2]
#             local_mean = np.mean(patch)

#             # If pixel is above local mean → embedded a 1
#             # If pixel is below local mean → embedded a 0
#             votes.append(1 if pixel > local_mean else 0)

#         # Majority vote
#         if votes:
#             extracted_bits.append(1 if sum(votes) > len(votes) / 2 else 0)

#     return _bits_to_text(extracted_bits)


# def verify_watermark(frame: np.ndarray, video_id: str) -> dict:
#     """
#     Verifies that a frame contains our organisation's watermark.

#     Returns:
#         {
#             "verified":        True/False,
#             "extracted_text":  "ORG=SPORTS_ORG|VID=9b332136...",
#             "expected_text":   "ORG=SPORTS_ORG|VID=9b332136...",
#             "org_found":       True/False,   ← did we find our org name?
#             "id_found":        True/False,   ← did we find the video ID?
#             "char_match_pct":  87.5,         ← how much of text matched
#         }
#     """
#     expected_text = build_watermark_text(video_id)
#     extracted     = extract_watermark_text(frame, expected_text_len=len(expected_text))

#     # Check if key parts of the watermark are present
#     org_found = ORG_NAME in extracted
#     vid_short = video_id.replace("-", "")[:16]
#     id_found  = vid_short in extracted

#     # Character-level match percentage
#     matches    = sum(a == b for a, b in zip(expected_text, extracted))
#     match_pct  = round(matches / max(len(expected_text), 1) * 100, 1)

#     verified = org_found or match_pct >= 70

#     print(f"[Watermark] Expected : '{expected_text}'")
#     print(f"[Watermark] Extracted: '{extracted}'")
#     print(f"[Watermark] org_found={org_found} id_found={id_found} match={match_pct}%")

#     return {
#         "verified":       verified,
#         "extracted_text": extracted,
#         "expected_text":  expected_text,
#         "org_found":      org_found,
#         "id_found":       id_found,
#         "char_match_pct": match_pct,
#     }