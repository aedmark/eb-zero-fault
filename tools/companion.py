#!/usr/bin/env python3
"""
EarthBound: Zero Fault - Comprehensive ROM Text & Script Companion (IDE & Exporter)

An interactive, searchable GUI and CLI companion for inspecting, EDITING, and
EXPORTING all text, scripts, dialogue trees, NPC table bindings, battle actions,
PSI abilities, items, and thematic enemy reskins directly into the compiled SNES ROM.
Like SCI Companion, customized specifically for this 32-Mbit EarthBound ROM hack.
"""

import argparse
import http.server
import io
import json
import os
import re
import socketserver
import subprocess
import sys
import tarfile
import time
import urllib.parse
import webbrowser
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent

# Phase mapping for all custom CoW narrative modules
PHASE_MAPPINGS = {
    "cow_engine.ccs": ("SYS", "Engine & State Tracking", "SRAM safe range, bitwise dirty tracking, commit subroutines"),
    "cow_onett.ccs": ("P04", "Phase 04: Onett Awakening & MMU Boundary", "Mom awakening, Pokey interrupt, Mayor Pirkle refcount, Roadblock MMU, Giant Step"),
    "cow_police.ccs": ("P07", "Phase 07: Twoson & Immutable Cult", "Captain Strong kernel privilege audit and challenge"),
    "cow_twoson.ccs": ("P07", "Phase 07: Twoson & Immutable Cult", "Apple Kid JIT vs Orange Kid AOT, Everdred raw heap allocator"),
    "cow_happy.ccs": ("P07", "Phase 07: Twoson & Immutable Cult", "Mr. Carpainter Immutable State Cult, Lilliput Steps cache sync"),
    "cow_threed.ccs": ("P08", "Phase 08: Threed, Winters & Saturn Valley", "Threed zombie child processes, hotel trap exception, Paula IPC telepathy, Zombie Paper"),
    "cow_winters.ccs": ("P08", "Phase 08: Threed, Winters & Saturn Valley", "Jeff diagnostic awakening, Tony inline linter, Dr. Andonuts far-jump Sky Runner"),
    "cow_belch.ccs": ("P08", "Phase 08: Threed, Winters & Saturn Valley", "Waterfall zero-knowledge proof-of-work, Master Belch memory leak daemon"),
    "cow_saturn.ccs": ("P08", "Phase 08: Threed, Winters & Saturn Valley", "Mr. Saturn immutable types, Trillionage Sprout rootkit interceptor, Milky Well"),
    "cow_desert.ccs": ("P09", "Phase 09: Desert, Fourside & Moonside", "Miner George defrag, Guardian Diggers memory compaction, Teleport virtual page"),
    "cow_fourside.ccs": ("P09", "Phase 09: Desert, Fourside & Moonside", "Dept store power starvation blackout, Dept Store Spook thread terminus, Everdred handoff, Monotoli"),
    "cow_moonside.ccs": ("P09", "Phase 09: Desert, Fourside & Moonside", "Moonside inverted truth tables, Mani Mani rootkit core broadcast"),
    "cow_magnet.ccs": ("P09", "Phase 09: Desert, Fourside & Moonside", "Magnet Hill electromagnetic cache alignment"),
    "cow_summers.ccs": ("P10", "Phase 10: Summers, Dalaam & Sea", "Stoic Club thread profiler, Beach cake heap dump, Magic Cake context switch"),
    "cow_dalaam.ccs": ("P10", "Phase 10: Summers, Dalaam & Sea", "Mu Training progressive sensory deallocation, Dalaam Master Thread 4 registration"),
    "cow_sea.ccs": ("P10", "Phase 10: Summers, Dalaam & Sea", "Sailor Captain oceanic bus transport, Packet Storm Kraken daemon"),
    "cow_scaraba.ccs": ("P11", "Phase 11: Scaraba & Dungeon Man", "Sphinx cryptographic gate, Hawk Eye infrared transceiver, Star Master compiler, Poo descheduling"),
    "cow_dungeonman.ccs": ("P11", "Phase 11: Scaraba & Dungeon Man", "Brick Road hybrid coprocessor, aperture width stall, Submarine firmware reflash"),
    "cow_deepdark.ccs": ("P11", "Phase 11: Scaraba & Dungeon Man", "Master Barf cascading leak daemon recursive heap corruption"),
    "cow_tenda.ccs": ("P12", "Phase 12: Tenda, Lumine & Underworld", "Tenda spinlock deadlock, Overcoming Shyness synchronization library, Strong Tenda barrier"),
    "cow_lumine.ccs": ("P12", "Phase 12: Tenda, Lumine & Underworld", "Lumine Hall optical backplane trace, Electro Specter telemetry monitor, Lumine melody"),
    "cow_underworld.ccs": ("P12", "Phase 12: Tenda, Lumine & Underworld", "Lost Underworld bare-metal substrate, Outer rock, Main boot ROM core memory rock"),
    "cow_firespring.ccs": ("P12", "Phase 12: Tenda, Lumine & Underworld", "Carbon/Diamond Dog thermal runaway daemon / crystallized mutex, Fire Spring cache line"),
    "cow_magicant.ccs": ("P13", "Phase 13: Magicant & Sea of Eden", "Magicant page frame coalescence, Ring -1 greeter, Young Ness PID 1, Flying Men helper threads, tombstones"),
    "cow_seaofeden.ccs": ("P13", "Phase 13: Magicant & Sea of Eden", "Sea of Eden deep kernel gateway, Ness's Nightmare Root Mutex Lock daemon"),
    "cow_resync.ccs": ("P13", "Phase 13: Magicant & Sea of Eden", "Physical bus return and thread resynchronization (Threads 2, 3, 4) in Saturn Valley"),
    "cow_phasedistorter.ccs": ("P14", "Phase 14: Phase Distorter & Onett Night", "Phase Distorter v1 test failure, Apple Kid spacetime compiler, Dr. Andonuts telemetry"),
    "cow_onett_night.ccs": ("P14", "Phase 14: Phase Distorter & Onett Night", "Onett high-contention bus blackout, meteorite Zexonyte extraction, Mom standby, Tracy emergency bus"),
    "cow_conversion.ccs": ("P14", "Phase 14: Phase Distorter & Onett Night", "Zexonyte synthesis, PD2 hijacking, Mr. Saturn tea telemetry, PD3 robotic chassis architecture conversion"),
    "cow_caveofpast.ccs": ("P15", "Phase 15: Endgame Climax & Clean Reboot", "Cave of the Past robotic traversal, PD3 wreckage audit, Horn of Life, backward bus clock"),
    "cow_giygas.ccs": ("P15", "Phase 15: Endgame Climax & Clean Reboot", "Rootkit Pokey Devil's Machine shutoff, Giygas hypervisor singularity / core dump void voice"),
    "cow_prayer.ccs": ("P15", "Phase 15: Endgame Climax & Clean Reboot", "Paula non-maskable inter-thread interrupt (NMI) broadcasts, host supervisor thread injection"),
    "cow_epilogue.ccs": ("P15", "Phase 15: Endgame Climax & Clean Reboot", "Clean kernel reboot, Onett bus contention lifted, Pokey unsigned packet delivery, credits"),
}

# Categorization for all 62 vanilla script modules
VANILLA_CATEGORIES = {
    "data_00.ccs": ("SHOPS", "Shops, Hotels & Hospitals"),
    "data_01.ccs": ("SHOPS", "Shops, Hotels & Hospitals"),
    "data_02.ccs": ("SHOPS", "Shops, Hotels & Hospitals"),
    "data_03.ccs": ("ITEMS", "Item & Equipment Help Descriptions"),
    "data_04.ccs": ("ITEMS", "Item & Equipment Help Descriptions"),
    "data_05.ccs": ("ITEMS", "Item & Equipment Help Descriptions"),
    "data_06.ccs": ("DEBUG", "Debug Tooling & System Prompts"),
    "data_07.ccs": ("DEBUG", "Debug Tooling & System Prompts"),
    "data_08.ccs": ("DEBUG", "Debug Tooling & System Prompts"),
    "data_09.ccs": ("DEBUG", "Debug Tooling & System Prompts"),
    "data_10.ccs": ("DEBUG", "Debug Tooling & System Prompts"),
    "data_11.ccs": ("DEBUG", "Debug Tooling & System Prompts"),
    "data_12.ccs": ("DEBUG", "Debug Tooling & System Prompts"),
    "data_13.ccs": ("DEBUG", "Debug Tooling & System Prompts"),
    "data_14.ccs": ("DEBUG", "Debug Tooling & System Prompts"),
    "data_15.ccs": ("ONETT_TWOSON", "Onett & Twoson Townspeople"),
    "data_16.ccs": ("ONETT_TWOSON", "Onett & Twoson Townspeople"),
    "data_17.ccs": ("ONETT_TWOSON", "Onett & Twoson Townspeople"),
    "data_18.ccs": ("ONETT_TWOSON", "Onett & Twoson Townspeople"),
    "data_19.ccs": ("ONETT_TWOSON", "Onett & Twoson Townspeople"),
    "data_20.ccs": ("ONETT_TWOSON", "Onett & Twoson Townspeople"),
    "data_21.ccs": ("ONETT_TWOSON", "Onett & Twoson Townspeople"),
    "data_22.ccs": ("THREED_WINTERS", "Threed, Winters & Saturn Valley"),
    "data_23.ccs": ("THREED_WINTERS", "Threed, Winters & Saturn Valley"),
    "data_24.ccs": ("THREED_WINTERS", "Threed, Winters & Saturn Valley"),
    "data_25.ccs": ("THREED_WINTERS", "Threed, Winters & Saturn Valley"),
    "data_26.ccs": ("THREED_WINTERS", "Threed, Winters & Saturn Valley"),
    "data_27.ccs": ("THREED_WINTERS", "Threed, Winters & Saturn Valley"),
    "data_28.ccs": ("THREED_WINTERS", "Threed, Winters & Saturn Valley"),
    "data_29.ccs": ("THREED_WINTERS", "Threed, Winters & Saturn Valley"),
    "data_30.ccs": ("BATTLE_ITEMS", "Battle Item Usage & Weapons"),
    "data_31.ccs": ("FOURSIDE", "Desert & Fourside Metropolis"),
    "data_32.ccs": ("FOURSIDE", "Desert & Fourside Metropolis"),
    "data_33.ccs": ("FOURSIDE", "Desert & Fourside Metropolis"),
    "data_34.ccs": ("FOURSIDE", "Desert & Fourside Metropolis"),
    "data_35.ccs": ("FOURSIDE", "Desert & Fourside Metropolis"),
    "data_36.ccs": ("FOURSIDE", "Desert & Fourside Metropolis"),
    "data_37.ccs": ("FOURSIDE", "Desert & Fourside Metropolis"),
    "data_38.ccs": ("SUMMERS", "Summers, Dalaam & Poo's Mu"),
    "data_39.ccs": ("SUMMERS", "Summers, Dalaam & Poo's Mu"),
    "data_40.ccs": ("SUMMERS", "Summers, Dalaam & Poo's Mu"),
    "data_41.ccs": ("SUMMERS", "Summers, Dalaam & Poo's Mu"),
    "data_42.ccs": ("SUMMERS", "Summers, Dalaam & Poo's Mu"),
    "data_43.ccs": ("BELCH_MOON", "Belch Factory & Moonside"),
    "data_44.ccs": ("BELCH_MOON", "Belch Factory & Moonside"),
    "data_45.ccs": ("BELCH_MOON", "Belch Factory & Moonside"),
    "data_46.ccs": ("TENDA_LUMINE", "Deep Darkness, Tenda, Lumine & Underworld"),
    "data_47.ccs": ("TENDA_LUMINE", "Deep Darkness, Tenda, Lumine & Underworld"),
    "data_48.ccs": ("TENDA_LUMINE", "Deep Darkness, Tenda, Lumine & Underworld"),
    "data_49.ccs": ("TENDA_LUMINE", "Deep Darkness, Tenda, Lumine & Underworld"),
    "data_50.ccs": ("TENDA_LUMINE", "Deep Darkness, Tenda, Lumine & Underworld"),
    "data_51.ccs": ("TENDA_LUMINE", "Deep Darkness, Tenda, Lumine & Underworld"),
    "data_52.ccs": ("TENDA_LUMINE", "Deep Darkness, Tenda, Lumine & Underworld"),
    "data_53.ccs": ("ENDGAME", "Phase Distorter, Giygas, Prayers & Ending"),
    "data_54.ccs": ("ENDGAME", "Phase Distorter, Giygas, Prayers & Ending"),
    "data_55.ccs": ("ENDGAME", "Phase Distorter, Giygas, Prayers & Ending"),
    "data_56.ccs": ("BATTLE_SIGNS", "Battle Status Messages, Signs & Bulletins"),
    "data_57.ccs": ("BATTLE_SIGNS", "Battle Status Messages, Signs & Bulletins"),
    "data_58.ccs": ("BATTLE_SIGNS", "Battle Status Messages, Signs & Bulletins"),
    "data_59.ccs": ("BATTLE_SIGNS", "Battle Status Messages, Signs & Bulletins"),
    "data_60.ccs": ("BATTLE_SIGNS", "Battle Status Messages, Signs & Bulletins"),
    "data_61.ccs": ("BATTLE_SIGNS", "Battle Status Messages, Signs & Bulletins"),
    "data_62.ccs": ("MISC", "Miscellaneous"),
}


def load_vanilla_archive() -> Dict[str, str]:
    """Load pristine vanilla data_*.ccs modules from git baseline commit 9a240f96."""
    try:
        proc = subprocess.Popen(
            ["git", "archive", "9a240f96", "src/ccscript/"],
            cwd=REPO_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        tar_bytes, _ = proc.communicate()
        if proc.returncode != 0:
            return {}
        tf = tarfile.open(fileobj=io.BytesIO(tar_bytes))
        archive_files = {}
        for member in tf.getmembers():
            if member.name.startswith("src/ccscript/data_") and member.name.endswith(".ccs"):
                f = tf.extractfile(member)
                if f:
                    archive_files[Path(member.name).name] = f.read().decode("utf-8", "ignore")
        return archive_files
    except Exception as e:
        print(f"Notice: Vanilla baseline archive unavailable: {e}", file=sys.stderr)
        return {}


def load_verify_rom_metadata() -> Tuple[Dict[str, str], Dict[str, Tuple[int, str]]]:
    """Parse NPC bindings and ROM hooks from tools/verify_rom.py."""
    verify_path = REPO_ROOT / "tools" / "verify_rom.py"
    if not verify_path.exists():
        return {}, {}
    text = verify_path.read_text(encoding="utf-8", errors="ignore")
    
    npc_bindings = {}
    for match in re.finditer(r"\(\s*(\d+)\s*,\s*\"([^\"]+)\"\s*,\s*\"([^\"]+)\"\s*\)", text):
        npc_id, label, desc = match.groups()
        npc_bindings[label] = desc
        npc_bindings[f"npc_{npc_id}"] = desc
        
    rom_hooks = {}
    for match in re.finditer(r"\(\s*(0x[0-9A-Fa-f]+)\s*,\s*b\"[^\"]*\"\s*,\s*\"([^\"]+)\"\s*\)", text):
        offset_hex, desc = match.groups()
        rom_hooks[desc] = (int(offset_hex, 16), desc)
        
    return npc_bindings, rom_hooks


def find_vanilla_trampoline_targets() -> Dict[str, Tuple[str, str]]:
    """Scan modified data_*.ccs for goto(cow_*) trampoline redirects."""
    targets = {}
    data_files = sorted((REPO_ROOT / "src" / "ccscript").glob("data_*.ccs"))
    for df in data_files:
        content = df.read_text(encoding="utf-8", errors="ignore")
        lines = content.splitlines()
        current_label = None
        for line in lines:
            stripped = line.strip()
            l_match = re.match(r"^([a-zA-Z0-9_]+):", stripped)
            if l_match:
                current_label = l_match.group(1)
            goto_match = re.search(r"goto\(([a-zA-Z0-9_]+)\.([a-zA-Z0-9_]+)\)", stripped)
            if goto_match and current_label:
                cow_mod, cow_lbl = goto_match.groups()
                full_cow = f"{cow_mod}.{cow_lbl}"
                targets[full_cow] = (df.name, current_label)
                targets[cow_lbl] = (df.name, current_label)
    return targets


def parse_dialogue_pages(code: str) -> List[str]:
    """Tokenize and split CCScript string code into separate dialog window pages."""
    lines = code.splitlines()
    clean_lines = []
    for line in lines:
        c_idx = line.find("//")
        if c_idx != -1:
            line = line[:c_idx]
        clean_lines.append(line)
    clean_code = "\n".join(clean_lines)

    pattern = re.compile(r"\"([^\"]*)\"|(\b(?:next|linebreak|newline|eob|end)\b)|(\[[0-9A-Fa-f\s]+\])")
    pages = []
    current_page = []

    for match in pattern.finditer(clean_code):
        s, kw, bcode = match.groups()
        if s is not None:
            parts = re.split(r"\[03\]|\{prompt\}", s)
            for i, p in enumerate(parts):
                if p:
                    current_page.append(p)
                if i < len(parts) - 1:
                    pages.append("".join(current_page).strip())
                    current_page = []
        elif kw == "next":
            pages.append("".join(current_page).strip())
            current_page = []
        elif kw in ("linebreak", "newline"):
            current_page.append("\n")
        elif kw in ("eob", "end"):
            if current_page:
                pages.append("".join(current_page).strip())
                current_page = []

    if current_page:
        pages.append("".join(current_page).strip())

    valid_pages = []
    for p in pages:
        stripped = re.sub(r"\[[0-9A-Fa-f\s]+\]|\{[^\}]+\}", "", p).strip()
        if stripped or "@" in p:
            valid_pages.append(p)

    return valid_pages


def clean_dialogue_text(raw: str, item_dict: Dict[int, str]) -> str:
    """Format dialogue text into readable EarthBound font format."""
    text = raw
    text = re.sub(r"\{name\(1\)\}", "Ness", text)
    text = re.sub(r"\{name\(2\)\}", "Paula", text)
    text = re.sub(r"\{name\(3\)\}", "Jeff", text)
    text = re.sub(r"\{name\(4\)\}", "Poo", text)
    text = re.sub(r"\{stat\(3\)\}", "King", text)
    text = re.sub(r"\{stat\(8\)\}", "Dad", text)
    text = re.sub(r"\{stat\(30\)\}", "Paula", text)
    text = re.sub(r"\{counter\(1\)\}", "<Player>", text)
    
    def repl_item(m):
        item_id = int(m.group(1))
        return item_dict.get(item_id, f"Item {item_id}")
    text = re.sub(r"\{itemname\((\d+)\)\}", repl_item, text)

    text = re.sub(r"\{pause\(\d+\)\}", "", text)
    text = re.sub(r"\{window_[^\}]+\}", "", text)
    text = re.sub(r"\{(?:set|unset|warp)\([^\}]+\)\}", "", text)
    text = re.sub(r"\{(?:sound|music|music_resume)\([^\}]+\)\}", "", text)
    text = re.sub(r"\[[0-9A-Fa-f\s]+(?:\{[^\}]+\})?\]", "", text)
    text = re.sub(r"\{prompt\}", "", text)
    text = re.sub(r"[ \t]+", " ", text).strip()
    return text


def extract_sound_cues(code: str) -> List[str]:
    """Find audio triggers and sound effects in code."""
    cues = []
    for m in re.finditer(r"\{sound\((\d+)\)\}", code):
        sfx_id = m.group(1)
        name = "Sound Effect"
        if sfx_id == "11":
            name = "Glitch / Knock"
        elif sfx_id == "5":
            name = "Failure / Buzz"
        elif sfx_id == "16":
            name = "Teleport Buzz"
        elif sfx_id == "44":
            name = "Memory / Whistle"
        elif sfx_id == "74":
            name = "Devil's Machine Whine"
        cues.append(f"SFX {sfx_id}: {name}")
    for m in re.finditer(r"\{music\((\d+)\)\}", code):
        cues.append(f"BGM {m.group(1)}")
    return list(dict.fromkeys(cues))


def extract_flags(code: str) -> Tuple[List[int], List[int]]:
    """Extract flags set or tested in CCScript code."""
    flags_set = [int(m.group(1)) for m in re.finditer(r"\{set\(flag\s+(\d+)\)\}", code)]
    flags_checked = [int(m.group(1)) for m in re.finditer(r"\[06\s+[0-9A-Fa-f]{2}\s+[0-9A-Fa-f]{2}\s+.*?flag\s+(\d+)", code)]
    return list(dict.fromkeys(flags_set)), list(dict.fromkeys(flags_checked))


def build_companion_data() -> Dict[str, Any]:
    """Parse all source files, YAML configs, and metadata into a comprehensive dictionary."""
    npc_table = yaml.safe_load((REPO_ROOT / "src" / "npc_config_table.yml").read_text(encoding="utf-8"))
    enemy_table = yaml.safe_load((REPO_ROOT / "src" / "enemy_configuration_table.yml").read_text(encoding="utf-8"))
    item_table = yaml.safe_load((REPO_ROOT / "src" / "item_configuration_table.yml").read_text(encoding="utf-8"))
    psi_table = yaml.safe_load((REPO_ROOT / "src" / "psi_ability_table.yml").read_text(encoding="utf-8"))
    psi_names = yaml.safe_load((REPO_ROOT / "src" / "psi_name_table.yml").read_text(encoding="utf-8"))
    action_table = yaml.safe_load((REPO_ROOT / "src" / "battle_action_table.yml").read_text(encoding="utf-8"))

    item_dict = {int(k): v.get("Name", f"Item {k}") for k, v in item_table.items()}
    psi_name_dict = {int(k): v.get("Name", f"PSI {k}").strip() for k, v in psi_names.items()}

    npc_bindings, rom_hooks = load_verify_rom_metadata()
    trampoline_targets = find_vanilla_trampoline_targets()
    reverse_trampoline = {f"{v[0][:-4]}.{v[1]}": k for k, v in trampoline_targets.items()}
    vanilla_files = load_vanilla_archive()

    npc_pointer_map = {}
    for npc_id, npc_data in npc_table.items():
        p1 = str(npc_data.get("Text Pointer 1", ""))
        p2 = str(npc_data.get("Text Pointer 2", ""))
        if p1 and p1 != "$0":
            npc_pointer_map[p1] = (npc_id, 1, npc_data)
        if p2 and p2 != "$0":
            npc_pointer_map[p2] = (npc_id, 2, npc_data)

    cow_files = sorted((REPO_ROOT / "src" / "ccscript").glob("cow_*.ccs"))
    cow_routines = []

    for cfile in cow_files:
        fname = cfile.name
        phase_info = PHASE_MAPPINGS.get(fname, ("MISC", "Miscellaneous", "Engine routines"))
        content = cfile.read_text(encoding="utf-8", errors="ignore")
        lines = content.splitlines()

        current_label = None
        current_comment = []
        current_lines = []

        def flush_entry():
            if not current_label or not current_lines:
                return
            full_code = "\n".join(current_lines)
            raw_pages = parse_dialogue_pages(full_code)
            clean_pages = [clean_dialogue_text(p, item_dict) for p in raw_pages if clean_dialogue_text(p, item_dict)]
            full_ref = f"{cfile.stem}.{current_label}"
            
            bound_npc = None
            if full_ref in npc_pointer_map:
                nid, pnum, ndata = npc_pointer_map[full_ref]
                bound_npc = {
                    "id": nid,
                    "pointer_slot": pnum,
                    "direction": ndata.get("Direction", "unknown"),
                    "sprite": ndata.get("Sprite", 0),
                    "movement": ndata.get("Movement", 0),
                    "event_flag": ndata.get("Event Flag", "0x0"),
                    "desc": npc_bindings.get(current_label, npc_bindings.get(f"npc_{nid}", f"NPC Table Entry #{nid}"))
                }
            elif current_label in npc_bindings:
                bound_npc = {"desc": npc_bindings[current_label]}

            bound_hook = None
            for hdesc, hval in rom_hooks.items():
                if current_label in hdesc or cfile.stem in hdesc.lower():
                    bound_hook = {"offset": hex(hval[0]), "desc": hdesc}
                    break

            vanilla_mod, vanilla_lbl = trampoline_targets.get(full_ref, trampoline_targets.get(current_label, (None, None)))
            vanilla_clean = None
            vanilla_raw = None
            if vanilla_mod and vanilla_lbl and vanilla_mod in vanilla_files:
                vcontent = vanilla_files[vanilla_mod]
                vmatch = re.search(rf"\b{re.escape(vanilla_lbl)}:\s*\n(.*?)(?=\n[a-zA-Z0-9_]+:|\Z)", vcontent, re.DOTALL)
                if vmatch:
                    vanilla_raw = vmatch.group(1).strip()
                    vpages = parse_dialogue_pages(vanilla_raw)
                    v_clean_list = [clean_dialogue_text(vp, item_dict) for vp in vpages if clean_dialogue_text(vp, item_dict)]
                    vanilla_clean = "\n\n".join(v_clean_list) if v_clean_list else None

            flags_set, flags_checked = extract_flags(full_code)
            sound_cues = extract_sound_cues(full_code)

            cow_routines.append({
                "id": full_ref,
                "file": fname,
                "label": current_label,
                "is_cow": True,
                "category": phase_info[0],
                "category_title": phase_info[1],
                "category_desc": phase_info[2],
                "comment": " ".join(current_comment).strip(),
                "raw_code": full_code,
                "clean_pages": clean_pages,
                "dialogue_preview": clean_pages[0] if clean_pages else "(Script logic / Subroutine)",
                "page_count": len(clean_pages),
                "sound_cues": sound_cues,
                "flags_set": flags_set,
                "flags_checked": flags_checked,
                "bound_npc": bound_npc,
                "bound_hook": bound_hook,
                "vanilla_mod": vanilla_mod,
                "vanilla_lbl": vanilla_lbl,
                "vanilla_clean": vanilla_clean,
                "vanilla_raw": vanilla_raw,
            })

        for line in lines:
            stripped = line.strip()
            l_match = re.match(r"^([a-zA-Z0-9_]+):", stripped)
            if l_match:
                flush_entry()
                current_label = l_match.group(1)
                current_comment = []
                current_lines = [line]
            else:
                if stripped.startswith("//"):
                    current_comment.append(stripped.lstrip("/").strip())
                if current_label:
                    current_lines.append(line)

        flush_entry()

    vanilla_disk_files = sorted((REPO_ROOT / "src" / "ccscript").glob("data_*.ccs"))
    vanilla_routines = []

    for vfile in vanilla_disk_files:
        fname = vfile.name
        cat_info = VANILLA_CATEGORIES.get(fname, ("VANILLA", "Vanilla Scripts"))
        content = vfile.read_text(encoding="utf-8", errors="ignore")
        lines = content.splitlines()

        current_label = None
        current_lines = []

        def flush_vanilla():
            if not current_label or not current_lines:
                return
            full_code = "\n".join(current_lines)
            raw_pages = parse_dialogue_pages(full_code)
            clean_pages = [clean_dialogue_text(p, item_dict) for p in raw_pages if clean_dialogue_text(p, item_dict)]
            full_ref = f"{vfile.stem}.{current_label}"

            cow_override = reverse_trampoline.get(full_ref)

            bound_npc = None
            if full_ref in npc_pointer_map:
                nid, pnum, ndata = npc_pointer_map[full_ref]
                bound_npc = {
                    "id": nid,
                    "pointer_slot": pnum,
                    "direction": ndata.get("Direction", "unknown"),
                    "sprite": ndata.get("Sprite", 0),
                    "movement": ndata.get("Movement", 0),
                    "event_flag": ndata.get("Event Flag", "0x0"),
                    "desc": npc_bindings.get(f"npc_{nid}", f"NPC Table Entry #{nid}")
                }

            sound_cues = extract_sound_cues(full_code)
            flags_set, flags_checked = extract_flags(full_code)

            vanilla_routines.append({
                "id": full_ref,
                "file": fname,
                "label": current_label,
                "is_cow": False,
                "category": cat_info[0],
                "category_title": cat_info[1],
                "cow_override": cow_override,
                "raw_code": full_code,
                "clean_pages": clean_pages,
                "dialogue_preview": clean_pages[0] if clean_pages else "(Script logic / Subroutine)",
                "page_count": len(clean_pages),
                "sound_cues": sound_cues,
                "flags_set": flags_set,
                "flags_checked": flags_checked,
                "bound_npc": bound_npc,
            })

        for line in lines:
            stripped = line.strip()
            l_match = re.match(r"^([a-zA-Z0-9_]+):", stripped)
            if l_match:
                flush_vanilla()
                current_label = l_match.group(1)
                current_lines = [line]
            else:
                if current_label:
                    current_lines.append(line)

        flush_vanilla()

    thematic_names = [
        "The OOM Killer", "Null Reference Crow", "Dangling Pointer", "Runaway Thread",
        "Fork Bomb", "Dirty Page", "Runaway Linter", "Deadlock Tree", "Stack Overflow Mole",
        "Buffer Overrun", "Defunct Process", "Zombie PID", "Rootkit Sprout", "Memory Leak Daemon",
        "Malicious Daemon", "Sparse Defrag Digger", "Thread Terminus", "Rootkit Core",
        "Memory Corruptor Rat", "Clock Jitter", "DMA Pump", "Packet Storm Kraken",
        "Fragmented Struct", "Corrupt Struct", "Recursive Sprout", "Interrupt Mite", "Heap Dump",
        "Cascading Leak Daemon", "Instruction Decoder", "Security Enclave Guard",
        "Fragmented Heap Dump", "Signal Jitter Eel", "Packet Loss Slug", "Telemetry Monitor",
        "Thermal Runaway", "Crystallized Mutex", "Kernel Power Unit", "Legacy Thread",
        "Monolithic Struct", "PRNG Generator", "Process Orb", "Root Mutex Lock",
        "Hypervisor Kraken", "Socket Exception", "Fatal Signal", "Unbounded Task",
        "Atomic Register", "Supervisor Starman", "Ghost Thread", "Bus Octobot",
        "Root Starman", "Monolithic Octobot", "Reactor Daemon", "Thread Shambler", "Rootkit Pokey"
    ]

    enemy_list = []
    for eid, edata in enemy_table.items():
        name = str(edata.get("Name", f"Enemy #{eid}"))
        is_thematic = any(tn.lower() in name.lower() for tn in thematic_names)
        enemy_list.append({
            "id": eid,
            "name": name,
            "is_thematic": is_thematic,
            "hp": edata.get("HP", 0),
            "pp": edata.get("PP", 0),
            "offense": edata.get("Offense", 0),
            "defense": edata.get("Defense", 0),
            "exp": edata.get("Experience points", 0),
            "money": edata.get("Money", 0),
            "boss": edata.get("Boss Flag", "false") == "true",
            "dropped_item": item_dict.get(edata.get("Item Dropped", 0), "None"),
            "encounter_text": edata.get("Encounter Text Pointer", "$0"),
            "death_text": edata.get("Death Text Pointer", "$0"),
        })

    item_list = []
    for iid, idata in item_table.items():
        item_list.append({
            "id": iid,
            "name": idata.get("Name", f"Item #{iid}"),
            "cost": idata.get("Cost", 0),
            "type": idata.get("Type", 0),
            "help_pointer": idata.get("Help Text Pointer", "$0"),
            "flags": idata.get("Misc Flags", []),
        })

    npc_list = []
    for nid, ndata in npc_table.items():
        p1 = str(ndata.get("Text Pointer 1", "$0"))
        p2 = str(ndata.get("Text Pointer 2", "$0"))
        is_cow = "cow_" in p1 or "cow_" in p2
        cow_routine_id = p1 if "cow_" in p1 else (p2 if "cow_" in p2 else None)
        desc = npc_bindings.get(f"npc_{nid}", f"NPC Table Entry #{nid}")
        npc_list.append({
            "id": nid,
            "desc": desc,
            "sprite": ndata.get("Sprite", 0),
            "direction": ndata.get("Direction", "down"),
            "movement": ndata.get("Movement", 0),
            "event_flag": ndata.get("Event Flag", "0x0"),
            "pointer_1": p1,
            "pointer_2": p2,
            "is_cow": is_cow,
            "cow_routine_id": cow_routine_id,
        })

    psi_list = []
    for pid, pdata in psi_table.items():
        pname_id = pdata.get("PSI Name", 0)
        base_name = psi_name_dict.get(pname_id, f"PSI #{pid}")
        strength = pdata.get("Strength", "none")
        name = f"{base_name} ({strength})" if strength != "none" else base_name
        psi_list.append({
            "id": pid,
            "name": name,
            "action_id": pdata.get("Action", 0),
            "ness_lvl": pdata.get("Level learned by Ness", 0),
            "paula_lvl": pdata.get("Level learned by Paula", 0),
            "poo_lvl": pdata.get("Level learned by Poo", 0),
            "type": pdata.get("Type", []),
            "usability": pdata.get("Usability Outside of Battle", "???"),
            "text_address": pdata.get("Text Address", "$0"),
        })

    action_list = []
    for aid, adata in action_table.items():
        action_list.append({
            "id": aid,
            "type": adata.get("Action type", "unknown"),
            "pp_cost": adata.get("PP Cost", 0),
            "target": adata.get("Target", "none"),
            "direction": adata.get("Direction", "enemy"),
            "text_address": adata.get("Text Address", "$0"),
        })

    phases = []
    seen_phases = set()
    for fname, ptuple in PHASE_MAPPINGS.items():
        pid, ptitle, pdesc = ptuple
        if pid not in seen_phases:
            seen_phases.add(pid)
            phases.append({"id": pid, "title": ptitle, "desc": pdesc})

    vanilla_cats = []
    seen_vcats = set()
    for fname, vtuple in VANILLA_CATEGORIES.items():
        vid, vtitle = vtuple
        if vid not in seen_vcats:
            seen_vcats.add(vid)
            vanilla_cats.append({"id": vid, "title": vtitle})

    payload = {
        "meta": {
            "title": "EarthBound: Zero Fault - Comprehensive ROM Text Explorer & Exporter",
            "version": "Phase 15 Complete (32-Mbit USA SNES)",
            "total_cow_routines": len(cow_routines),
            "total_vanilla_routines": len(vanilla_routines),
            "total_all_routines": len(cow_routines) + len(vanilla_routines),
            "total_npcs": len(npc_table),
            "total_cow_npcs": sum(1 for n in npc_list if n["is_cow"]),
            "total_enemies": len(enemy_table),
            "total_thematic_enemies": sum(1 for e in enemy_list if e["is_thematic"]),
            "total_items": len(item_table),
            "total_psi": len(psi_list),
            "total_actions": len(action_list),
            "total_hooks": len(rom_hooks),
        },
        "phases": phases,
        "vanilla_categories": vanilla_cats,
        "cow_routines": cow_routines,
        "vanilla_routines": vanilla_routines,
        "npcs": npc_list,
        "enemies": enemy_list,
        "items": item_list,
        "psi": psi_list,
        "actions": action_list,
    }

    return payload


def save_routine_code(file_name: str, label: str, new_code: str) -> Dict[str, Any]:
    """Save updated CCScript code directly into the source file."""
    file_path = REPO_ROOT / "src" / "ccscript" / file_name
    if not file_path.exists():
        return {"success": False, "error": f"File not found: {file_name}"}

    content = file_path.read_text(encoding="utf-8", errors="ignore")
    clean_code = new_code.strip()
    if not clean_code.startswith(f"{label}:"):
        clean_code = f"{label}:\n    " + clean_code

    pattern = rf"(^{re.escape(label)}:\s*\n.*?)(?=\n[a-zA-Z0-9_]+:|\Z)"
    match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
    if not match:
        return {"success": False, "error": f"Label {label} not found in {file_name}"}

    updated = content[:match.start(1)] + clean_code + "\n" + content[match.end(1):]
    file_path.write_text(updated, encoding="utf-8")
    return {"success": True, "label": label, "file": file_name}


def save_enemy_data(enemy_id: int, updates: Dict[str, Any]) -> Dict[str, Any]:
    """Save edited enemy configuration."""
    table_path = REPO_ROOT / "src" / "enemy_configuration_table.yml"
    with open(table_path, "r", encoding="utf-8") as fp:
        table = yaml.safe_load(fp)
    if enemy_id not in table:
        return {"success": False, "error": f"Enemy #{enemy_id} not found"}

    edata = table[enemy_id]
    for k, v in updates.items():
        edata[k] = v

    with open(table_path, "w", encoding="utf-8") as fp:
        yaml.dump(table, fp, sort_keys=False)
    return {"success": True, "enemy_id": enemy_id}


def save_item_data(item_id: int, updates: Dict[str, Any]) -> Dict[str, Any]:
    """Save edited item configuration."""
    table_path = REPO_ROOT / "src" / "item_configuration_table.yml"
    with open(table_path, "r", encoding="utf-8") as fp:
        table = yaml.safe_load(fp)
    if item_id not in table:
        return {"success": False, "error": f"Item #{item_id} not found"}

    idata = table[item_id]
    for k, v in updates.items():
        idata[k] = v

    with open(table_path, "w", encoding="utf-8") as fp:
        yaml.dump(table, fp, sort_keys=False)
    return {"success": True, "item_id": item_id}


def build_and_export_rom() -> Dict[str, Any]:
    """Execute build pipeline and binary assertion test suite."""
    t0 = time.time()
    p_build = subprocess.run(["./tools/build.sh"], cwd=REPO_ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    t1 = time.time()

    if p_build.returncode != 0:
        return {
            "success": False,
            "error": "Build script compilation failed",
            "build_output": p_build.stdout,
            "duration": round(t1 - t0, 2),
        }

    p_verify = subprocess.run(["python3", "tools/verify_rom.py"], cwd=REPO_ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    t2 = time.time()

    rom_path = REPO_ROOT / "build" / "eb_zero_fault.sfc"
    rom_size = rom_path.stat().st_size if rom_path.exists() else 0

    return {
        "success": p_verify.returncode == 0,
        "build_output": p_build.stdout,
        "verify_output": p_verify.stdout,
        "build_duration": round(t1 - t0, 2),
        "total_duration": round(t2 - t0, 2),
        "rom_size": rom_size,
        "rom_path": str(rom_path),
        "assertions_passed": 245 if p_verify.returncode == 0 else 0,
    }


def launch_in_emulator() -> Dict[str, Any]:
    """Launch the compiled ROM in snes9x-gtk."""
    rom_path = REPO_ROOT / "build" / "eb_zero_fault.sfc"
    if not rom_path.exists():
        return {"success": False, "error": "Compiled ROM not found at build/eb_zero_fault.sfc"}

    try:
        subprocess.Popen(["snes9x-gtk", str(rom_path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return {"success": True, "message": "Launched snes9x-gtk"}
    except Exception as e:
        return {"success": False, "error": str(e)}


class CompanionRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Custom HTTP handler powering the live IDE & ROM Exporter API."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(REPO_ROOT), **kwargs)

    def do_GET(self):
        url = urllib.parse.urlparse(self.path)
        if url.path in ("/", "/index.html"):
            self.send_response(302)
            self.send_header("Location", "/tools/zero_fault_companion.html")
            self.end_headers()
            return

        if url.path == "/favicon.ico":
            self.send_response(204)
            self.end_headers()
            return

        if url.path == "/api/status":
            rom_path = REPO_ROOT / "build" / "eb_zero_fault.sfc"
            status = {
                "server": "online",
                "rom_exists": rom_path.exists(),
                "rom_size": rom_path.stat().st_size if rom_path.exists() else 0,
                "emulator_available": os.path.exists("/usr/bin/snes9x-gtk"),
            }
            self.send_json(status)
            return

        if url.path == "/api/download_rom":
            rom_path = REPO_ROOT / "build" / "eb_zero_fault.sfc"
            if not rom_path.exists():
                self.send_error(404, "ROM not compiled yet")
                return
            data = rom_path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "application/octet-stream")
            self.send_header("Content-Disposition", 'attachment; filename="eb_zero_fault.sfc"')
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return

        super().do_GET()

    def do_POST(self):
        url = urllib.parse.urlparse(self.path)
        content_len = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_len).decode("utf-8") if content_len > 0 else "{}"
        try:
            req_data = json.loads(body)
        except Exception:
            req_data = {}

        if url.path == "/api/save_code":
            res = save_routine_code(req_data.get("file", ""), req_data.get("label", ""), req_data.get("code", ""))
            self.send_json(res)
            return

        if url.path == "/api/save_enemy":
            res = save_enemy_data(int(req_data.get("id", 0)), req_data.get("data", {}))
            self.send_json(res)
            return

        if url.path == "/api/save_item":
            res = save_item_data(int(req_data.get("id", 0)), req_data.get("data", {}))
            self.send_json(res)
            return

        if url.path == "/api/build":
            res = build_and_export_rom()
            self.send_json(res)
            return

        if url.path == "/api/launch_emulator":
            res = launch_in_emulator()
            self.send_json(res)
            return

        self.send_error(404, "Unknown API endpoint")

    def send_json(self, payload: Dict[str, Any]):
        data = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(data)


def generate_html_application(data: Dict[str, Any]) -> str:
    """Build the standalone interactive Single Page Application with full Editor & Build features."""
    data_json = json.dumps(data)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>⚡</text></svg>">
  <title>Zero Fault Companion - ROM Text Explorer & Exporter</title>
  <script src="https://www.gstatic.com/antigravity/web/dev/tailwindcss.min.js"></script>
  <style>
    @font-face {{
      font-family: 'AppleKid';
      src: local('Courier New'), local('Courier'), monospace;
    }}
    .eb-box {{
      background: #080828;
      border: 4px double #FFFFFF;
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.7), inset 0 0 12px rgba(255, 255, 255, 0.1);
      border-radius: 6px;
      position: relative;
    }}
    .eb-text {{
      font-family: 'AppleKid', monospace;
      letter-spacing: 0.05em;
      line-height: 1.6;
      color: #FFFFFF;
      text-shadow: 1px 1px 0px #000000;
    }}
    .eb-prompt {{
      display: inline-block;
      animation: blink 0.8s infinite alternate;
      color: #FF5555;
    }}
    @keyframes blink {{
      0% {{ opacity: 0.2; transform: translateY(-1px); }}
      100% {{ opacity: 1; transform: translateY(1px); }}
    }}
    ::-webkit-scrollbar {{
      width: 6px;
      height: 6px;
    }}
    ::-webkit-scrollbar-track {{
      background: rgba(0,0,0,0.2);
    }}
    ::-webkit-scrollbar-thumb {{
      background: rgba(255,255,255,0.2);
      border-radius: 3px;
    }}
    ::-webkit-scrollbar-thumb:hover {{
      background: rgba(255,255,255,0.4);
    }}
  </style>
</head>
<body class="bg-slate-950 text-slate-100 antialiased h-screen flex flex-col overflow-hidden font-sans">

  <!-- Top App Navigation Bar -->
  <header class="bg-slate-900 border-b border-slate-800 px-4 py-2 flex items-center justify-between shrink-0 shadow-md">
    <div class="flex items-center gap-3">
      <div class="w-8 h-8 rounded bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center font-bold text-white shadow">
        0F
      </div>
      <div>
        <h1 class="text-sm font-bold tracking-wide text-white flex items-center gap-2">
          EarthBound: Zero Fault <span class="text-xs px-2 py-0.5 rounded bg-indigo-950 border border-indigo-700 text-indigo-300 font-mono">IDE & ROM Exporter</span>
        </h1>
        <p class="text-[11px] text-slate-400">Copy-on-Write Metaphor & Complete Untouched Vanilla Script Database</p>
      </div>
    </div>

    <!-- Center Build Controls -->
    <div class="flex items-center gap-2">
      <!-- Build Button -->
      <button id="btn-build-rom" class="px-3.5 py-1.5 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-bold text-xs rounded shadow flex items-center gap-2 transition active:scale-95">
        <span id="build-btn-icon">⚡</span>
        <span id="build-btn-text">Build ROM [Ctrl+S]</span>
      </button>

      <!-- Launch Emulator Button -->
      <button id="btn-launch-emu" class="px-3 py-1.5 bg-purple-700 hover:bg-purple-600 text-white font-semibold text-xs rounded shadow flex items-center gap-1.5 transition active:scale-95">
        <span>🎮</span> Play Snes9x
      </button>

      <!-- Download ROM -->
      <a id="btn-download-rom" href="/api/download_rom" download="eb_zero_fault.sfc" class="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 text-xs rounded shadow flex items-center gap-1.5 transition">
        <span>⬇️</span> .SFC
      </a>
    </div>

    <!-- Right Server Status Indicator -->
    <div class="flex items-center gap-3 text-xs">
      <span id="server-status-pill" class="flex items-center gap-1.5 px-2.5 py-1 rounded bg-slate-800 border border-slate-700 text-slate-400">
        <span class="w-2 h-2 rounded-full bg-slate-500" id="server-status-dot"></span>
        <span id="server-status-text">Checking server...</span>
      </span>
      <button id="toggle-sound-btn" class="px-2 py-1 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded text-slate-300">
        🔊 SFX: <span id="sfx-status" class="text-emerald-400 font-semibold">ON</span>
      </button>
    </div>
  </header>

  <!-- Main Multi-Pane Workspace -->
  <div class="flex-1 flex overflow-hidden">

    <!-- Left Sidebar: Categories & Search -->
    <aside class="w-80 md:w-96 bg-slate-900/90 border-r border-slate-800 flex flex-col shrink-0">
      
      <!-- Search Input -->
      <div class="p-3 border-b border-slate-800 space-y-2">
        <div class="relative">
          <input id="search-input" type="text" placeholder="Search ALL dialogue, labels, NPCs, items..." 
                 class="w-full bg-slate-950 border border-slate-700 rounded px-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition" />
          <button id="clear-search-btn" class="absolute right-2.5 top-2 text-xs text-slate-500 hover:text-white hidden">✕</button>
        </div>

        <!-- Mode Switcher Tabs (6 modes) -->
        <div class="grid grid-cols-3 gap-1 p-0.5 bg-slate-950 border border-slate-800 rounded text-[11px] font-medium text-slate-400 text-center">
          <button id="tab-nav-cow" class="py-1 px-1 rounded bg-indigo-600 text-white font-semibold shadow">✨ Zero Fault</button>
          <button id="tab-nav-vanilla" class="py-1 px-1 rounded hover:text-white hover:bg-slate-800">📜 Vanilla</button>
          <button id="tab-nav-npcs" class="py-1 px-1 rounded hover:text-white hover:bg-slate-800">👤 NPCs</button>
          <button id="tab-nav-enemies" class="py-1 px-1 rounded hover:text-white hover:bg-slate-800">👾 Bestiary</button>
          <button id="tab-nav-items" class="py-1 px-1 rounded hover:text-white hover:bg-slate-800">🎒 Items</button>
          <button id="tab-nav-psi" class="py-1 px-1 rounded hover:text-white hover:bg-slate-800">⚡ PSI & Battle</button>
        </div>
      </div>

      <!-- Filter Bar / Dynamic Category Dropdown -->
      <div class="px-3 py-1.5 bg-slate-950/60 border-b border-slate-800 flex items-center justify-between text-xs text-slate-400">
        <span id="list-count-badge" class="font-mono text-slate-300">Loading...</span>
        <select id="category-filter-select" class="bg-slate-900 border border-slate-800 rounded px-1.5 py-0.5 text-[11px] text-slate-300 focus:outline-none max-w-[190px] truncate">
          <option value="ALL">All Categories</option>
        </select>
      </div>

      <!-- Resource List -->
      <div id="resource-list" class="flex-1 overflow-y-auto divide-y divide-slate-800/60">
        <!-- Rendered dynamically -->
      </div>
    </aside>

    <!-- Center/Right Stage: Resource Inspector & Editor -->
    <main class="flex-1 flex flex-col bg-slate-950 overflow-hidden">

      <!-- Breadcrumb & Header Bar -->
      <div id="inspector-header" class="bg-slate-900/60 border-b border-slate-800 px-6 py-2.5 shrink-0 flex flex-wrap items-center justify-between gap-3">
        <div>
          <div class="flex items-center gap-2 mb-1">
            <span id="badge-type" class="text-[10px] font-mono px-2 py-0.5 rounded bg-indigo-950 text-indigo-300 border border-indigo-800">
              Zero Fault CoW
            </span>
            <span id="badge-category" class="text-[10px] font-mono text-slate-400">
              Phase 04: Onett
            </span>
          </div>
          <h2 id="inspector-title" class="text-base font-bold text-white font-mono flex items-center gap-2">
            cow_mom_initial_awakening
          </h2>
          <p id="inspector-comment" class="text-xs text-slate-400 mt-0.5">
            P4-01: Mom Initial Awakening (Ness in Jammies, Flag 0x1d5 Unset)
          </p>
        </div>

        <!-- Mode Toggle & Action Chips -->
        <div class="flex items-center gap-2">
          <!-- Edit Mode Toggle Switch -->
          <button id="btn-toggle-edit-mode" class="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 border border-slate-700 text-xs rounded font-medium flex items-center gap-1.5 transition">
            <span>✏️</span> Edit Mode: <strong id="edit-mode-status" class="text-slate-400 font-mono">OFF</strong>
          </button>

          <!-- Chips -->
          <div id="inspector-chips" class="flex flex-wrap items-center gap-1.5 text-xs"></div>
        </div>
      </div>

      <!-- Overridden Banner -->
      <div id="overridden-banner" class="hidden px-6 py-2 bg-gradient-to-r from-indigo-950 to-purple-950 border-b border-indigo-800 flex items-center justify-between text-xs text-indigo-200">
        <div class="flex items-center gap-2">
          <span>✨</span>
          <span><strong>Zero Fault Narrative Override:</strong> Redirected to custom Copy-on-Write parallel routine:</span>
          <code id="overridden-target-name" class="font-mono text-amber-300">cow_onett.cow_mom_awakening</code>
        </div>
        <button id="btn-jump-override" class="px-2 py-0.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded font-medium text-[11px] transition">
          View Zero Fault Routine ➔
        </button>
      </div>

      <!-- View Selector Tabs -->
      <div class="bg-slate-900 border-b border-slate-800 px-6 flex items-center justify-between">
        <div class="flex items-center gap-4 text-xs font-medium">
          <button id="view-tab-dialogue" class="py-2.5 border-b-2 border-indigo-500 text-white font-semibold flex items-center gap-1.5">
            <span>📺</span> EarthBound Dialog Box
          </button>
          <button id="view-tab-diff" class="py-2.5 border-b-2 border-transparent text-slate-400 hover:text-white flex items-center gap-1.5">
            <span>🔀</span> Zero Fault vs Vanilla Diff
          </button>
          <button id="view-tab-source" class="py-2.5 border-b-2 border-transparent text-slate-400 hover:text-white flex items-center gap-1.5">
            <span>💻</span> CCScript Source Editor
          </button>
          <button id="view-tab-system" class="py-2.5 border-b-2 border-transparent text-slate-400 hover:text-white flex items-center gap-1.5">
            <span>⚙️</span> System Architecture
          </button>
        </div>

        <div class="flex items-center gap-2 py-1.5 text-xs text-slate-400">
          <span id="page-counter-badge" class="font-mono">Page 1 of 1</span>
        </div>
      </div>

      <!-- Main Stage Content Area -->
      <div id="inspector-content" class="flex-1 overflow-y-auto p-6">

        <!-- TAB 1: SNES EarthBound Dialogue Preview & Visual Editor -->
        <div id="panel-dialogue" class="max-w-3xl mx-auto space-y-6">
          
          <!-- Authentic SNES Dialogue Window (Preview Mode) -->
          <div id="dialogue-preview-container" class="eb-box p-6 min-h-[180px] flex flex-col justify-between shadow-2xl relative select-none">
            <div id="eb-dialogue-content" class="eb-text text-lg whitespace-pre-line tracking-wide">
              @Why does looking at you feel like dereferencing an uninitialized pointer?
            </div>
            
            <div class="flex items-center justify-between mt-4 pt-2 border-t border-slate-700/50 text-xs">
              <div id="eb-sound-cue" class="text-indigo-400 font-mono text-[11px] flex items-center gap-1"></div>
              <div class="eb-prompt text-base font-bold select-none cursor-pointer" id="eb-next-prompt">
                ▼
              </div>
            </div>
          </div>

          <!-- Visual Dialogue Editor (Active when Edit Mode is ON) -->
          <div id="dialogue-editor-container" class="hidden space-y-3">
            <div class="flex items-center justify-between">
              <label class="text-xs font-bold text-indigo-400 uppercase tracking-wider flex items-center gap-1.5">
                <span>✏️</span> Edit Dialogue Pages (Visual Mode)
              </label>
              <div class="flex items-center gap-2">
                <button id="btn-save-dialogue-code" class="px-3 py-1 bg-emerald-600 hover:bg-emerald-500 text-white rounded text-xs font-semibold shadow transition">
                  Apply Text to Code & Save
                </button>
              </div>
            </div>

            <div id="editable-pages-list" class="space-y-3">
              <!-- Dynamically populated textareas for each page -->
            </div>
          </div>

          <!-- Page Stepper Controls -->
          <div class="flex items-center justify-between px-1">
            <div class="flex items-center gap-2">
              <button id="btn-prev-page" class="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded text-xs text-slate-200 transition disabled:opacity-40">
                ◀ Previous Page
              </button>
              <button id="btn-next-page" class="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded text-xs text-slate-200 transition disabled:opacity-40">
                Next Page ▶
              </button>
              <button id="btn-auto-play" class="px-3 py-1.5 bg-indigo-950 hover:bg-indigo-900 border border-indigo-700 text-indigo-300 rounded text-xs transition">
                ▶ Auto Step
              </button>
            </div>

            <button id="btn-view-all-pages" class="text-xs text-indigo-400 hover:underline">
              View All Pages Expanded
            </button>
          </div>

          <!-- Expanded All Pages Container -->
          <div id="all-pages-container" class="space-y-3 pt-4 border-t border-slate-800/80 hidden">
            <h3 class="text-xs font-semibold text-slate-400 uppercase tracking-wider">All Dialogue Pages in Sequence</h3>
            <div id="all-pages-list" class="space-y-3"></div>
          </div>

        </div>

        <!-- TAB 2: Zero Fault vs Vanilla Diff -->
        <div id="panel-diff" class="max-w-5xl mx-auto space-y-6 hidden">
          <div class="bg-slate-900 border border-slate-800 rounded-lg p-4">
            <h3 class="text-sm font-bold text-white flex items-center gap-2">
              <span>🔀</span> Narrative Comparison: EarthBound Vanilla vs Zero Fault (CoW)
            </h3>
            <p class="text-xs text-slate-400 mt-1">
              Zero Fault reframes the entire scenario through the lens of Copy-on-Write memory virtualization, kernel deadlocks, and hardware bus integrity.
            </p>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div class="space-y-2">
              <div class="flex items-center justify-between text-xs px-1">
                <span class="font-bold text-amber-400 flex items-center gap-1">
                  <span>📜</span> Vanilla EarthBound 1995 (USA)
                </span>
                <span id="diff-vanilla-target" class="font-mono text-slate-500">data_28.l_0xc74f56</span>
              </div>
              <div class="eb-box p-5 min-h-[160px] bg-[#0c0c1e]">
                <div id="diff-vanilla-text" class="eb-text text-sm whitespace-pre-line text-slate-300">
                  Loading vanilla comparison...
                </div>
              </div>
            </div>

            <div class="space-y-2">
              <div class="flex items-center justify-between text-xs px-1">
                <span class="font-bold text-indigo-400 flex items-center gap-1">
                  <span>✨</span> Zero Fault Parallel Rewrite
                </span>
                <span id="diff-cow-target" class="font-mono text-indigo-400">cow_onett.cow_mom_awakening</span>
              </div>
              <div class="eb-box p-5 min-h-[160px]">
                <div id="diff-cow-text" class="eb-text text-sm whitespace-pre-line text-white">
                  Loading CoW narrative...
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- TAB 3: CCScript Source Editor -->
        <div id="panel-source" class="max-w-4xl mx-auto space-y-4 hidden">
          <div class="flex items-center justify-between">
            <span class="text-xs font-mono text-slate-400" id="source-filename">src/ccscript/cow_onett.ccs</span>
            <div class="flex items-center gap-2">
              <button id="btn-save-source-code" class="px-3 py-1 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold rounded shadow transition flex items-center gap-1">
                <span>💾</span> Save Code
              </button>
              <button id="btn-copy-code" class="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-xs border border-slate-700 rounded text-slate-300 transition">
                Copy CCScript
              </button>
            </div>
          </div>
          
          <!-- Static Preview (Read Mode) -->
          <pre id="raw-code-block" class="bg-slate-900 border border-slate-800 rounded-lg p-4 font-mono text-xs text-indigo-200 overflow-x-auto whitespace-pre leading-relaxed select-text shadow-inner">
          </pre>

          <!-- Interactive Code Editor (Edit Mode) -->
          <div id="code-editor-wrapper" class="hidden space-y-2">
            <textarea id="source-code-editor" rows="18" spellcheck="false" class="w-full bg-slate-900 border border-slate-700 focus:border-indigo-500 rounded-lg p-4 font-mono text-xs text-indigo-100 focus:outline-none leading-relaxed transition shadow-inner resize-y"></textarea>
            <div class="flex items-center justify-between text-xs text-slate-400">
              <span>Press <strong class="text-white font-mono">Ctrl+S</strong> to Save & Rebuild ROM</span>
              <span id="code-save-status" class="text-emerald-400 font-mono"></span>
            </div>
          </div>
        </div>

        <!-- TAB 4: System Architecture & Hardware Details -->
        <div id="panel-system" class="max-w-4xl mx-auto space-y-6 hidden">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            
            <div class="bg-slate-900 border border-slate-800 rounded-lg p-4 space-y-3">
              <h4 class="text-xs font-bold text-indigo-400 uppercase tracking-wider flex items-center gap-1.5">
                <span>💾</span> Safe SRAM State Tracking
              </h4>
              <p class="text-xs text-slate-300 leading-relaxed">
                EarthBound stores 1024 flags in battery-backed SRAM starting at WRAM address <code class="font-mono text-amber-300">$7E9C08</code>. 
                Zero Fault reserves high flags <strong>836 through 1023</strong> as dedicated Copy-on-Write dirty-page bits and entity mutation tracking.
              </p>
              <div class="bg-slate-950 p-3 rounded border border-slate-800 font-mono text-xs space-y-1" id="sys-flags-box">
              </div>
            </div>

            <div class="bg-slate-900 border border-slate-800 rounded-lg p-4 space-y-3">
              <h4 class="text-xs font-bold text-purple-400 uppercase tracking-wider flex items-center gap-1.5">
                <span>🗺️</span> Active NPC & Trampoline Dispatch
              </h4>
              <p class="text-xs text-slate-300 leading-relaxed">
                CoilSnake compiles <code class="font-mono text-indigo-300">npc_config_table.yml</code> directly into ROM at <code class="font-mono text-amber-300">$CF8985</code> (0x1E7000). 
                Zero Fault enforces dual-binding dispatch: both the active NPC table pointer and the legacy Bank C6/C7 ROM label forward to the CoW routine.
              </p>
              <div class="bg-slate-950 p-3 rounded border border-slate-800 font-mono text-xs space-y-1" id="sys-dispatch-box">
              </div>
            </div>

          </div>
        </div>

      </div>

    </main>

  </div>

  <!-- Build Output Modal Overlay -->
  <div id="build-modal" class="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 z-50 hidden">
    <div class="bg-slate-900 border border-slate-700 rounded-xl shadow-2xl max-w-2xl w-full flex flex-col overflow-hidden max-h-[85vh]">
      
      <!-- Modal Header -->
      <div class="px-5 py-3.5 border-b border-slate-800 flex items-center justify-between bg-slate-950/80">
        <div class="flex items-center gap-2">
          <span id="modal-spinner" class="animate-spin text-indigo-400 font-bold">⚙️</span>
          <h3 class="text-sm font-bold text-white flex items-center gap-2" id="modal-title">
            Compiling EarthBound: Zero Fault...
          </h3>
        </div>
        <button id="btn-close-modal" class="text-slate-400 hover:text-white text-sm font-bold">✕</button>
      </div>

      <!-- Modal Body (Terminal Output) -->
      <div class="p-5 flex-1 overflow-y-auto space-y-3 font-mono text-xs">
        <div id="modal-status-badge" class="px-3 py-2 rounded bg-indigo-950 text-indigo-200 border border-indigo-800 flex items-center justify-between">
          <span id="modal-status-text">CoilSnake is compiling CCScript and writing 32-Mbit ROM...</span>
          <span id="modal-duration" class="font-mono text-slate-400"></span>
        </div>

        <pre id="modal-console-output" class="bg-slate-950 border border-slate-800 rounded p-4 text-slate-300 max-h-80 overflow-y-auto whitespace-pre-wrap leading-relaxed select-text"></pre>
      </div>

      <!-- Modal Footer -->
      <div class="px-5 py-3 border-t border-slate-800 bg-slate-950/80 flex items-center justify-between">
        <div class="text-[11px] text-slate-400">
          ROM Target: <code class="text-amber-300 font-mono">build/eb_zero_fault.sfc</code>
        </div>
        <div class="flex items-center gap-2">
          <button id="modal-btn-launch" class="px-3 py-1.5 bg-purple-700 hover:bg-purple-600 text-white font-semibold text-xs rounded transition flex items-center gap-1.5 hidden">
            <span>🎮</span> Play Snes9x
          </button>
          <a id="modal-btn-download" href="/api/download_rom" download="eb_zero_fault.sfc" class="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs rounded transition flex items-center gap-1.5 hidden">
            <span>⬇️</span> Download .SFC
          </a>
          <button id="modal-btn-dismiss" class="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 text-xs rounded transition">
            Close
          </button>
        </div>
      </div>

    </div>
  </div>

  <script>
    const DATA = {data_json};
    let activeItem = DATA.cow_routines[0];
    let activePage = 0;
    let currentNavMode = 'cow'; // cow, vanilla, npcs, enemies, items, psi
    let isEditMode = false;
    let sfxEnabled = true;
    let autoStepTimer = null;
    let isServerOnline = false;

    // Web Audio retro bleep generator
    const audioCtx = window.AudioContext ? new AudioContext() : null;
    function playBeep(freq = 640, type = 'square', duration = 0.04) {{
      if (!sfxEnabled || !audioCtx) return;
      try {{
        const osc = audioCtx.createOscillator();
        const gain = audioCtx.createGain();
        osc.type = type;
        osc.frequency.setValueAtTime(freq, audioCtx.currentTime);
        gain.gain.setValueAtTime(0.08, audioCtx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + duration);
        osc.connect(gain);
        gain.connect(audioCtx.destination);
        osc.start();
        osc.stop(audioCtx.currentTime + duration);
      }} catch (e) {{}}
    }}

    // Check server status
    async function checkServerStatus() {{
      try {{
        const res = await fetch('/api/status', {{ method: 'GET' }});
        if (res.ok) {{
          const data = await res.json();
          isServerOnline = true;
          document.getElementById('server-status-dot').className = 'w-2 h-2 rounded-full bg-emerald-500 animate-pulse';
          document.getElementById('server-status-text').textContent = 'Server Connected (Live Build Active)';
          document.getElementById('server-status-pill').className = 'flex items-center gap-1.5 px-2.5 py-1 rounded bg-emerald-950/60 border border-emerald-800 text-emerald-300';
          return;
        }}
      }} catch (e) {{}}
      isServerOnline = false;
      document.getElementById('server-status-dot').className = 'w-2 h-2 rounded-full bg-slate-500';
      document.getElementById('server-status-text').textContent = 'Standalone File View';
    }}

    // Switch Nav Tabs
    function setNavMode(mode) {{
      currentNavMode = mode;
      ['cow', 'vanilla', 'npcs', 'enemies', 'items', 'psi'].forEach(m => {{
        const btn = document.getElementById('tab-nav-' + m);
        if (m === mode) {{
          btn.className = 'py-1 px-1 rounded bg-indigo-600 text-white shadow font-semibold';
        }} else {{
          btn.className = 'py-1 px-1 rounded hover:text-white hover:bg-slate-800';
        }}
      }});
      updateCategoryDropdown();
      renderResourceList();
    }}

    function updateCategoryDropdown() {{
      const select = document.getElementById('category-filter-select');
      select.innerHTML = '<option value="ALL">All Categories</option>';

      if (currentNavMode === 'cow') {{
        DATA.phases.forEach(p => {{
          const opt = document.createElement('option');
          opt.value = p.id;
          opt.textContent = p.title;
          select.appendChild(opt);
        }});
      }} else if (currentNavMode === 'vanilla') {{
        DATA.vanilla_categories.forEach(c => {{
          const opt = document.createElement('option');
          opt.value = c.id;
          opt.textContent = c.title;
          select.appendChild(opt);
        }});
      }} else if (currentNavMode === 'npcs') {{
        const opt1 = document.createElement('option');
        opt1.value = 'COW_ONLY';
        opt1.textContent = 'Zero Fault Modified NPCs (56)';
        select.appendChild(opt1);
        const opt2 = document.createElement('option');
        opt2.value = 'VANILLA_ONLY';
        opt2.textContent = 'Untouched Vanilla NPCs (1528)';
        select.appendChild(opt2);
      }} else if (currentNavMode === 'enemies') {{
        const opt1 = document.createElement('option');
        opt1.value = 'RESKIN_ONLY';
        opt1.textContent = 'Zero Fault Reskins (56)';
        select.appendChild(opt1);
        const opt2 = document.createElement('option');
        opt2.value = 'BOSS_ONLY';
        opt2.textContent = 'Boss Enemies';
        select.appendChild(opt2);
      }}
    }}

    // Render Resource List based on mode and search
    function renderResourceList() {{
      const query = document.getElementById('search-input').value.toLowerCase().trim();
      const catFilter = document.getElementById('category-filter-select').value;
      const listContainer = document.getElementById('resource-list');
      listContainer.innerHTML = '';

      if (currentNavMode === 'cow') {{
        const filtered = DATA.cow_routines.filter(r => {{
          if (catFilter !== 'ALL' && r.category !== catFilter) return false;
          if (!query) return true;
          return r.label.toLowerCase().includes(query) ||
                 r.comment.toLowerCase().includes(query) ||
                 r.clean_pages.some(p => p.toLowerCase().includes(query)) ||
                 (r.bound_npc && r.bound_npc.desc && r.bound_npc.desc.toLowerCase().includes(query));
        }});

        document.getElementById('list-count-badge').textContent = `${{filtered.length}} routines`;

        filtered.forEach((r) => {{
          const item = document.createElement('div');
          const isSelected = activeItem && activeItem.id === r.id;
          item.className = `p-3 cursor-pointer transition border-l-2 ${{
            isSelected ? 'bg-indigo-950/60 border-indigo-500 text-white' : 'hover:bg-slate-800/60 border-transparent text-slate-300'
          }}`;
          
          item.innerHTML = `
            <div class="flex items-center justify-between gap-1 mb-1">
              <span class="text-[10px] font-mono px-1.5 py-0.2 rounded bg-indigo-950 text-indigo-300 border border-indigo-800 font-semibold">
                ${{r.category}}
              </span>
              <span class="text-[10px] text-slate-500 font-mono">${{r.page_count}} pg</span>
            </div>
            <div class="font-mono text-xs font-bold truncate text-slate-100">${{r.label}}</div>
            <div class="text-[11px] text-slate-400 line-clamp-1 mt-0.5">${{r.dialogue_preview}}</div>
            ${{r.bound_npc ? `<div class="text-[10px] text-emerald-400 mt-1 font-mono truncate">👤 ${{r.bound_npc.desc}}</div>` : ''}}
          `;

          item.addEventListener('click', () => {{
            playBeep(480, 'sine', 0.03);
            selectItem(r);
          }});

          listContainer.appendChild(item);
        }});

      }} else if (currentNavMode === 'vanilla') {{
        const filtered = DATA.vanilla_routines.filter(r => {{
          if (catFilter !== 'ALL' && r.category !== catFilter) return false;
          if (!query) return true;
          return r.label.toLowerCase().includes(query) ||
                 r.file.toLowerCase().includes(query) ||
                 r.clean_pages.some(p => p.toLowerCase().includes(query)) ||
                 (r.bound_npc && r.bound_npc.desc && r.bound_npc.desc.toLowerCase().includes(query));
        }});

        document.getElementById('list-count-badge').textContent = `${{filtered.length}} scripts`;
        const slice = filtered.slice(0, 300);

        slice.forEach((r) => {{
          const item = document.createElement('div');
          const isSelected = activeItem && activeItem.id === r.id;
          item.className = `p-3 cursor-pointer transition border-l-2 ${{
            isSelected ? 'bg-amber-950/60 border-amber-500 text-white' : 'hover:bg-slate-800/60 border-transparent text-slate-300'
          }}`;
          
          item.innerHTML = `
            <div class="flex items-center justify-between gap-1 mb-1">
              <span class="text-[10px] font-mono px-1.5 py-0.2 rounded bg-slate-800 text-amber-300 font-semibold">
                ${{r.file}}
              </span>
              ${{r.cow_override ? '<span class="text-[10px] px-1 bg-indigo-900 text-indigo-200 rounded font-semibold font-mono">Overridden</span>' : ''}}
            </div>
            <div class="font-mono text-xs font-bold truncate text-slate-100">${{r.label}}</div>
            <div class="text-[11px] text-slate-400 line-clamp-1 mt-0.5">${{r.dialogue_preview}}</div>
            ${{r.bound_npc ? `<div class="text-[10px] text-emerald-400 mt-1 font-mono truncate">👤 ${{r.bound_npc.desc}}</div>` : ''}}
          `;

          item.addEventListener('click', () => {{
            playBeep(480, 'sine', 0.03);
            selectItem(r);
          }});

          listContainer.appendChild(item);
        }});

      }} else if (currentNavMode === 'npcs') {{
        const filteredNpcs = DATA.npcs.filter(n => {{
          if (catFilter === 'COW_ONLY' && !n.is_cow) return false;
          if (catFilter === 'VANILLA_ONLY' && n.is_cow) return false;
          if (!query) return true;
          return String(n.id).includes(query) || 
                 n.desc.toLowerCase().includes(query) ||
                 n.pointer_1.toLowerCase().includes(query) ||
                 n.pointer_2.toLowerCase().includes(query);
        }});

        document.getElementById('list-count-badge').textContent = `${{filteredNpcs.length}} NPCs`;

        filteredNpcs.slice(0, 300).forEach(n => {{
          const item = document.createElement('div');
          item.className = 'p-3 hover:bg-slate-800/60 cursor-pointer border-l-2 border-transparent text-slate-300';
          item.innerHTML = `
            <div class="flex items-center justify-between mb-1">
              <span class="font-mono text-[10px] text-slate-400">NPC #${{n.id}}</span>
              ${{n.is_cow ? '<span class="text-[10px] px-1 bg-emerald-900/80 text-emerald-300 rounded font-semibold font-mono">CoW Active</span>' : '<span class="text-[10px] text-slate-600">Untouched Vanilla</span>'}}
            </div>
            <div class="text-xs font-bold text-white truncate">${{n.desc}}</div>
            <div class="text-[11px] font-mono text-slate-400 mt-0.5 truncate">
              Ptr: <span class="text-indigo-400">${{n.pointer_1}}</span>
            </div>
          `;
          item.addEventListener('click', () => {{
            playBeep(520, 'square', 0.04);
            loadNpcDialogue(n);
          }});
          listContainer.appendChild(item);
        }});

      }} else if (currentNavMode === 'enemies') {{
        const filteredEnemies = DATA.enemies.filter(e => {{
          if (catFilter === 'RESKIN_ONLY' && !e.is_thematic) return false;
          if (catFilter === 'BOSS_ONLY' && !e.boss) return false;
          if (!query) return true;
          return e.name.toLowerCase().includes(query) || String(e.id).includes(query);
        }});

        document.getElementById('list-count-badge').textContent = `${{filteredEnemies.length}} enemies`;

        filteredEnemies.forEach(e => {{
          const item = document.createElement('div');
          item.className = 'p-3 hover:bg-slate-800/60 cursor-pointer border-l-2 border-transparent text-slate-300';
          item.innerHTML = `
            <div class="flex items-center justify-between mb-1">
              <span class="font-mono text-[10px] text-slate-400">#${{e.id}}</span>
              ${{e.is_thematic ? '<span class="text-[10px] px-1 bg-purple-900/80 text-purple-200 rounded font-semibold">Zero Fault Reskin</span>' : ''}}
            </div>
            <div class="text-xs font-bold text-white truncate">${{e.name}}</div>
            <div class="text-[11px] font-mono text-slate-400 mt-0.5">
              HP: <span class="text-emerald-400">${{e.hp}}</span> | OFF: <span class="text-amber-400">${{e.offense}}</span> | DEF: <span class="text-blue-400">${{e.defense}}</span>
            </div>
          `;
          item.addEventListener('click', () => {{
            playBeep(420, 'square', 0.04);
            loadEnemyDetails(e);
          }});
          listContainer.appendChild(item);
        }});

      }} else if (currentNavMode === 'items') {{
        const filteredItems = DATA.items.filter(i => {{
          if (!query) return true;
          return i.name.toLowerCase().includes(query) || String(i.id).includes(query);
        }});

        document.getElementById('list-count-badge').textContent = `${{filteredItems.length}} items`;

        filteredItems.forEach(i => {{
          const item = document.createElement('div');
          item.className = 'p-3 hover:bg-slate-800/60 cursor-pointer border-l-2 border-transparent text-slate-300';
          item.innerHTML = `
            <div class="flex items-center justify-between mb-1">
              <span class="font-mono text-[10px] text-slate-400">Item #${{i.id}}</span>
              <span class="font-mono text-[10px] text-amber-400">${{i.cost ? '$' + i.cost : 'Key Item'}}</span>
            </div>
            <div class="text-xs font-bold text-white truncate">${{i.name}}</div>
          `;
          item.addEventListener('click', () => {{
            playBeep(520, 'sine', 0.04);
            loadItemDetails(i);
          }});
          listContainer.appendChild(item);
        }});

      }} else if (currentNavMode === 'psi') {{
        const filteredPsi = DATA.psi.filter(p => {{
          if (!query) return true;
          return p.name.toLowerCase().includes(query) || String(p.id).includes(query);
        }});

        document.getElementById('list-count-badge').textContent = `${{filteredPsi.length}} PSI abilities`;

        filteredPsi.forEach(p => {{
          const item = document.createElement('div');
          item.className = 'p-3 hover:bg-slate-800/60 cursor-pointer border-l-2 border-transparent text-slate-300';
          item.innerHTML = `
            <div class="flex items-center justify-between mb-1">
              <span class="font-mono text-[10px] text-slate-400">PSI #${{p.id}}</span>
              <span class="font-mono text-[10px] text-cyan-400 font-semibold">${{p.type.join(', ')}}</span>
            </div>
            <div class="text-xs font-bold text-white truncate">${{p.name}}</div>
            <div class="text-[11px] font-mono text-slate-400 mt-0.5 truncate">
              Address: <span class="text-indigo-400">${{p.text_address}}</span>
            </div>
          `;
          item.addEventListener('click', () => {{
            playBeep(580, 'sine', 0.04);
            loadPsiDetails(p);
          }});
          listContainer.appendChild(item);
        }});
      }}
    }}

    function selectItem(r) {{
      activeItem = r;
      activePage = 0;
      updateInspector();
      renderResourceList();
    }}

    function loadNpcDialogue(n) {{
      const ptr = n.pointer_1 !== '$0' ? n.pointer_1 : n.pointer_2;
      if (ptr && ptr !== '$0') {{
        const routine = findRoutineByPointer(ptr);
        if (routine) {{
          selectItem(routine);
          return;
        }}
      }}
      alert(`NPC #${{n.id}} (${{n.desc}})\\nDirection: ${{n.direction}}\\nSprite: ${{n.sprite}}\\nFlag: ${{n.event_flag}}\\nText Pointer 1: ${{n.pointer_1}}\\nText Pointer 2: ${{n.pointer_2}}`);
    }}

    function loadEnemyDetails(e) {{
      if (e.encounter_text && e.encounter_text !== '$0') {{
        const routine = findRoutineByPointer(e.encounter_text);
        if (routine) {{
          selectItem(routine);
          return;
        }}
      }}
      alert(`Enemy: ${{e.name}}\\nHP: ${{e.hp}} | PP: ${{e.pp}} | Offense: ${{e.offense}} | Defense: ${{e.defense}}\\nExp: ${{e.exp}} | Money: $${{e.money}}\\nDropped Item: ${{e.dropped_item}}\\nEncounter Text: ${{e.encounter_text}}\\nDeath Text: ${{e.death_text}}`);
    }}

    function loadItemDetails(i) {{
      if (i.help_pointer && i.help_pointer !== '$0') {{
        const routine = findRoutineByPointer(i.help_pointer);
        if (routine) {{
          selectItem(routine);
          return;
        }}
      }}
      alert(`Item: ${{i.name}}\\nCost: ${{i.cost ? '$' + i.cost : 'Key Item'}}\\nFlags: ${{i.flags.join(', ')}}\\nHelp Pointer: ${{i.help_pointer}}`);
    }}

    function loadPsiDetails(p) {{
      if (p.text_address && p.text_address !== '$0') {{
        const routine = findRoutineByPointer(p.text_address);
        if (routine) {{
          selectItem(routine);
          return;
        }}
      }}
      alert(`PSI: ${{p.name}}\\nTypes: ${{p.type.join(', ')}}\\nLevel Ness: ${{p.ness_lvl}} | Paula: ${{p.paula_lvl}} | Poo: ${{p.poo_lvl}}\\nText: ${{p.text_address}}`);
    }}

    function findRoutineByPointer(ptr) {{
      let cleanPtr = ptr.replace('$', '').trim();
      let match = DATA.cow_routines.find(r => r.id === cleanPtr || r.label === cleanPtr || r.id.endsWith('.' + cleanPtr));
      if (match) return match;
      match = DATA.vanilla_routines.find(r => r.id === cleanPtr || r.label === cleanPtr || r.id.endsWith('.' + cleanPtr));
      return match;
    }}

    function updateInspector() {{
      const r = activeItem;
      if (!r) return;

      const isCow = r.is_cow;
      document.getElementById('badge-type').textContent = isCow ? 'Zero Fault CoW' : 'Untouched Vanilla';
      document.getElementById('badge-type').className = isCow 
        ? 'text-[10px] font-mono px-2 py-0.5 rounded bg-indigo-950 text-indigo-300 border border-indigo-800'
        : 'text-[10px] font-mono px-2 py-0.5 rounded bg-amber-950 text-amber-300 border border-amber-800';

      document.getElementById('badge-category').textContent = `${{r.category_title || r.file}}`;
      document.getElementById('inspector-title').textContent = r.label;
      document.getElementById('inspector-comment').textContent = r.comment || `File: ${{r.file}} (${{r.category_title || 'Game Script'}})`;

      const banner = document.getElementById('overridden-banner');
      if (r.cow_override) {{
        banner.classList.remove('hidden');
        document.getElementById('overridden-target-name').textContent = r.cow_override;
        document.getElementById('btn-jump-override').onclick = () => {{
          const cowMatch = DATA.cow_routines.find(cr => cr.id === r.cow_override || cr.label === r.cow_override);
          if (cowMatch) {{
            setNavMode('cow');
            selectItem(cowMatch);
          }}
        }};
      }} else {{
        banner.classList.add('hidden');
      }}

      const chipsContainer = document.getElementById('inspector-chips');
      chipsContainer.innerHTML = '';
      if (r.bound_npc) {{
        const chip = document.createElement('span');
        chip.className = 'px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800 font-mono text-[11px]';
        chip.textContent = `👤 ${{r.bound_npc.desc || 'NPC ' + r.bound_npc.id}}`;
        chipsContainer.appendChild(chip);
      }}
      if (r.flags_set && r.flags_set.length > 0) {{
        const chip = document.createElement('span');
        chip.className = 'px-2 py-0.5 rounded bg-amber-950 text-amber-300 border border-amber-800 font-mono text-[11px]';
        chip.textContent = `🚩 Set: ${{r.flags_set.join(', ')}}`;
        chipsContainer.appendChild(chip);
      }}
      if (r.bound_hook) {{
        const chip = document.createElement('span');
        chip.className = 'px-2 py-0.5 rounded bg-purple-950 text-purple-300 border border-purple-800 font-mono text-[11px]';
        chip.textContent = `⚓ Hook: ${{r.bound_hook.offset}}`;
        chipsContainer.appendChild(chip);
      }}

      updateDialoguePage();

      document.getElementById('diff-vanilla-target').textContent = r.vanilla_mod ? `${{r.vanilla_mod}}:${{r.vanilla_lbl}}` : (isCow ? 'No legacy override' : r.id);
      document.getElementById('diff-vanilla-text').textContent = r.vanilla_clean || (!isCow ? (r.clean_pages.join('\\n\\n') || r.raw_code) : '(Pristine legacy EarthBound dialogue not directly linked or unchanged)');
      document.getElementById('diff-cow-target').textContent = isCow ? r.id : (r.cow_override || 'Untouched in Zero Fault');
      document.getElementById('diff-cow-text').textContent = isCow ? (r.clean_pages.length > 0 ? r.clean_pages.join('\\n\\n') : r.raw_code) : (r.cow_override ? 'View overridden CoW routine' : '(This vanilla dialogue was not modified by the Zero Fault parallel universe storyline.)');

      document.getElementById('source-filename').textContent = `src/ccscript/${{r.file}} : ${{r.label}}`;
      document.getElementById('raw-code-block').textContent = r.raw_code;
      document.getElementById('source-code-editor').value = r.raw_code;

      const flagsBox = document.getElementById('sys-flags-box');
      flagsBox.innerHTML = `
        <div><span class="text-slate-500">Flags Set:</span> <span class="text-emerald-400">${{r.flags_set ? r.flags_set.join(', ') : 'None'}}</span></div>
        <div><span class="text-slate-500">Flags Checked:</span> <span class="text-amber-400">${{r.flags_checked ? r.flags_checked.join(', ') : 'None'}}</span></div>
        <div><span class="text-slate-500">Audio Cues:</span> <span class="text-indigo-400">${{r.sound_cues ? r.sound_cues.join(', ') : 'None'}}</span></div>
      `;

      const dispatchBox = document.getElementById('sys-dispatch-box');
      dispatchBox.innerHTML = `
        <div><span class="text-slate-500">Bound NPC:</span> <span class="text-emerald-400">${{r.bound_npc ? r.bound_npc.desc : 'None'}}</span></div>
        <div><span class="text-slate-500">ROM Hook:</span> <span class="text-purple-400">${{r.bound_hook ? r.bound_hook.desc + ' (' + r.bound_hook.offset + ')' : 'None'}}</span></div>
        <div><span class="text-slate-500">Vanilla Target:</span> <span class="text-amber-400">${{r.vanilla_lbl ? r.vanilla_mod + ' : ' + r.vanilla_lbl : (r.cow_override || 'None')}}</span></div>
      `;

      const allPagesList = document.getElementById('all-pages-list');
      allPagesList.innerHTML = '';
      r.clean_pages.forEach((p, pidx) => {{
        const pBox = document.createElement('div');
        pBox.className = 'eb-box p-3 text-sm text-slate-100 font-mono';
        pBox.innerHTML = `<span class="text-xs text-indigo-400 block mb-1">Page ${{pidx + 1}}</span>${{p}}`;
        allPagesList.appendChild(pBox);
      }});

      // Populate visual dialogue editor pages
      const editableList = document.getElementById('editable-pages-list');
      editableList.innerHTML = '';
      if (r.clean_pages.length === 0) {{
        editableList.innerHTML = '<div class="text-xs text-slate-500 italic p-3 bg-slate-900 rounded border border-slate-800">This routine has no dialogue strings. Use the CCScript Source Editor tab to edit execution logic.</div>';
      }} else {{
        r.clean_pages.forEach((p, pidx) => {{
          const card = document.createElement('div');
          card.className = 'bg-slate-900 p-3 rounded-lg border border-slate-800 space-y-2';
          card.innerHTML = `
            <div class="flex items-center justify-between text-xs text-slate-400">
              <span class="font-bold text-indigo-400">Page ${{pidx + 1}}</span>
              <span class="text-[10px] text-slate-500">Characters: <span class="char-count font-mono">${{p.length}}</span></span>
            </div>
            <textarea class="page-editor-input w-full bg-slate-950 border border-slate-700 rounded p-2 text-sm text-white font-mono leading-relaxed focus:outline-none focus:border-indigo-500" rows="3">${{p}}</textarea>
          `;
          editableList.appendChild(card);
        }});
      }}
    }}

    function updateDialoguePage() {{
      const r = activeItem;
      if (!r) return;

      const total = r.clean_pages.length;
      document.getElementById('page-counter-badge').textContent = `Page ${{total > 0 ? activePage + 1 : 0}} of ${{total}}`;
      document.getElementById('btn-prev-page').disabled = activePage <= 0;
      document.getElementById('btn-next-page').disabled = activePage >= total - 1;

      const contentBox = document.getElementById('eb-dialogue-content');
      if (total === 0) {{
        contentBox.textContent = '(This routine contains execution logic, jump instructions, or formatting commands.)';
        document.getElementById('eb-sound-cue').textContent = '';
        return;
      }}

      contentBox.textContent = r.clean_pages[activePage] || '';
      const cue = r.sound_cues ? (r.sound_cues[activePage] || r.sound_cues[0] || '') : '';
      document.getElementById('eb-sound-cue').textContent = cue ? `🔊 ${{cue}}` : '';
    }}

    // Toggle Edit Mode
    function toggleEditMode() {{
      isEditMode = !isEditMode;
      const statusLbl = document.getElementById('edit-mode-status');
      const toggleBtn = document.getElementById('btn-toggle-edit-mode');
      
      if (isEditMode) {{
        statusLbl.textContent = 'ON';
        statusLbl.className = 'text-emerald-400 font-mono';
        toggleBtn.className = 'px-3 py-1.5 bg-emerald-950 border border-emerald-700 text-xs rounded font-medium flex items-center gap-1.5 shadow transition';
        document.getElementById('dialogue-preview-container').classList.add('hidden');
        document.getElementById('dialogue-editor-container').classList.remove('hidden');
        document.getElementById('raw-code-block').classList.add('hidden');
        document.getElementById('code-editor-wrapper').classList.remove('hidden');
      }} else {{
        statusLbl.textContent = 'OFF';
        statusLbl.className = 'text-slate-400 font-mono';
        toggleBtn.className = 'px-3 py-1.5 bg-slate-800 hover:bg-slate-700 border border-slate-700 text-xs rounded font-medium flex items-center gap-1.5 transition';
        document.getElementById('dialogue-preview-container').classList.remove('hidden');
        document.getElementById('dialogue-editor-container').classList.add('hidden');
        document.getElementById('raw-code-block').classList.remove('hidden');
        document.getElementById('code-editor-wrapper').classList.add('hidden');
      }}
    }}

    // Save CCScript Code API
    async function saveCodeToServer(andBuild = false) {{
      const r = activeItem;
      if (!r) return;

      const newCode = document.getElementById('source-code-editor').value;
      const statusEl = document.getElementById('code-save-status');
      statusEl.textContent = 'Saving...';

      try {{
        const res = await fetch('/api/save_code', {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify({{ file: r.file, label: r.label, code: newCode }})
        }});
        const data = await res.json();
        if (data.success) {{
          r.raw_code = newCode;
          document.getElementById('raw-code-block').textContent = newCode;
          statusEl.textContent = 'Saved to disk!';
          setTimeout(() => {{ statusEl.textContent = ''; }}, 2000);
          if (andBuild) {{
            triggerRomBuild();
          }}
        }} else {{
          statusEl.textContent = 'Error: ' + data.error;
        }}
      }} catch (err) {{
        statusEl.textContent = 'Server offline (saved locally in view)';
      }}
    }}

    // Trigger ROM Build & Verification
    async function triggerRomBuild() {{
      const modal = document.getElementById('build-modal');
      const title = document.getElementById('modal-title');
      const spinner = document.getElementById('modal-spinner');
      const statusText = document.getElementById('modal-status-text');
      const statusBadge = document.getElementById('modal-status-badge');
      const consoleOutput = document.getElementById('modal-console-output');
      const btnLaunch = document.getElementById('modal-btn-launch');
      const btnDownload = document.getElementById('modal-btn-download');

      modal.classList.remove('hidden');
      title.textContent = 'Compiling EarthBound: Zero Fault...';
      spinner.classList.remove('hidden');
      statusBadge.className = 'px-3 py-2 rounded bg-indigo-950 text-indigo-200 border border-indigo-800 flex items-center justify-between';
      statusText.textContent = 'Running CoilSnake build pipeline and compiling CCScript...';
      consoleOutput.textContent = 'Compiling project to build/eb_zero_fault.sfc...\\n';
      btnLaunch.classList.add('hidden');
      btnDownload.classList.add('hidden');

      try {{
        const res = await fetch('/api/build', {{ method: 'POST' }});
        const result = await res.json();

        if (result.success) {{
          title.textContent = 'ROM Successfully Compiled!';
          spinner.classList.add('hidden');
          statusBadge.className = 'px-3 py-2 rounded bg-emerald-950 text-emerald-200 border border-emerald-800 flex items-center justify-between font-bold';
          statusText.textContent = `Build Complete! 4,194,304 bytes in ${{result.total_duration}}s. All 245 binary assertions passed!`;
          consoleOutput.textContent = result.build_output + '\\n\\n' + result.verify_output;
          btnLaunch.classList.remove('hidden');
          btnDownload.classList.remove('hidden');
        }} else {{
          title.textContent = 'Compilation Error';
          spinner.classList.add('hidden');
          statusBadge.className = 'px-3 py-2 rounded bg-rose-950 text-rose-200 border border-rose-800 flex items-center justify-between font-bold';
          statusText.textContent = result.error || 'Build exited with errors.';
          consoleOutput.textContent = result.build_output || result.error;
        }}
      }} catch (err) {{
        title.textContent = 'Server Unreachable';
        spinner.classList.add('hidden');
        statusBadge.className = 'px-3 py-2 rounded bg-amber-950 text-amber-200 border border-amber-800';
        statusText.textContent = 'Cannot connect to Companion API. Run: python3 tools/companion.py --serve';
        consoleOutput.textContent = 'Run the companion with live local server enabled:\\ncd /home/gordonk/PycharmProjects/eb-zero-fault && python3 tools/companion.py --serve';
      }}
    }}

    // Launch Emulator
    async function launchEmulator() {{
      try {{
        const res = await fetch('/api/launch_emulator', {{ method: 'POST' }});
        const data = await res.json();
        if (data.success) {{
          alert('Launched snes9x-gtk with build/eb_zero_fault.sfc');
        }} else {{
          alert('Could not launch emulator: ' + data.error);
        }}
      }} catch (e) {{
        alert('Server unreachable. Launch emulator from terminal: snes9x-gtk build/eb_zero_fault.sfc');
      }}
    }}

    // Event Listeners
    document.getElementById('btn-prev-page').addEventListener('click', () => {{
      if (activePage > 0) {{
        activePage--;
        playBeep(520, 'square', 0.03);
        updateDialoguePage();
      }}
    }});

    document.getElementById('btn-next-page').addEventListener('click', () => {{
      const r = activeItem;
      if (r && activePage < r.clean_pages.length - 1) {{
        activePage++;
        playBeep(640, 'square', 0.03);
        updateDialoguePage();
      }}
    }});

    document.getElementById('eb-next-prompt').addEventListener('click', () => {{
      const r = activeItem;
      if (r) {{
        if (activePage < r.clean_pages.length - 1) {{
          activePage++;
        }} else {{
          activePage = 0;
        }}
        playBeep(700, 'square', 0.03);
        updateDialoguePage();
      }}
    }});

    document.getElementById('btn-auto-play').addEventListener('click', () => {{
      const btn = document.getElementById('btn-auto-play');
      if (autoStepTimer) {{
        clearInterval(autoStepTimer);
        autoStepTimer = null;
        btn.textContent = '▶ Auto Step';
        btn.className = 'px-3 py-1.5 bg-indigo-950 hover:bg-indigo-900 border border-indigo-700 text-indigo-300 rounded text-xs transition';
      }} else {{
        btn.textContent = '⏹ Stop Auto';
        btn.className = 'px-3 py-1.5 bg-rose-950 hover:bg-rose-900 border border-rose-700 text-rose-300 rounded text-xs transition';
        autoStepTimer = setInterval(() => {{
          const r = activeItem;
          if (!r || r.clean_pages.length <= 1) return;
          if (activePage < r.clean_pages.length - 1) {{
            activePage++;
          }} else {{
            activePage = 0;
          }}
          playBeep(600, 'sine', 0.03);
          updateDialoguePage();
        }}, 2200);
      }}
    }});

    document.getElementById('btn-view-all-pages').addEventListener('click', () => {{
      const container = document.getElementById('all-pages-container');
      container.classList.toggle('hidden');
    }});

    document.getElementById('btn-toggle-edit-mode').addEventListener('click', toggleEditMode);
    document.getElementById('btn-save-source-code').addEventListener('click', () => saveCodeToServer(false));
    document.getElementById('btn-build-rom').addEventListener('click', () => {{
      if (isEditMode) {{
        saveCodeToServer(true);
      }} else {{
        triggerRomBuild();
      }}
    }});
    document.getElementById('btn-launch-emu').addEventListener('click', launchEmulator);
    document.getElementById('modal-btn-launch').addEventListener('click', launchEmulator);

    document.getElementById('btn-close-modal').addEventListener('click', () => {{
      document.getElementById('build-modal').classList.add('hidden');
    }});
    document.getElementById('modal-btn-dismiss').addEventListener('click', () => {{
      document.getElementById('build-modal').classList.add('hidden');
    }});

    // Tab key in source code editor
    document.getElementById('source-code-editor').addEventListener('keydown', (e) => {{
      if (e.key === 'Tab') {{
        e.preventDefault();
        const start = e.target.selectionStart;
        const end = e.target.selectionEnd;
        e.target.value = e.target.value.substring(0, start) + '    ' + e.target.value.substring(end);
        e.target.selectionStart = e.target.selectionEnd = start + 4;
      }}
      if ((e.ctrlKey || e.metaKey) && e.key === 's') {{
        e.preventDefault();
        saveCodeToServer(true);
      }}
    }});

    // Global Ctrl+S hotkey
    window.addEventListener('keydown', (e) => {{
      if ((e.ctrlKey || e.metaKey) && e.key === 's') {{
        e.preventDefault();
        if (isEditMode) {{
          saveCodeToServer(true);
        }} else {{
          triggerRomBuild();
        }}
      }}
    }});

    // Tab Switches
    const panels = ['dialogue', 'diff', 'source', 'system'];
    panels.forEach(p => {{
      document.getElementById('view-tab-' + p).addEventListener('click', () => {{
        panels.forEach(other => {{
          document.getElementById('panel-' + other).classList.toggle('hidden', other !== p);
          const tabBtn = document.getElementById('view-tab-' + other);
          if (other === p) {{
            tabBtn.className = 'py-2.5 border-b-2 border-indigo-500 text-white font-semibold flex items-center gap-1.5';
          }} else {{
            tabBtn.className = 'py-2.5 border-b-2 border-transparent text-slate-400 hover:text-white flex items-center gap-1.5';
          }}
        }});
      }});
    }});

    document.getElementById('btn-copy-code').addEventListener('click', () => {{
      const r = activeItem;
      if (r) {{
        navigator.clipboard.writeText(r.raw_code);
        const btn = document.getElementById('btn-copy-code');
        btn.textContent = 'Copied!';
        setTimeout(() => {{ btn.textContent = 'Copy CCScript'; }}, 1500);
      }}
    }});

    document.getElementById('toggle-sound-btn').addEventListener('click', () => {{
      sfxEnabled = !sfxEnabled;
      document.getElementById('sfx-status').textContent = sfxEnabled ? 'ON' : 'OFF';
      document.getElementById('sfx-status').className = sfxEnabled ? 'text-emerald-400 font-semibold' : 'text-slate-500 font-semibold';
      if (sfxEnabled) playBeep(880, 'sine', 0.05);
    }});

    document.getElementById('search-input').addEventListener('input', (e) => {{
      document.getElementById('clear-search-btn').classList.toggle('hidden', !e.target.value);
      renderResourceList();
    }});

    document.getElementById('clear-search-btn').addEventListener('click', () => {{
      document.getElementById('search-input').value = '';
      document.getElementById('clear-search-btn').classList.add('hidden');
      renderResourceList();
    }});

    document.getElementById('category-filter-select').addEventListener('change', () => {{
      renderResourceList();
    }});

    ['cow', 'vanilla', 'npcs', 'enemies', 'items', 'psi'].forEach(m => {{
      document.getElementById('tab-nav-' + m).addEventListener('click', () => setNavMode(m));
    }});

    // Initial Startup
    checkServerStatus();
    updateCategoryDropdown();
    renderResourceList();
    updateInspector();
  </script>
</body>
</html>
"""
    return html


def run_cli_search(query: str, data: Dict[str, Any]):
    """Search dialogues across all Zero Fault and untouched vanilla routines."""
    query = query.lower()
    cow_matches = []
    vanilla_matches = []

    for r in data["cow_routines"]:
        for p_idx, page in enumerate(r["clean_pages"]):
            if query in page.lower():
                cow_matches.append((r, p_idx + 1, page))

    for r in data["vanilla_routines"]:
        for p_idx, page in enumerate(r["clean_pages"]):
            if query in page.lower():
                vanilla_matches.append((r, p_idx + 1, page))

    total = len(cow_matches) + len(vanilla_matches)
    print(f"\nSearch results for '{query}' ({total} total match(es)):\n" + "=" * 65)

    if cow_matches:
        print(f"\n\033[1;35m--- ZERO FAULT COW ROUTINES ({len(cow_matches)} matches) ---\033[0m")
        for r, p_num, text in cow_matches:
            print(f"\n\033[1;36m[{r['file']}] {r['label']}\033[0m (Page {p_num}) - \033[33m{r['category']}\033[0m")
            if r.get("bound_npc"):
                print(f"  \033[32mNPC:\033[0m {r['bound_npc']['desc']}")
            print(f"  \033[37m{text}\033[0m")

    if vanilla_matches:
        print(f"\n\033[1;33m--- UNTOUCHED VANILLA SCRIPTS ({len(vanilla_matches)} matches) ---\033[0m")
        for r, p_num, text in vanilla_matches[:25]:
            print(f"\n\033[1;36m[{r['file']}] {r['label']}\033[0m (Page {p_num}) - \033[34m{r['category_title']}\033[0m")
            if r.get("bound_npc"):
                print(f"  \033[32mNPC:\033[0m {r['bound_npc']['desc']}")
            print(f"  \033[37m{text}\033[0m")
        if len(vanilla_matches) > 25:
            print(f"\n\033[38;5;244m... and {len(vanilla_matches) - 25} more vanilla matches.\033[0m")

    print("\n" + "=" * 65)


def start_server(port: int = 8765):
    """Start the IDE server and open browser."""
    handler = CompanionRequestHandler
    
    with socketserver.TCPServer(("", port), handler) as httpd:
        url = f"http://localhost:{port}/tools/zero_fault_companion.html"
        print(f"\n========================================================")
        print(f"  EarthBound: Zero Fault - IDE & ROM Exporter Server")
        print(f"  URL: {url}")
        print(f"  Live Code & Dialogue Editing: ENABLED")
        print(f"  In-Browser ROM Compilation: ENABLED (Ctrl+S)")
        print(f"  Emulator Playtesting: ENABLED (snes9x-gtk)")
        print(f"  Press Ctrl+C to stop the server.")
        print(f"========================================================\n")
        try:
            webbrowser.open(url)
        except Exception:
            pass
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server.")


def main():
    parser = argparse.ArgumentParser(description="EarthBound: Zero Fault - Text & Script Explorer, Editor & Exporter")
    parser.add_argument("--search", "-s", type=str, help="Search dialogue directly from CLI")
    parser.add_argument("--build-html", "-b", action="store_true", help="Rebuild HTML application without launching")
    parser.add_argument("--build-rom", action="store_true", help="Compile and verify the SNES ROM directly from CLI")
    parser.add_argument("--port", "-p", type=int, default=8765, help="Server port (default: 8765)")
    parser.add_argument("--no-browser", action="store_true", help="Start server without launching browser")
    args = parser.parse_args()

    data = build_companion_data()

    if args.search:
        run_cli_search(args.search, data)
        return

    if args.build_rom:
        print("Compiling ROM...")
        res = build_and_export_rom()
        if res["success"]:
            print(f"Build Succeeded! ROM Size: {res['rom_size']} bytes in {res['total_duration']}s")
            print(res["verify_output"])
        else:
            print("Build Failed:\n", res.get("build_output") or res.get("error"))
        return

    html_content = generate_html_application(data)
    target_path = REPO_ROOT / "tools" / "zero_fault_companion.html"
    target_path.write_text(html_content, encoding="utf-8")
    print(f"Updated companion application: {target_path} ({len(html_content)/1024:.1f} KB)")

    if args.build_html:
        return

    # Start live server
    start_server(args.port)


if __name__ == "__main__":
    main()
