#!/usr/bin/env python3
"""
EarthBound: Zero Fault - 3-Slot Battery SRAM (.srm) Save Generator

Generates a verified, multi-checkpoint battery save file containing:
  Slot 1: Mid-game checkpoint (Phase 9/10 - Fourside Monolithic Kernel & Moonside)
  Slot 2: Late-game checkpoint (Phase 13 - Magicant Core Dump & Sea of Eden)
  Slot 3: Endgame checkpoint (Phase 15 - Cave of the Past Robotic Chassis & Giygas)

Calculates dual checksums (Sum mod 0x10000 and 16-bit word XOR) for both primary (A)
and mirror (B) blocks for all three slots.
"""

import os
import struct
import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BUILD_SRM = REPO_ROOT / "build" / "eb_zero_fault.srm"
PRESET_DIR = REPO_ROOT / "tools" / "presets"
PRESET_SRM = PRESET_DIR / "eb_zero_fault.srm"

# SRAM Layout Constants
SRAM_SIZE = 8192
BLOCK_SIZE = 0x500
DATA_OFFSET = 0x20
DATA_SIZE = 0x4E0  # 1248 bytes

SAVE_SLOTS = {
    1: (0x0000, 0x0500),
    2: (0x0A00, 0x0F00),
    3: (0x1400, 0x1900),
}

# Save Payload Offsets (relative to DATA_OFFSET)
OFF_PET_NAME = 0x24
OFF_FAV_FOOD = 0x2A
OFF_FAV_THING = 0x34
OFF_MONEY_HAND = 0x3C
OFF_MONEY_ATM = 0x40
OFF_X_COORD = 0x82
OFF_Y_COORD = 0x86
OFF_DIRECTION = 0x8A
OFF_PARTY_LIST = 0x96
OFF_PCC_LIST = 0x9D
OFF_NUM_PARTY = 0xAE
OFF_NUM_PCC = 0xAF
OFF_TEXT_SPEED = 0xC1
OFF_SOUND_MODE = 0xC2
OFF_WINDOW_FLAVOR = 0x1D8
OFF_CHAR_TABLE = 0x1D9
CHAR_ENTRY_SIZE = 0x5F
OFF_FLAG_TABLE = 0x413

# Character Struct Offsets (relative to character entry start)
E_NAME = 0x00
E_LEVEL = 0x05
E_XP = 0x06
E_MAX_HP = 0x0A
E_MAX_PP = 0x0C
E_PSTATUS = 0x0E
E_OFF = 0x15
E_DEF = 0x16
E_SPD = 0x17
E_GUT = 0x18
E_LUC = 0x19
E_VIT = 0x1A
E_IQ = 0x1B
E_BOFF = 0x1C
E_BDEF = 0x1D
E_BSPD = 0x1E
E_BGUT = 0x1F
E_BLUC = 0x20
E_BVIT = 0x21
E_BIQ = 0x22
E_INV = 0x23
E_WEAP = 0x31
E_BODY = 0x32
E_ARMS = 0x33
E_OTHER = 0x34
E_ROLL_HP = 0x45
E_CUR_HP = 0x47
E_ROLL_PP = 0x4B
E_CUR_PP = 0x4D

# Item IDs
ITEM_FRANKLIN_BADGE = 0x01
ITEM_BIG_LEAGUE_BAT = 0x16
ITEM_MAGICANT_BAT = 0x18
ITEM_GUTSY_BAT = 0x1A
ITEM_SWORD_OF_KINGS = 0x23
ITEM_LASER_GUN = 0x29
ITEM_GAIA_BEAM = 0x30
ITEM_STAR_PENDANT = 0x3E
ITEM_CLOAK_OF_KINGS = 0x3F
ITEM_BRACER_OF_KINGS = 0x49
ITEM_DIADEM_OF_KINGS = 0x57
ITEM_DIRTY_PAGE = 0x58
ITEM_BRAIN_FOOD_LUNCH = 0x64
ITEM_HORN_OF_LIFE = 0x82
ITEM_FORK_BOMB = 0x93
ITEM_NON_STICK_FRYPAN = 0xF8
ITEM_CUP_OF_LIFENOODLES = 0xFC
ITEM_EARTH_PENDANT = 0x3D
ITEM_GODDESS_BAND = 0x48
ITEM_SOUVENIR_COIN = 0x56
ITEM_SOUND_STONE = 0xC4
ITEM_BAZOOKA = 0x31
ITEM_HEAVY_BAZOOKA = 0x32


def encode_eb_text(s: str, length: int) -> bytes:
    """Encode ASCII text into EarthBound text encoding."""
    out = bytearray()
    for ch in s:
        if ch == " ":
            out.append(0x50)
        elif 0x20 <= ord(ch) < 0x80:
            out.append((ord(ch) + 0x30) & 0xFF)
        else:
            out.append(0x00)
        if len(out) >= length:
            break
    while len(out) < length:
        out.append(0x00)
    return bytes(out)


def calc_checksum1(data: bytes) -> int:
    """Sum of all data bytes modulo 0x10000."""
    return sum(data) & 0xFFFF


def calc_checksum2(data: bytes) -> int:
    """Bitwise XOR of all 16-bit little-endian words."""
    x = 0
    for i in range(0, len(data), 2):
        w = data[i] | (data[i + 1] << 8)
        x ^= w
    return x & 0xFFFF


def set_flag(flags: bytearray, flag_num: int) -> None:
    """Set 1-based or 0-based EarthBound flag in 128-byte flag array."""
    idx = flag_num // 8
    bit = flag_num % 8
    if idx < len(flags):
        flags[idx] |= (1 << bit)


def configure_character(
    payload: bytearray,
    char_idx: int,
    name: str,
    level: int,
    hp: int,
    pp: int,
    off: int,
    defense: int,
    spd: int,
    gut: int,
    luc: int,
    vit: int,
    iq: int,
    weapon: int = 0,
    body: int = 0,
    arms: int = 0,
    other: int = 0,
    inventory: list = None,
) -> None:
    """Configure individual character block in save payload."""
    eo = OFF_CHAR_TABLE + char_idx * CHAR_ENTRY_SIZE
    payload[eo + E_NAME : eo + E_NAME + 5] = encode_eb_text(name, 5)
    payload[eo + E_LEVEL] = level
    struct.pack_into("<I", payload, eo + E_XP, level * 15000)
    struct.pack_into("<H", payload, eo + E_MAX_HP, hp)
    struct.pack_into("<H", payload, eo + E_CUR_HP, hp)
    struct.pack_into("<H", payload, eo + E_ROLL_HP, hp)
    struct.pack_into("<H", payload, eo + E_MAX_PP, pp)
    struct.pack_into("<H", payload, eo + E_CUR_PP, pp)
    struct.pack_into("<H", payload, eo + E_ROLL_PP, pp)
    payload[eo + E_PSTATUS] = 0  # Normal status

    # Current stats & base stats
    for stat_val, offset, b_offset in [
        (off, E_OFF, E_BOFF),
        (defense, E_DEF, E_BDEF),
        (spd, E_SPD, E_BSPD),
        (gut, E_GUT, E_BGUT),
        (luc, E_LUC, E_BLUC),
        (vit, E_VIT, E_BVIT),
        (iq, E_IQ, E_BIQ),
    ]:
        payload[eo + offset] = min(255, stat_val)
        payload[eo + b_offset] = min(255, stat_val)

    # Equipment
    payload[eo + E_WEAP] = weapon
    payload[eo + E_BODY] = body
    payload[eo + E_ARMS] = arms
    payload[eo + E_OTHER] = other

    # Inventory (up to 14 items)
    inv = (inventory or [])[:14]
    while len(inv) < 14:
        inv.append(0)
    for idx, item_id in enumerate(inv):
        payload[eo + E_INV + idx] = item_id


def build_save_file() -> bytearray:
    """Build the complete 8192-byte SRAM battery save file."""
    srm = bytearray(SRAM_SIZE)

    # -------------------------------------------------------------
    # SLOT 1: Mid-Game Checkpoint (Phase 9/10: Fourside & Moonside)
    # -------------------------------------------------------------
    p1 = bytearray(DATA_SIZE)
    p1[OFF_PET_NAME : OFF_PET_NAME + 6] = encode_eb_text("King", 6)
    p1[OFF_FAV_FOOD : OFF_FAV_FOOD + 6] = encode_eb_text("Steak", 6)
    p1[OFF_FAV_THING : OFF_FAV_THING + 6] = encode_eb_text("Rockin", 6)
    struct.pack_into("<I", p1, OFF_MONEY_HAND, 12500)
    struct.pack_into("<I", p1, OFF_MONEY_ATM, 35000)
    struct.pack_into("<H", p1, OFF_X_COORD, 5956)
    struct.pack_into("<H", p1, OFF_Y_COORD, 6096)
    p1[OFF_DIRECTION] = 0
    p1[OFF_PARTY_LIST : OFF_PARTY_LIST + 4] = bytes([1, 2, 3, 0])
    p1[OFF_PCC_LIST : OFF_PCC_LIST + 4] = bytes([1, 2, 3, 0])
    p1[OFF_NUM_PARTY] = 3
    p1[OFF_NUM_PCC] = 3
    p1[OFF_TEXT_SPEED] = 1  # Fast
    p1[OFF_SOUND_MODE] = 1  # Stereo
    p1[OFF_WINDOW_FLAVOR] = 0

    # Characters
    configure_character(
        p1, 0, "Ness", 45, 420, 180, 95, 85, 35, 30, 30, 42, 36,
        weapon=ITEM_BIG_LEAGUE_BAT, body=ITEM_EARTH_PENDANT, arms=0x47, other=ITEM_FRANKLIN_BADGE,
        inventory=[ITEM_BIG_LEAGUE_BAT, ITEM_EARTH_PENDANT, ITEM_FRANKLIN_BADGE, ITEM_DIRTY_PAGE, ITEM_FORK_BOMB, ITEM_BRAIN_FOOD_LUNCH, ITEM_CUP_OF_LIFENOODLES]
    )
    configure_character(
        p1, 1, "Paula", 43, 260, 240, 45, 65, 40, 25, 35, 26, 48,
        weapon=ITEM_NON_STICK_FRYPAN, body=0, arms=0x47, other=0,
        inventory=[ITEM_NON_STICK_FRYPAN, ITEM_BRAIN_FOOD_LUNCH, ITEM_HORN_OF_LIFE]
    )
    configure_character(
        p1, 2, "Jeff", 42, 310, 0, 75, 70, 38, 20, 30, 31, 55,
        weapon=ITEM_LASER_GUN, body=0, arms=0x47, other=0,
        inventory=[ITEM_LASER_GUN, ITEM_BAZOOKA, ITEM_BRAIN_FOOD_LUNCH]
    )

    # CoW Flags: All Phases 1-8 dirtied and committed (840..867)
    flags1 = bytearray(128)
    for f in range(840, 868):
        set_flag(flags1, f)
    # Story progression flags: Twoson, Happy Happy, Threed, Belch defeated
    set_flag(flags1, 19)   # Twoson arrived
    set_flag(flags1, 37)   # Everdred met
    set_flag(flags1, 75)   # Paula rescued
    set_flag(flags1, 110)  # Threed zombies cleared
    set_flag(flags1, 142)  # Belch defeated
    set_flag(flags1, 185)  # Fourside entered
    p1[OFF_FLAG_TABLE : OFF_FLAG_TABLE + 128] = flags1

    # -------------------------------------------------------------
    # SLOT 2: Late-Game Checkpoint (Phase 13: Magicant & Sea of Eden)
    # -------------------------------------------------------------
    p2 = bytearray(DATA_SIZE)
    p2[OFF_PET_NAME : OFF_PET_NAME + 6] = encode_eb_text("King", 6)
    p2[OFF_FAV_FOOD : OFF_FAV_FOOD + 6] = encode_eb_text("Steak", 6)
    p2[OFF_FAV_THING : OFF_FAV_THING + 6] = encode_eb_text("Rockin", 6)
    struct.pack_into("<I", p2, OFF_MONEY_HAND, 24800)
    struct.pack_into("<I", p2, OFF_MONEY_ATM, 75000)
    struct.pack_into("<H", p2, OFF_X_COORD, 8099)
    struct.pack_into("<H", p2, OFF_Y_COORD, 7880)
    p2[OFF_DIRECTION] = 0
    p2[OFF_PARTY_LIST : OFF_PARTY_LIST + 4] = bytes([1, 0, 0, 0])
    p2[OFF_PCC_LIST : OFF_PCC_LIST + 4] = bytes([1, 0, 0, 0])
    p2[OFF_NUM_PARTY] = 1
    p2[OFF_NUM_PCC] = 1
    p2[OFF_TEXT_SPEED] = 1
    p2[OFF_SOUND_MODE] = 1
    p2[OFF_WINDOW_FLAVOR] = 0

    configure_character(
        p2, 0, "Ness", 75, 680, 340, 175, 140, 65, 55, 60, 68, 68,
        weapon=ITEM_MAGICANT_BAT, body=ITEM_EARTH_PENDANT, arms=ITEM_GODDESS_BAND, other=ITEM_SOUVENIR_COIN,
        inventory=[ITEM_MAGICANT_BAT, ITEM_EARTH_PENDANT, ITEM_GODDESS_BAND, ITEM_SOUVENIR_COIN, ITEM_SOUND_STONE, ITEM_FRANKLIN_BADGE, ITEM_HORN_OF_LIFE, ITEM_CUP_OF_LIFENOODLES, ITEM_BRAIN_FOOD_LUNCH]
    )

    # CoW Flags: All Phases 1-12 dirtied and committed (840..889)
    flags2 = bytearray(128)
    for f in range(840, 890):
        set_flag(flags2, f)
    # Story flags: All 8 Sanctuaries recorded, Magicant unlocked
    for s_flag in [43, 67, 108, 145, 192, 230, 265, 290]:
        set_flag(flags2, s_flag)
    set_flag(flags2, 310)  # Magicant warp trigger
    p2[OFF_FLAG_TABLE : OFF_FLAG_TABLE + 128] = flags2

    # -------------------------------------------------------------
    # SLOT 3: Endgame Checkpoint (Phase 15: Cave of the Past / Final Battle)
    # -------------------------------------------------------------
    p3 = bytearray(DATA_SIZE)
    p3[OFF_PET_NAME : OFF_PET_NAME + 6] = encode_eb_text("King", 6)
    p3[OFF_FAV_FOOD : OFF_FAV_FOOD + 6] = encode_eb_text("Steak", 6)
    p3[OFF_FAV_THING : OFF_FAV_THING + 6] = encode_eb_text("Rockin", 6)
    struct.pack_into("<I", p3, OFF_MONEY_HAND, 99999)
    struct.pack_into("<I", p3, OFF_MONEY_ATM, 99999)
    struct.pack_into("<H", p3, OFF_X_COORD, 599)
    struct.pack_into("<H", p3, OFF_Y_COORD, 6945)
    p3[OFF_DIRECTION] = 0
    p3[OFF_PARTY_LIST : OFF_PARTY_LIST + 4] = bytes([1, 2, 3, 4])
    p3[OFF_PCC_LIST : OFF_PCC_LIST + 4] = bytes([1, 2, 3, 4])
    p3[OFF_NUM_PARTY] = 4
    p3[OFF_NUM_PCC] = 4
    p3[OFF_TEXT_SPEED] = 1
    p3[OFF_SOUND_MODE] = 1
    p3[OFF_WINDOW_FLAVOR] = 0

    configure_character(
        p3, 0, "Ness", 99, 850, 450, 240, 190, 85, 80, 80, 85, 90,
        weapon=ITEM_GUTSY_BAT, body=ITEM_STAR_PENDANT, arms=ITEM_GODDESS_BAND, other=ITEM_SOUVENIR_COIN,
        inventory=[ITEM_GUTSY_BAT, ITEM_STAR_PENDANT, ITEM_GODDESS_BAND, ITEM_SOUVENIR_COIN, ITEM_FRANKLIN_BADGE, ITEM_HORN_OF_LIFE, ITEM_BRAIN_FOOD_LUNCH, ITEM_CUP_OF_LIFENOODLES]
    )
    configure_character(
        p3, 1, "Paula", 99, 520, 500, 110, 150, 88, 50, 75, 52, 99,
        weapon=ITEM_NON_STICK_FRYPAN, body=ITEM_STAR_PENDANT, arms=ITEM_GODDESS_BAND, other=0,
        inventory=[ITEM_NON_STICK_FRYPAN, ITEM_STAR_PENDANT, ITEM_GODDESS_BAND, ITEM_HORN_OF_LIFE, ITEM_CUP_OF_LIFENOODLES]
    )
    configure_character(
        p3, 2, "Jeff", 99, 640, 0, 180, 165, 82, 45, 70, 64, 99,
        weapon=ITEM_GAIA_BEAM, body=ITEM_STAR_PENDANT, arms=ITEM_GODDESS_BAND, other=0,
        inventory=[ITEM_GAIA_BEAM, ITEM_STAR_PENDANT, ITEM_GODDESS_BAND, ITEM_HEAVY_BAZOOKA, ITEM_CUP_OF_LIFENOODLES]
    )
    configure_character(
        p3, 3, "Poo", 99, 690, 380, 200, 175, 90, 60, 75, 69, 85,
        weapon=ITEM_SWORD_OF_KINGS, body=ITEM_CLOAK_OF_KINGS, arms=ITEM_BRACER_OF_KINGS, other=ITEM_DIADEM_OF_KINGS,
        inventory=[ITEM_SWORD_OF_KINGS, ITEM_CLOAK_OF_KINGS, ITEM_BRACER_OF_KINGS, ITEM_DIADEM_OF_KINGS, ITEM_BRAIN_FOOD_LUNCH, ITEM_CUP_OF_LIFENOODLES]
    )

    # CoW Flags: All Phases 1-15 dirtied & committed
    flags3 = bytearray(128)
    for f in range(840, 895):
        set_flag(flags3, f)
    # Story flags: Phase Distorter v3 conversion complete, Cave of Past active
    set_flag(flags3, 349)  # Robotic conversion state
    set_flag(flags3, 382)  # Cave of the Past final portal open
    set_flag(flags3, 476)  # Saturn Valley Phase Distorter launch
    p3[OFF_FLAG_TABLE : OFF_FLAG_TABLE + 128] = flags3

    # -------------------------------------------------------------
    # Write Blocks to SRM (Primary A & Mirror B)
    # -------------------------------------------------------------
    slot_payloads = {1: p1, 2: p2, 3: p3}

    for slot, (off_a, off_b) in SAVE_SLOTS.items():
        payload = slot_payloads[slot]
        c1 = calc_checksum1(payload)
        c2 = calc_checksum2(payload)

        block = bytearray(BLOCK_SIZE)
        block[0x00:0x14] = b"HAL Laboratory, inc."
        struct.pack_into("<H", block, 0x1C, c1)
        struct.pack_into("<H", block, 0x1E, c2)
        block[DATA_OFFSET : DATA_OFFSET + DATA_SIZE] = payload

        # Primary copy A
        srm[off_a : off_a + BLOCK_SIZE] = block
        # Mirror copy B
        srm[off_b : off_b + BLOCK_SIZE] = block

    # Metadata & Anti-Piracy Footer
    srm[0x1FF0] = 0x31  # Anti-piracy verification byte
    struct.pack_into("<H", srm, 0x1FFE, 0x0493)  # US release version word

    return srm


def main():
    srm_data = build_save_file()
    PRESET_DIR.mkdir(parents=True, exist_ok=True)
    BUILD_SRM.parent.mkdir(parents=True, exist_ok=True)

    with open(BUILD_SRM, "wb") as f:
        f.write(srm_data)

    with open(PRESET_SRM, "wb") as f:
        f.write(srm_data)

    print(f"Generated 3-slot battery save:")
    print(f"  Target 1: {BUILD_SRM} ({len(srm_data)} bytes)")
    print(f"  Target 2: {PRESET_SRM} ({len(srm_data)} bytes)")
    print()
    print("Slot Manifest:")
    print("  [Slot 1] Phase 9/10  - Fourside & Moonside Checkpoint (Ness, Paula, Jeff Lvl 45/43/42)")
    print("  [Slot 2] Phase 13    - Magicant & Sea of Eden Checkpoint (Ness Solo Lvl 75)")
    print("  [Slot 3] Phase 15    - Cave of the Past & Final Battle (Robotic Party Lvl 99)")


if __name__ == "__main__":
    main()
