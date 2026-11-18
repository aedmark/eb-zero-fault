#!/usr/bin/env python3
"""
Verify EarthBound: Zero Fault compiled ROM binary integrity and injected hooks.
"""

import os
import sys
from pathlib import Path

ROM_PATH = "build/eb_zero_fault.sfc"
SUMMARY_PATH = "src/ccscript/summary.txt"
EXPECTED_SIZE = 4_194_304  # 32 Mbits (4 MB)

HOOKS = [
    # Dash hooks (0xC02F30, 0xC031B8, 0xC07960, 0xC0B8F1)
    (0x002F30, b"\x22", "Dash Hook 1 (Movement Vector)"),
    (0x0031B8, b"\x22", "Dash Hook 2 (Diagonal Vector)"),
    (0x007960, b"\x22", "Dash Hook 3 (Movement Normalization)"),
    (0x00B8F1, b"\x29\x00\x20", "Dash Hook 4 (Overworld B-Button Status Bypass)"),
    # Fast text hooks
    (0x01FEC9, b"\x22", "Fast Text Hook 1 (Delay Calculation)"),
    (0x010D4B, b"\x22", "Fast Text Hook 2 (Delay Check Call 1)"),
    (0x044055, b"\x22", "Fast Text Hook 3 (Delay Check Call 2)"),
    (0x0444E3, b"\x22", "Fast Text Hook 4 (Delay Check Call 3)"),
    (0x02038B, b"\x5C", "Fast Text Battle HDMA Queue Guard"),
    # Shop stat comparison hooks
    (0x05E277, b"\x0A", "Shop Equipment Stat Display Part 1"),
    (0x05E2F7, b"\x0A", "Shop Equipment Stat Display Part 2"),
    # Phase 17: Volatile Memory Pressure & Flush Loop Hooks
    (0x021669, b"\x22", "CoW Flag Mutation Pressure Hook ($C21669)"),
    (0x0185DA, b"\x22", "Payphone Save Pressure Relief Hook ($C185DA)"),
    # Phase 4: CoW Narrative & MMU Hooks
    (0x066D3E, b"\x0A", "CoW Mom Initial Awakening Hook (0xC66D3E)"),
    (0x074F56, b"\x0A", "CoW Mom Awakening Script Hook (0xC74F56)"),
    (0x075C33, b"\x0A", "CoW Pokey Front Door Burst Hook (0xC75C33)"),
    (0x072AF8, b"\x0A", "CoW Mayor Pirkle Refcount Hook (0xC72AF8)"),
    (0x066002, b"\x0A", "CoW Twoson MMU Roadblock Hook (0xC66002)"),
    (0x07BEB9, b"\x0A", "CoW Giant Step Cache Commit Hook (0xC7BEB9)"),
    # Phase 7: Twoson & Immutable Cult Hooks
    (0x07699E, b"\x0A", "CoW Captain Strong Desk Hook (0xC7699E)"),
    (0x05F859, b"\x0A", "CoW Captain Strong Challenge Hook (0xC5F859)"),
    (0x081676, b"\x0A", "CoW Apple Kid JIT Hook (0xC81676)"),
    (0x095C0E, b"\x0A", "CoW Everdred Raw Heap Hook (0xC95C0E)"),
    (0x098024, b"\x0A", "CoW Mr. Carpainter Immutable Cult Hook (0xC98024)"),
    (0x07BF95, b"\x0A", "CoW Lilliput Steps Cache Commit Hook (0xC7BF95)"),
    # Phase 8: Threed, Winters, Belch, and Saturn Valley Hooks
    (0x08E14A, b"\x0A", "CoW Threed Greeter Hook (0xC8E14A)"),
    (0x079D81, b"\x0A", "CoW Threed Hotel Ambush Hook (0xC79D81)"),
    (0x079E55, b"\x0A", "CoW Paula Telepathy Broadcast Hook (0xC79E55)"),
    (0x068D5A, b"\x0A", "CoW Paula Ambient Telepathy Hook (0xC68D5A)"),
    (0x07A300, b"\x0A", "CoW Apple Kid Zombie Paper Hook (0xC7A300)"),
    (0x079F33, b"\x0A", "CoW Jeff Awakening Hook (0xC79F33)"),
    (0x07A04A, b"\x0A", "CoW Tony Linter Hook (0xC7A04A)"),
    (0x06B18D, b"\x0A", "CoW Dr. Andonuts Lab Hook (0xC6B18D)"),
    (0x088875, b"\x0A", "CoW Waterfall Password Hook (0xC88875)"),
    (0x2F6446, b"\x0A", "CoW Master Belch Dialogue Hook (0xEF6446)"),
    (0x2F6569, b"\x0A", "CoW Master Belch Battle Hook (0xEF6569)"),
    (0x07E819, b"\x0A", "CoW Saturn Valley Greeter Hook (0xC7E819)"),
    (0x2F679A, b"\x0A", "CoW Rootkit Sprout Hook (0xEF679A)"),
    (0x07C12A, b"\x0A", "CoW Milky Well Commit Hook (0xC7C12A)"),
    (0x07C17B, b"\x0A", "CoW Milky Well Message Hook (0xC7C17B)"),
    # Phase 9: Dusty Dunes Desert, Fourside, Moonside, and Magnet Hill Hooks
    (0x061228, b"\x0A", "CoW Miner George Defrag Hook (0xC61228)"),
    (0x0613B3, b"\x0A", "CoW Guardian Digger Hook (0xC613B3)"),
    (0x0628A1, b"\x0A", "CoW Teleport Monkey Demo Hook (0xC628A1)"),
    (0x062AE7, b"\x0A", "CoW Teleport Monkey Learn Hook (0xC62AE7)"),
    (0x089580, b"\x0A", "CoW Dept Store Blackout Hook (0xC89580)"),
    (0x082C6B, b"\x0A", "CoW Dept Store Spook Hook (0xC82C6B)"),
    (0x08361C, b"\x0A", "CoW Everdred Cafe Hook (0xC8361C)"),
    (0x06EA34, b"\x0A", "CoW Monotoli 48th Floor Hook (0xC6EA34)"),
    (0x06EB2C, b"\x0A", "CoW Monotoli Confession Hook (0xC6EB2C)"),
    (0x096D10, b"\x0A", "CoW Moonside Greeter Hook (0xC96D10)"),
    (0x096DB2, b"\x0A", "CoW Moonside Inversion Hook (0xC96DB2)"),
    (0x09794B, b"\x0A", "CoW Moonside Mani Mani Hook (0xC9794B)"),
    (0x097990, b"\x0A", "CoW Moonside Mani Mani Destroyed Hook (0xC97990)"),
    (0x07C208, b"\x0A", "CoW Magnet Hill Commit Hook (0xC7C208)"),
    (0x07C258, b"\x0A", "CoW Magnet Hill Message Hook (0xC7C258)"),
    (0x08B8D5, b"\x0A", "CoW Stoic Cake Lady Hook (0xC8B8D5)"),
    (0x08B191, b"\x0A", "CoW Beach Cake Lady Hook (0xC8B191)"),
    (0x0920A2, b"\x0A", "CoW Magic Cake Dream Hook (0xC920A2)"),
    (0x09254A, b"\x0A", "CoW Mu Trial Legs Hook (0xC9254A)"),
    (0x0925E3, b"\x0A", "CoW Mu Trial Arms Hook (0xC925E3)"),
    (0x09268E, b"\x0A", "CoW Mu Trial Ears Hook (0xC9268E)"),
    (0x092723, b"\x0A", "CoW Mu Trial Eyes Hook (0xC92723)"),
    (0x0927EA, b"\x0A", "CoW Mu Trial Mind Hook (0xC927EA)"),
    (0x09C991, b"\x0A", "CoW Dalaam Master Hook (0xC9C991)"),
    (0x09C9E8, b"\x0A", "CoW Dalaam Conclude Hook (0xC9C9E8)"),
    (0x08B52A, b"\x0A", "CoW Sailor Captain Hook (0xC8B52A)"),
    (0x092C70, b"\x0A", "CoW Kraken Voyage Hook (0xC92C70)"),
    (0x087220, b"\x0A", "CoW Sphinx Gate Hook (0xC87220)"),
    (0x087280, b"\x0A", "CoW Sphinx Open Hook (0xC87280)"),
    (0x093181, b"\x0A", "CoW Pyramid Hawk Eye Hook (0xC93181)"),
    (0x0932F6, b"\x0A", "CoW Poo Departure Hook (0xC932F6)"),
    (0x05739F, b"\x0A", "CoW Star Master Hook (0xC5739F)"),
    (0x0573DC, b"\x0A", "CoW Star Master Explain Hook (0xC573DC)"),
    (0x05762C, b"\x0A", "CoW Dungeon Man Key NPC Hook (0xC5762C)"),
    (0x057760, b"\x0A", "CoW Dungeon Man Unlock Hook (0xC57760)"),
    (0x057955, b"\x0A", "CoW Brick Road Dungeon Man Hook (0xC57955)"),
    (0x093381, b"\x0A", "CoW Dungeon Man Stuck Hook (0xC93381)"),
    (0x09344F, b"\x0A", "CoW Dungeon Man Submarine Talk Hook (0xC9344F)"),
    (0x057C2C, b"\x0A", "CoW Jeff Repair Submarine Hook (0xC57C2C)"),
    (0x09E619, b"\x0A", "CoW Master Barf Hook (0xC9E619)"),
    # Phase 12 hooks
    (0x09D77F, b"\x0A", "CoW Tenda Rumor Hook (0xC9D77F)"),
    (0x09D940, b"\x0A", "CoW Tenda Chief Check Hook (0xC9D940)"),
    (0x09D95E, b"\x0A", "CoW Tenda Chief Read Hook (0xC9D95E)"),
    (0x09DC2C, b"\x0A", "CoW Tenda Unshy Hook (0xC9DC2C)"),
    (0x0936E6, b"\x0A", "CoW Strong Tenda Hook (0xC936E6)"),
    (0x0937D9, b"\x0A", "CoW Lumine Wall Hook (0xC937D9)"),
    (0x09E27B, b"\x0A", "CoW Lumine Boss Hook (0xC9E27B)"),
    (0x07C3C2, b"\x0A", "CoW Lumine Melody Hook (0xC7C3C2)"),
    (0x09E2F5, b"\x0A", "CoW Outer Talking Rock Hook (0xC9E2F5)"),
    (0x09DE0E, b"\x0A", "CoW Main Talking Rock Hook (0xC9DE0E)"),
    (0x2F57EB, b"\x0A", "CoW Fire Spring Boss Hook (0xEF57EB)"),
    (0x07C479, b"\x0A", "CoW Fire Spring Melody Hook (0xC7C479)"),
    # Phase 13 hooks
    (0x076F7A, b"\x0A", "CoW Magicant Flying Man 1 Hook (0xC76F7A)"),
    (0x076F96, b"\x0A", "CoW Magicant Flying Man 2 Hook (0xC76F96)"),
    (0x076FB2, b"\x0A", "CoW Magicant Flying Man Dialogue Hook (0xC76FB2)"),
    (0x0772FF, b"\x0A", "CoW Magicant Tracy Hook (0xC772FF)"),
    (0x0773F4, b"\x0A", "CoW Magicant Greeter Hook (0xC773F4)"),
    (0x07743D, b"\x0A", "CoW Magicant Young Ness Hook (0xC7743D)"),
    (0x0776EE, b"\x0A", "CoW Magicant Tombstone 1 Hook (0xC776EE)"),
    (0x077713, b"\x0A", "CoW Magicant Tombstone 2 Hook (0xC77713)"),
    (0x07779E, b"\x0A", "CoW Magicant Buzz Buzz Tombstone Hook (0xC7779E)"),
    (0x0777F2, b"\x0A", "CoW Sea of Eden Greeter Hook (0xC777F2)"),
    (0x07786E, b"\x0A", "CoW Sea of Eden Guide Hook (0xC7786E)"),
    (0x07794C, b"\x0A", "CoW Ness Nightmare Hook (0xC7794C)"),
    (0x09B4C9, b"\x0A", "CoW Magicant Resync Saturn Valley Hook (0xC9B4C9)"),
    # Phase 14 hooks
    (0x09B900, b"\x0A", "CoW Phase Distorter 1 Test Hook (0xC9B900)"),
    (0x09BCA1, b"\x0A", "CoW Phase Distorter 3 Conversion Hook (0xC9BCA1)"),
    (0x07EF3B, b"\x0A", "CoW Apple Kid Saturn Valley Hook (0xC7EF3B)"),
    (0x07F165, b"\x0A", "CoW Dr. Andonuts Saturn Valley Hook (0xC7F165)"),
    (0x07F29E, b"\x0A", "CoW Dr. Andonuts Zexonyte Hook (0xC7F29E)"),
    (0x07F710, b"\x0A", "CoW Mr. Saturn Tea Ceremony Hook (0xC7F710)"),
    (0x086279, b"\x0A", "CoW Onett Meteorite Night Hook (0xC86279)"),
    (0x07533C, b"\x0A", "CoW Mom Onett Night Hook (0xC7533C)"),
    (0x066B33, b"\x0A", "CoW Tracy Onett Night Hook (0xC66B33)"),
    # Phase 15 hooks
    (0x2F58C7, b"\x0A", "CoW Broken Phase Distorter Hook (0xEF58C7)"),
    (0x09C262, b"\x0A", "CoW Cave of Past Saturn 1 Hook (0xC9C262)"),
    (0x09C27E, b"\x0A", "CoW Cave of Past Saturn 2 Hook (0xC9C27E)"),
    (0x08FB1B, b"\x0A", "CoW Pokey Battle Entry Hook (0xC8FB1B)"),
    (0x08FC2E, b"\x0A", "CoW Pokey Unleash Giygas Hook (0xC8FC2E)"),
    (0x08FD11, b"\x0A", "CoW Pokey Taunt Hook (0xC8FD11)"),
    (0x08FF31, b"\x0A", "CoW Pokey Flee Hook (0xC8FF31)"),
    (0x09EE2F, b"\x0A", "CoW Giygas Voice Random Hook (0xC9EE2F)"),
    (0x09F0B8, b"\x0A", "CoW Prayer 1 Intro Hook (0xC9F0B8)"),
    (0x09F134, b"\x0A", "CoW Prayer 1 Hook (0xC9F134)"),
    (0x09F442, b"\x0A", "CoW Prayer Mom Hook (0xC9F442)"),
    (0x09F4A2, b"\x0A", "CoW Prayer Runaway Five Hook (0xC9F4A2)"),
    (0x09F70C, b"\x0A", "CoW Prayer User Hook (0xC9F70C)"),
    (0x09F86A, b"\x0A", "CoW Giygas Unstable Hook (0xC9F86A)"),
    (0x07547D, b"\x0A", "CoW Mom Epilogue Hook (0xC7547D)"),
    (0x07625E, b"\x0A", "CoW Tracy Epilogue Hook (0xC7625E)"),
    (0x09C85D, b"\x0A", "CoW Picky Epilogue Letter Hook (0xC9C85D)"),
]

# Active NPC Configuration Table bindings verified dynamically against compiled symbols in summary.txt
NPC_BINDINGS = [
    (15, "cow_mom_initial_awakening", "NPC Table Entry 15 (Mom Initial Awakening Pointer)"),
    (14, "cow_mom_awakening", "NPC Table Entry 14 (Mom Awakening Door Knock Pointer)"),
    (17, "cow_pokey_burst", "NPC Table Entry 17 (Pokey Front Door Burst Pointer)"),
    (86, "cow_mayor_pirkle", "NPC Table Entry 86 (Mayor Pirkle Refcount Pointer)"),
    (144, "cow_police_roadblock", "NPC Table Entry 144 (Police Roadblock MMU Pointer)"),
    (67, "cow_captain_strong_desk", "NPC Table Entry 67 (Captain Strong Desk Pointer)"),
    (221, "cow_apple_kid", "NPC Table Entry 221 (Apple Kid JIT Pointer)"),
    (254, "cow_everdred", "NPC Table Entry 254 (Everdred Raw Heap Pointer)"),
    (376, "cow_carpainter", "NPC Table Entry 376 (Mr. Carpainter Immutable Cult Pointer)"),
    (515, "cow_threed_greeter", "NPC Table Entry 515 (Threed Greeter Defunct PID Pointer)"),
    (615, "cow_dr_andonuts", "NPC Table Entry 615 (Dr. Andonuts Far-Jump Vector Pointer)"),
    (697, "cow_master_belch", "NPC Table Entry 697 (Master Belch Memory Leak Daemon Pointer)"),
    (705, "cow_trillionage_sprout", "NPC Table Entry 705 (Rootkit Sprout Interceptor Pointer)"),
    (718, "cow_saturn_valley", "NPC Table Entry 718 (Mr. Saturn Alien Primitive Type Pointer)"),
    (830, "cow_miner_george", "NPC Table Entry 830 (Miner George Defrag Pointer)"),
    (831, "cow_guardian_digger_1", "NPC Table Entry 831 (Guardian Digger 1 Pointer)"),
    (773, "cow_teleport_monkey", "NPC Table Entry 773 (Teleport Monkey Teacher Pointer)"),
    (941, "cow_dept_store_spook", "NPC Table Entry 941 (Dept Store Spook Thread Terminus Pointer)"),
    (952, "cow_everdred_cafe", "NPC Table Entry 952 (Everdred Jackie's Cafe Pointer)"),
    (872, "cow_monotoli", "NPC Table Entry 872 (Monotoli 48th Floor Pointer)"),
    (1379, "cow_moonside_greeter", "NPC Table Entry 1379 (Moonside Inversion Greeter Pointer)"),
    (1406, "cow_mani_mani", "NPC Table Entry 1406 (Moonside Mani Mani Rootkit Pointer)"),
    (1002, "cow_stoic_cake_lady", "NPC Table Entry 1002 (Stoic Club Cake Lady Pointer)"),
    (1069, "cow_beach_cake_lady", "NPC Table Entry 1069 (Beach Cart Cake Lady Pointer)"),
    (1089, "cow_master_dalaam", "NPC Table Entry 1089 (Dalaam Master Pointer)"),
    (1065, "cow_sailor_captain", "NPC Table Entry 1065 (Sailor Captain Pointer)"),
    (1149, "cow_dungeonman_key_npc", "NPC Table Entry 1149 (Dungeon Man Key NPC Pointer)"),
    (1152, "cow_dungeonman_submarine_talk", "NPC Table Entry 1152 (Dungeon Man Submarine Talk Pointer)"),
    (1196, "cow_brick_road", "NPC Table Entry 1196 (Brick Road Dungeon Man Pointer)"),
    (1197, "cow_jeff_repair_submarine", "NPC Table Entry 1197 (Submarine Repair Pointer)"),
    (1229, "cow_master_barf", "NPC Table Entry 1229 (Master Barf Deep Darkness Pointer)"),
    # Phase 12 NPC bindings
    (1246, "cow_lumine_boss", "NPC Table Entry 1246 (Electro Specter Telemetry Monitor Pointer)"),
    (1252, "cow_tenda_rumor", "NPC Table Entry 1252 (Tenda Chief Rumor Pointer)"),
    (1258, "cow_tenda_strong", "NPC Table Entry 1258 (Strong Tenda Barrier Pointer)"),
    (1260, "cow_underworld_outer_stone", "NPC Table Entry 1260 (Outer Talking Rock Pointer)"),
    (1261, "cow_tenda_unshy", "NPC Table Entry 1261 (Un-shy Tenda Pointer)"),
    (1276, "cow_firespring_boss", "NPC Table Entry 1276 (Carbon Dog Thermal Runaway Pointer)"),
    (1292, "cow_underworld_main_stone", "NPC Table Entry 1292 (Main Talking Rock Pointer)"),
    # Phase 13 NPC bindings
    (1316, "cow_magicant_flying_man_1", "NPC Table Entry 1316 (Magicant Flying Man 1 Pointer)"),
    (1317, "cow_magicant_flying_man_2", "NPC Table Entry 1317 (Magicant Flying Man 2 Pointer)"),
    (1322, "cow_magicant_greeter", "NPC Table Entry 1322 (Magicant CoW Greeter Pointer)"),
    (1323, "cow_magicant_young_ness", "NPC Table Entry 1323 (Magicant Young Ness Cached PID Pointer)"),
    (1340, "cow_seaofeden_greeter", "NPC Table Entry 1340 (Sea of Eden Greeter Pointer)"),
    (1341, "cow_seaofeden_guide", "NPC Table Entry 1341 (Sea of Eden Architecture Guide Pointer)"),
    (1343, "cow_magicant_tracy", "NPC Table Entry 1343 (Magicant Auxiliary Storage Tracy Pointer)"),
    (1347, "cow_magicant_tombstone_1", "NPC Table Entry 1347 (Worker Thread 1 Core Dump Pointer)"),
    (1348, "cow_magicant_tombstone_2", "NPC Table Entry 1348 (Worker Thread 2 Core Dump Pointer)"),
    (1352, "cow_magicant_tombstone_buzz", "NPC Table Entry 1352 (Buzz Buzz Debug Daemon Tombstone Pointer)"),
    (1358, "cow_ness_nightmare", "NPC Table Entry 1358 (Root Mutex Lock Ness's Nightmare Pointer)"),
    # Phase 14 NPC bindings
    (198, "cow_onett_night_meteorite", "NPC Table Entry 198 (Onett Meteorite Night Pointer)"),
    (727, "cow_phasedistorter_apple_kid", "NPC Table Entry 727 (Apple Kid Saturn Valley Pointer)"),
    (728, "cow_phasedistorter_andonuts", "NPC Table Entry 728 (Dr. Andonuts Saturn Valley Pointer)"),
    (729, "cow_saturn_tea_ceremony", "NPC Table Entry 729 (Mr. Saturn Tea Telemetry Pointer)"),
    # Phase 15 NPC bindings
    (1271, "cow_caveofpast_saturn_1", "NPC Table Entry 1271 (Cave of Past Saturn 1 Pointer)"),
    (1272, "cow_caveofpast_saturn_2", "NPC Table Entry 1272 (Cave of Past Saturn 2 Pointer)"),
    (1273, "cow_caveofpast_wreckage", "NPC Table Entry 1273 (Cave of Past Wreckage Pointer)"),
]

# EarthBound standard text byte mappings (A-Z = 0x71-0x8A, a-z = 0x91-0xAA, space = 0x50)
def eb_encode(text: str) -> bytes:
    res = bytearray()
    for ch in text:
        if ch == " ":
            res.append(0x50)
        elif "A" <= ch <= "Z":
            res.append(ord(ch) + 0x30)
        elif "a" <= ch <= "z":
            res.append(ord(ch) + 0x30)
        elif "0" <= ch <= "9":
            res.append(ord(ch) + 0x30)
        else:
            res.append(ord(ch))
    return bytes(res)


THEMATIC_NAMES = [
    # Phase 5 thematic items and early enemies
    "The OOM Killer",
    "Null Reference Crow",
    "Dangling Pointer",
    "Runaway Thread",
    "Fork Bomb",
    "Dirty Page",
    # Phase 7 thematic enemies
    "Runaway Linter",
    "Deadlock Tree",
    "Stack Overflow Mole",
    # Phase 8 thematic enemies
    "Buffer Overrun",
    "Defunct Process",
    "Zombie PID",
    "Rootkit Sprout",
    "Memory Leak Daemon",
    "Malicious Daemon",
    # Phase 9 thematic enemies
    "Sparse Defrag Digger",
    "Thread Terminus",
    "Rootkit Core",
    "Memory Corruptor Rat",
    "Clock Jitter",
    "DMA Pump",
    # Phase 10 thematic enemies
    "Packet Storm Kraken",
    "Fragmented Struct",
    "Corrupt Struct",
    "Recursive Sprout",
    "Interrupt Mite",
    "Heap Dump",
    # Phase 11 thematic enemies
    "Cascading Leak Daemon",
    "Instruction Decoder",
    "Security Enclave Guard",
    "Fragmented Heap Dump",
    "Signal Jitter Eel",
    "Packet Loss Slug",
    # Phase 12 thematic enemies
    "Telemetry Monitor",
    "Thermal Runaway",
    "Crystallized Mutex",
    "Kernel Power Unit",
    "Legacy Thread",
    "Monolithic Struct",
    "PRNG Generator",
    "Process Orb",
    # Phase 13 thematic enemies
    "Root Mutex Lock",
    "Hypervisor Kraken",
    "Socket Exception",
    "Fatal Signal",
    "Unbounded Task",
    "Atomic Register",
    # Phase 14 thematic enemies
    "Ghost Thread",
    "Watchdog Daemon",
    "Bus Octobot",
    "Supervisor Starman",
    # Phase 15 thematic enemies
    "Root Starman",
    "Monolithic Octobot",
    "Reactor Daemon",
    "Thread Shambler",
    "Rootkit Pokey",
    # Phase 16: Architectural PSI and Diagnostic Hardware
    "PSI Fork",
    "PSI SIGKILL",
    "PSI SIGBUS",
    "PSI Defrag",
    "PSI Flush",
    "Heap Clean",
    "Mutex Lock",
    "Kernel Mutex",
    "Core Dump",
    "Bus Analyzer",
    "Logic Probe",
    "Interrupt Vector",
    "Worn Polarized Lens",
    # Phase 17: Memory Pressure and Compaction
    "Garbage Collector",
    "sector memory pressure",
    "sector memory pressure reset",
]


def load_summary_labels(summary_path: str = SUMMARY_PATH) -> dict:
    labels = {}
    if not os.path.isfile(summary_path):
        return labels
    with open(summary_path, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.split()
            if len(parts) >= 2 and parts[1].startswith("$"):
                try:
                    labels[parts[0]] = int(parts[1][1:], 16)
                except ValueError:
                    pass
    return labels


def main() -> int:
    if not os.path.isfile(ROM_PATH):
        print(f"ERROR: ROM not found at {ROM_PATH}. Run tools/build.sh first.")
        return 1

    size = os.path.getsize(ROM_PATH)
    if size != EXPECTED_SIZE:
        print(f"ERROR: Invalid ROM size {size} bytes (expected {EXPECTED_SIZE}).")
        return 1

    labels = load_summary_labels()
    if not labels:
        print(f"ERROR: Failed to load compiled symbols from {SUMMARY_PATH}")
        return 1

    errors = 0
    with open(ROM_PATH, "rb") as f:
        rom_data = f.read()

        # Check HiROM SNES title at 0xFFC0
        f.seek(0xFFC0)
        title = f.read(21)
        if title != b"EARTH BOUND          ":
            print(f"ERROR: Unexpected internal title: {title!r}")
            errors += 1
        else:
            print(f"OK: Internal SNES Title: {title.decode('latin1').strip()}")

        for offset, expected_prefix, description in HOOKS:
            f.seek(offset)
            actual = f.read(len(expected_prefix))
            if actual != expected_prefix:
                print(
                    f"ERROR: Hook mismatch for {description} at {hex(offset)}: "
                    f"expected {expected_prefix.hex()}, found {actual.hex()}"
                )
                errors += 1
            else:
                print(f"OK: {description} verified at {hex(offset)}")

        # Verify Action 197 Developer Debug Menu bindings
        debug_menu_addr = labels.get("l_0xc58000")
        if not debug_menu_addr:
            print("ERROR: Symbol 'l_0xc58000' not found in summary.txt")
            errors += 1
        else:
            expected_text_ptr = debug_menu_addr.to_bytes(4, "little")
            f.seek(0x1584A8)
            actual_text_ptr = f.read(4)
            if actual_text_ptr != expected_text_ptr:
                print(
                    f"ERROR: ATM Card Debug Menu Text Hook mismatch at 0x1584a8: "
                    f"expected {expected_text_ptr.hex()}, found {actual_text_ptr.hex()}"
                )
                errors += 1
            else:
                print(f"OK: ATM Card Debug Menu Text Hook (Action 197) verified at 0x1584a8 (${hex(debug_menu_addr)})")

            # Safe return code pointer ($C29039)
            f.seek(0x1584AC)
            actual_code_ptr = f.read(4)
            if actual_code_ptr != b"\x39\x90\xc2\x00":
                print(
                    f"ERROR: ATM Card Safe Return Code Pointer mismatch at 0x1584ac: "
                    f"expected 3990c200, found {actual_code_ptr.hex()}"
                )
                errors += 1
            else:
                print("OK: ATM Card Safe Return Code Pointer (Action 197) verified at 0x1584ac")

            # Legacy dialogue trampoline at l_0xc9fbf2
            legacy_addr = labels.get("l_0xc9fbf2")
            if not legacy_addr:
                print("ERROR: Symbol 'l_0xc9fbf2' not found in summary.txt")
                errors += 1
            else:
                legacy_bank = (legacy_addr >> 16) & 0xFF
                legacy_offset = ((legacy_bank - 0xC0) << 16) | (legacy_addr & 0xFFFF)
                f.seek(legacy_offset)
                actual_trampoline = f.read(5)
                expected_trampoline = b"\x0A" + expected_text_ptr
                if actual_trampoline != expected_trampoline:
                    print(
                        f"ERROR: ATM Card Legacy Trampoline mismatch at {hex(legacy_offset)}: "
                        f"expected {expected_trampoline.hex()}, found {actual_trampoline.hex()}"
                    )
                    errors += 1
                else:
                    print(f"OK: ATM Card Legacy Dialogue Trampoline verified at {hex(legacy_offset)}")

        # Resolve active dynamic NPC configuration table base offset
        npc_table_addr = rom_data[0x131CB] | (rom_data[0x131CC] << 8)
        npc_table_bank = rom_data[0x131D0]
        npc_table_file_offset = ((npc_table_bank - 0xC0) << 16) | npc_table_addr

        for npc_id, label_name, description in NPC_BINDINGS:
            target_addr = labels.get(label_name)
            if not target_addr:
                print(f"ERROR: Target symbol '{label_name}' for NPC {npc_id} not found in summary.txt")
                errors += 1
                continue
            expected_ptr = target_addr.to_bytes(3, "little")
            offset = npc_table_file_offset + (npc_id * 17) + 9
            f.seek(offset)
            actual = f.read(len(expected_ptr))
            if actual != expected_ptr:
                print(
                    f"ERROR: Pointer mismatch for {description} at {hex(offset)}: "
                    f"expected {expected_ptr.hex()} (${hex(target_addr)}), found {actual.hex()}"
                )
                errors += 1
            else:
                print(f"OK: {description} verified at {hex(offset)} (${hex(target_addr)})")

        for name in THEMATIC_NAMES:
            encoded = eb_encode(name)
            if encoded in rom_data:
                print(f"OK: Thematic string '{name}' verified in ROM")
            else:
                print(f"ERROR: Thematic string '{name}' not found in ROM")
                errors += 1

    total_checks = 1 + len(HOOKS) + 3 + len(NPC_BINDINGS) + len(THEMATIC_NAMES)
    if errors == 0:
        print(f"\nAll {total_checks} binary assertions passed successfully.")
        return 0
    else:
        print(f"\nVerification failed with {errors} error(s).")
        return 1


if __name__ == "__main__":
    sys.exit(main())
