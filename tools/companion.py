#!/usr/bin/env python3
"""
EarthBound: Zero Fault - ROM Text & Script Explorer (Zero Fault Companion)

An interactive, searchable GUI and CLI companion for inspecting all text, scripts,
dialogue trees, NPC table bindings, and thematic enemy reskins in EarthBound: Zero Fault.
Like SCI Companion, but customized specifically for this 32-Mbit SNES ROM hack.
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

    # In EarthBound, [03], next, and {prompt} trigger dialogue page breaks
    pattern = re.compile(r"\"([^\"]*)\"|(\b(?:next|linebreak|newline|eob|end)\b)|(\[[0-9A-Fa-f\s]+\])")
    pages = []
    current_page = []

    for match in pattern.finditer(clean_code):
        s, kw, bcode = match.groups()
        if s is not None:
            # Split on [03] or {prompt} inside strings
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
    print("Parsing project configuration tables...")
    npc_table = yaml.safe_load((REPO_ROOT / "src" / "npc_config_table.yml").read_text(encoding="utf-8"))
    enemy_table = yaml.safe_load((REPO_ROOT / "src" / "enemy_configuration_table.yml").read_text(encoding="utf-8"))
    item_table = yaml.safe_load((REPO_ROOT / "src" / "item_configuration_table.yml").read_text(encoding="utf-8"))

    item_dict = {int(k): v.get("Name", f"Item {k}") for k, v in item_table.items()}

    npc_bindings, rom_hooks = load_verify_rom_metadata()
    trampoline_targets = find_vanilla_trampoline_targets()
    vanilla_files = load_vanilla_archive()

    # Map NPC table pointers
    npc_pointer_map = {}
    for npc_id, npc_data in npc_table.items():
        p1 = str(npc_data.get("Text Pointer 1", ""))
        p2 = str(npc_data.get("Text Pointer 2", ""))
        if p1 and p1 != "$0":
            npc_pointer_map[p1] = (npc_id, 1, npc_data)
        if p2 and p2 != "$0":
            npc_pointer_map[p2] = (npc_id, 2, npc_data)

    print("Parsing custom CoW script modules...")
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
            
            # Match NPC binding
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

            # Match ROM hook
            bound_hook = None
            for hdesc, hval in rom_hooks.items():
                if current_label in hdesc or cfile.stem in hdesc.lower():
                    bound_hook = {"offset": hex(hval[0]), "desc": hdesc}
                    break

            # Match vanilla target & text
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
                "phase_id": phase_info[0],
                "phase_title": phase_info[1],
                "phase_desc": phase_info[2],
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

    print("Formatting bestiary, item, and NPC directory...")
    # Thematic enemies
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

    # Items
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

    # NPCs directory
    npc_list = []
    for nid, ndata in npc_table.items():
        p1 = str(ndata.get("Text Pointer 1", "$0"))
        p2 = str(ndata.get("Text Pointer 2", "$0"))
        is_cow = "cow_" in p1 or "cow_" in p2
        cow_routine_id = p1 if "cow_" in p1 else (p2 if "cow_" in p2 else None)
        desc = npc_bindings.get(f"npc_{nid}", f"NPC #{nid}")
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

    # Phases summary
    phases = []
    seen_phases = set()
    for fname, ptuple in PHASE_MAPPINGS.items():
        pid, ptitle, pdesc = ptuple
        if pid not in seen_phases:
            seen_phases.add(pid)
            phases.append({"id": pid, "title": ptitle, "desc": pdesc})

    payload = {
        "meta": {
            "title": "EarthBound: Zero Fault - ROM Text & Script Explorer",
            "version": "Phase 15 Complete (32-Mbit USA SNES)",
            "total_routines": len(cow_routines),
            "total_dialogue_pages": sum(r["page_count"] for r in cow_routines),
            "total_npcs": len(npc_table),
            "total_cow_npcs": sum(1 for n in npc_list if n["is_cow"]),
            "total_enemies": len(enemy_table),
            "total_thematic_enemies": sum(1 for e in enemy_list if e["is_thematic"]),
            "total_items": len(item_table),
            "total_hooks": len(rom_hooks),
        },
        "phases": phases,
        "routines": cow_routines,
        "npcs": npc_list,
        "enemies": enemy_list,
        "items": item_list,
    }

    print(f"Extraction complete: {len(cow_routines)} routines, {len(npc_list)} NPCs, {len(enemy_list)} enemies, {len(item_list)} items.")
    return payload


def generate_html_application(data: Dict[str, Any]) -> str:
    """Build the standalone interactive Single Page Application."""
    data_json = json.dumps(data)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Zero Fault Companion - EarthBound ROM Text & Script Explorer</title>
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
      font-family: 'AppleKid', monospace, monospace;
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
    /* Custom scrollbars */
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
  <header class="bg-slate-900 border-b border-slate-800 px-4 py-2.5 flex items-center justify-between shrink-0 shadow-md">
    <div class="flex items-center gap-3">
      <div class="w-8 h-8 rounded bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center font-bold text-white shadow">
        0F
      </div>
      <div>
        <h1 class="text-sm font-bold tracking-wide text-white flex items-center gap-2">
          EarthBound: Zero Fault <span class="text-xs px-2 py-0.5 rounded bg-indigo-950 border border-indigo-700 text-indigo-300 font-mono">ROM Text & Script Companion</span>
        </h1>
        <p class="text-[11px] text-slate-400">Copy-on-Write Memory Architecture Narrative & Systems Explorer</p>
      </div>
    </div>

    <!-- Quick Stats Bar -->
    <div class="hidden md:flex items-center gap-2 text-xs">
      <span class="px-2 py-1 bg-slate-800/80 border border-slate-700 rounded text-slate-300">
        <strong class="text-indigo-400 font-mono">{data['meta']['total_routines']}</strong> Routines
      </span>
      <span class="px-2 py-1 bg-slate-800/80 border border-slate-700 rounded text-slate-300">
        <strong class="text-purple-400 font-mono">{data['meta']['total_dialogue_pages']}</strong> Pages
      </span>
      <span class="px-2 py-1 bg-slate-800/80 border border-slate-700 rounded text-slate-300">
        <strong class="text-emerald-400 font-mono">{data['meta']['total_cow_npcs']}</strong> CoW NPCs
      </span>
      <span class="px-2 py-1 bg-slate-800/80 border border-slate-700 rounded text-slate-300">
        <strong class="text-amber-400 font-mono">{data['meta']['total_thematic_enemies']}</strong> Reskins
      </span>
    </div>

    <!-- Right Controls -->
    <div class="flex items-center gap-2">
      <button id="toggle-sound-btn" class="px-2.5 py-1 text-xs bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded flex items-center gap-1.5 transition">
        <span>🔊</span> SFX: <span id="sfx-status" class="text-emerald-400 font-semibold">ON</span>
      </button>
      <a href="https://github.com/oopismcgoopis/eb-zero-fault" target="_blank" class="px-2.5 py-1 text-xs bg-indigo-600/80 hover:bg-indigo-600 text-white rounded transition shadow">
        Repo
      </a>
    </div>
  </header>

  <!-- Main Multi-Pane Workspace -->
  <div class="flex-1 flex overflow-hidden">

    <!-- Left Sidebar: Categories & Search -->
    <aside class="w-80 md:w-96 bg-slate-900/90 border-r border-slate-800 flex flex-col shrink-0">
      
      <!-- Search Input -->
      <div class="p-3 border-b border-slate-800 space-y-2">
        <div class="relative">
          <input id="search-input" type="text" placeholder="Search dialogue, labels, NPCs, flags..." 
                 class="w-full bg-slate-950 border border-slate-700 rounded px-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition" />
          <button id="clear-search-btn" class="absolute right-2.5 top-2 text-xs text-slate-500 hover:text-white hidden">✕</button>
        </div>

        <!-- Mode Switcher Tabs -->
        <div class="grid grid-cols-4 gap-1 p-0.5 bg-slate-950 border border-slate-800 rounded text-[11px] font-medium text-slate-400 text-center">
          <button id="tab-nav-story" class="py-1 px-1.5 rounded bg-indigo-600 text-white shadow">Story</button>
          <button id="tab-nav-npcs" class="py-1 px-1.5 rounded hover:text-white hover:bg-slate-800">NPCs</button>
          <button id="tab-nav-enemies" class="py-1 px-1.5 rounded hover:text-white hover:bg-slate-800">Bestiary</button>
          <button id="tab-nav-items" class="py-1 px-1.5 rounded hover:text-white hover:bg-slate-800">Items</button>
        </div>
      </div>

      <!-- Filter Bar / Active Phase Dropdown -->
      <div class="px-3 py-1.5 bg-slate-950/60 border-b border-slate-800 flex items-center justify-between text-xs text-slate-400">
        <span id="list-count-badge" class="font-mono text-slate-300">Loading...</span>
        <select id="phase-filter-select" class="bg-slate-900 border border-slate-800 rounded px-1.5 py-0.5 text-[11px] text-slate-300 focus:outline-none">
          <option value="ALL">All Story Phases</option>
          <option value="P04">Phase 04: Onett</option>
          <option value="P07">Phase 07: Twoson / Cult</option>
          <option value="P08">Phase 08: Threed / Saturn</option>
          <option value="P09">Phase 09: Fourside / Moon</option>
          <option value="P10">Phase 10: Summers / Poo</option>
          <option value="P11">Phase 11: Scaraba / DM</option>
          <option value="P12">Phase 12: Tenda / Lumine</option>
          <option value="P13">Phase 13: Magicant / Mutex</option>
          <option value="P14">Phase 14: Distorter / Robot</option>
          <option value="P15">Phase 15: Endgame / Reboot</option>
          <option value="SYS">System / Kernel</option>
        </select>
      </div>

      <!-- Resource List -->
      <div id="resource-list" class="flex-1 overflow-y-auto divide-y divide-slate-800/60">
        <!-- Rendered dynamically -->
      </div>
    </aside>

    <!-- Center/Right Stage: Resource Inspector -->
    <main class="flex-1 flex flex-col bg-slate-950 overflow-hidden">

      <!-- Breadcrumb & Header Bar -->
      <div id="inspector-header" class="bg-slate-900/60 border-b border-slate-800 px-6 py-3 shrink-0 flex flex-wrap items-center justify-between gap-3">
        <div>
          <div class="flex items-center gap-2 mb-1">
            <span id="badge-phase" class="text-[10px] font-mono px-2 py-0.5 rounded bg-indigo-950 text-indigo-300 border border-indigo-800">
              Phase 04
            </span>
            <span id="badge-file" class="text-[10px] font-mono text-slate-400">
              cow_onett.ccs
            </span>
          </div>
          <h2 id="inspector-title" class="text-base font-bold text-white font-mono flex items-center gap-2">
            cow_mom_initial_awakening
          </h2>
          <p id="inspector-comment" class="text-xs text-slate-400 mt-0.5">
            P4-01: Mom Initial Awakening (Ness in Jammies, Flag 0x1d5 Unset)
          </p>
        </div>

        <!-- Action / Metadata Chips -->
        <div id="inspector-chips" class="flex flex-wrap items-center gap-1.5 text-xs">
          <!-- Bound NPC / Flag / Hook Badges -->
        </div>
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
            <span>💻</span> CCScript Source
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

        <!-- TAB 1: SNES EarthBound Dialogue Preview -->
        <div id="panel-dialogue" class="max-w-3xl mx-auto space-y-6">
          
          <!-- Authentic SNES Dialogue Window -->
          <div class="eb-box p-6 min-h-[180px] flex flex-col justify-between shadow-2xl relative select-none">
            <div id="eb-dialogue-content" class="eb-text text-lg whitespace-pre-line tracking-wide">
              @Why does looking at you feel like dereferencing an uninitialized pointer?
            </div>
            
            <div class="flex items-center justify-between mt-4 pt-2 border-t border-slate-700/50 text-xs">
              <div id="eb-sound-cue" class="text-indigo-400 font-mono text-[11px] flex items-center gap-1">
                <!-- Sound cue if any -->
              </div>
              <div class="eb-prompt text-base font-bold select-none cursor-pointer" id="eb-next-prompt">
                ▼
              </div>
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
            <!-- Left: Vanilla Dialogue -->
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

            <!-- Right: Zero Fault CoW Dialogue -->
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

        <!-- TAB 3: CCScript Source Code -->
        <div id="panel-source" class="max-w-4xl mx-auto space-y-4 hidden">
          <div class="flex items-center justify-between">
            <span class="text-xs font-mono text-slate-400" id="source-filename">src/ccscript/cow_onett.ccs</span>
            <button id="btn-copy-code" class="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-xs border border-slate-700 rounded text-slate-300 transition">
              Copy CCScript
            </button>
          </div>
          <pre id="raw-code-block" class="bg-slate-900 border border-slate-800 rounded-lg p-4 font-mono text-xs text-indigo-200 overflow-x-auto whitespace-pre leading-relaxed select-text shadow-inner">
          </pre>
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
                <!-- Flags set / checked -->
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
                <!-- NPC / Trampoline -->
              </div>
            </div>

          </div>
        </div>

      </div>

    </main>

  </div>

  <script>
    const DATA = {data_json};
    let activeIndex = 0;
    let activePage = 0;
    let currentFilteredRoutines = DATA.routines;
    let currentNavMode = 'story'; // story, npcs, enemies, items
    let sfxEnabled = true;
    let autoStepTimer = null;

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

    // Switch Nav Tabs
    function setNavMode(mode) {{
      currentNavMode = mode;
      ['story', 'npcs', 'enemies', 'items'].forEach(m => {{
        const btn = document.getElementById('tab-nav-' + m);
        if (m === mode) {{
          btn.className = 'py-1 px-1.5 rounded bg-indigo-600 text-white shadow font-semibold';
        }} else {{
          btn.className = 'py-1 px-1.5 rounded hover:text-white hover:bg-slate-800';
        }}
      }});
      renderResourceList();
    }}

    // Render Resource List based on mode and search
    function renderResourceList() {{
      const query = document.getElementById('search-input').value.toLowerCase().trim();
      const phaseFilter = document.getElementById('phase-filter-select').value;
      const listContainer = document.getElementById('resource-list');
      listContainer.innerHTML = '';

      if (currentNavMode === 'story') {{
        currentFilteredRoutines = DATA.routines.filter(r => {{
          if (phaseFilter !== 'ALL' && r.phase_id !== phaseFilter) return false;
          if (!query) return true;
          return r.label.toLowerCase().includes(query) ||
                 r.comment.toLowerCase().includes(query) ||
                 r.clean_pages.some(p => p.toLowerCase().includes(query)) ||
                 (r.bound_npc && r.bound_npc.desc && r.bound_npc.desc.toLowerCase().includes(query));
        }});

        document.getElementById('list-count-badge').textContent = `${{currentFilteredRoutines.length}} routines`;

        currentFilteredRoutines.forEach((r) => {{
          const item = document.createElement('div');
          const isSelected = r.id === (DATA.routines[activeIndex] ? DATA.routines[activeIndex].id : null);
          item.className = `p-3 cursor-pointer transition border-l-2 ${{
            isSelected ? 'bg-indigo-950/60 border-indigo-500 text-white' : 'hover:bg-slate-800/60 border-transparent text-slate-300'
          }}`;
          
          item.innerHTML = `
            <div class="flex items-center justify-between gap-1 mb-1">
              <span class="text-[10px] font-mono px-1.5 py-0.2 rounded bg-slate-800 text-indigo-300 font-semibold">
                ${{r.phase_id}}
              </span>
              <span class="text-[10px] text-slate-500 font-mono">${{r.page_count}} pg</span>
            </div>
            <div class="font-mono text-xs font-bold truncate text-slate-100">${{r.label}}</div>
            <div class="text-[11px] text-slate-400 line-clamp-1 mt-0.5">${{r.dialogue_preview}}</div>
            ${{r.bound_npc ? `<div class="text-[10px] text-emerald-400 mt-1 font-mono truncate">👤 ${{r.bound_npc.desc}}</div>` : ''}}
          `;

          item.addEventListener('click', () => {{
            playBeep(480, 'sine', 0.03);
            selectRoutineById(r.id);
          }});

          listContainer.appendChild(item);
        }});

      }} else if (currentNavMode === 'npcs') {{
        const filteredNpcs = DATA.npcs.filter(n => {{
          if (!query) return n.is_cow;
          return String(n.id).includes(query) || 
                 n.desc.toLowerCase().includes(query) ||
                 n.pointer_1.toLowerCase().includes(query) ||
                 n.pointer_2.toLowerCase().includes(query);
        }});

        document.getElementById('list-count-badge').textContent = `${{filteredNpcs.length}} NPCs`;

        filteredNpcs.forEach(n => {{
          const item = document.createElement('div');
          item.className = 'p-3 hover:bg-slate-800/60 cursor-pointer border-l-2 border-transparent text-slate-300';
          item.innerHTML = `
            <div class="flex items-center justify-between mb-1">
              <span class="font-mono text-[10px] text-slate-400">NPC #${{n.id}}</span>
              ${{n.is_cow ? '<span class="text-[10px] px-1 bg-emerald-900/80 text-emerald-300 rounded font-semibold font-mono">CoW Active</span>' : '<span class="text-[10px] text-slate-600">Vanilla</span>'}}
            </div>
            <div class="text-xs font-bold text-white truncate">${{n.desc}}</div>
            <div class="text-[11px] font-mono text-slate-400 mt-0.5 truncate">
              Ptr: <span class="text-indigo-400">${{n.pointer_1}}</span>
            </div>
          `;
          item.addEventListener('click', () => {{
            playBeep(520, 'square', 0.04);
            if (n.cow_routine_id) {{
              const target = n.cow_routine_id.includes('.') ? n.cow_routine_id : n.cow_routine_id;
              selectRoutineById(target);
            }} else {{
              alert(`NPC #${{n.id}}\\nDirection: ${{n.direction}}\\nSprite: ${{n.sprite}}\\nFlag: ${{n.event_flag}}\\nText Pointer 1: ${{n.pointer_1}}\\nText Pointer 2: ${{n.pointer_2}}`);
            }}
          }});
          listContainer.appendChild(item);
        }});

      }} else if (currentNavMode === 'enemies') {{
        const filteredEnemies = DATA.enemies.filter(e => {{
          if (!query) return e.is_thematic;
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
            showEnemyModal(e);
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
            showItemModal(i);
          }});
          listContainer.appendChild(item);
        }});
      }}
    }}

    function selectRoutineById(id) {{
      const idx = DATA.routines.findIndex(r => r.id === id || r.label === id || r.id.endsWith('.' + id));
      if (idx !== -1) {{
        activeIndex = idx;
        activePage = 0;
        updateInspector();
        renderResourceList();
      }}
    }}

    function updateInspector() {{
      const r = DATA.routines[activeIndex];
      if (!r) return;

      document.getElementById('badge-phase').textContent = `${{r.phase_id}} - ${{r.phase_title}}`;
      document.getElementById('badge-file').textContent = r.file;
      document.getElementById('inspector-title').textContent = r.label;
      document.getElementById('inspector-comment').textContent = r.comment || '(No inline comment)';

      // Chips
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

      // Dialogue Page
      updateDialoguePage();

      // Diff
      document.getElementById('diff-vanilla-target').textContent = r.vanilla_mod ? `${{r.vanilla_mod}}:${{r.vanilla_lbl}}` : 'No legacy override';
      document.getElementById('diff-vanilla-text').textContent = r.vanilla_clean || '(Pristine legacy EarthBound dialogue not directly linked or unchanged in this subroutine)';
      document.getElementById('diff-cow-target').textContent = r.id;
      document.getElementById('diff-cow-text').textContent = r.clean_pages.length > 0 ? r.clean_pages.join('\\n\\n') : r.raw_code;

      // Source
      document.getElementById('source-filename').textContent = `src/ccscript/${{r.file}} : ${{r.label}}`;
      document.getElementById('raw-code-block').textContent = r.raw_code;

      // System
      const flagsBox = document.getElementById('sys-flags-box');
      flagsBox.innerHTML = `
        <div><span class="text-slate-500">Flags Set:</span> <span class="text-emerald-400">${{r.flags_set.join(', ') || 'None'}}</span></div>
        <div><span class="text-slate-500">Flags Checked:</span> <span class="text-amber-400">${{r.flags_checked.join(', ') || 'None'}}</span></div>
        <div><span class="text-slate-500">Audio Cues:</span> <span class="text-indigo-400">${{r.sound_cues.join(', ') || 'None'}}</span></div>
      `;

      const dispatchBox = document.getElementById('sys-dispatch-box');
      dispatchBox.innerHTML = `
        <div><span class="text-slate-500">Bound NPC:</span> <span class="text-emerald-400">${{r.bound_npc ? r.bound_npc.desc : 'None'}}</span></div>
        <div><span class="text-slate-500">ROM Hook:</span> <span class="text-purple-400">${{r.bound_hook ? r.bound_hook.desc + ' (' + r.bound_hook.offset + ')' : 'None'}}</span></div>
        <div><span class="text-slate-500">Vanilla Target:</span> <span class="text-amber-400">${{r.vanilla_lbl ? r.vanilla_mod + ' : ' + r.vanilla_lbl : 'None'}}</span></div>
      `;

      // Render all pages list
      const allPagesList = document.getElementById('all-pages-list');
      allPagesList.innerHTML = '';
      r.clean_pages.forEach((p, pidx) => {{
        const pBox = document.createElement('div');
        pBox.className = 'eb-box p-3 text-sm text-slate-100 font-mono';
        pBox.innerHTML = `<span class="text-xs text-indigo-400 block mb-1">Page ${{pidx + 1}}</span>${{p}}`;
        allPagesList.appendChild(pBox);
      }});
    }}

    function updateDialoguePage() {{
      const r = DATA.routines[activeIndex];
      if (!r) return;

      const total = r.clean_pages.length;
      document.getElementById('page-counter-badge').textContent = `Page ${{total > 0 ? activePage + 1 : 0}} of ${{total}}`;
      document.getElementById('btn-prev-page').disabled = activePage <= 0;
      document.getElementById('btn-next-page').disabled = activePage >= total - 1;

      const contentBox = document.getElementById('eb-dialogue-content');
      if (total === 0) {{
        contentBox.textContent = '(This routine contains execution logic or jump commands rather than direct player dialogue.)';
        document.getElementById('eb-sound-cue').textContent = '';
        return;
      }}

      contentBox.textContent = r.clean_pages[activePage] || '';
      const cue = r.sound_cues[activePage] || r.sound_cues[0] || '';
      document.getElementById('eb-sound-cue').textContent = cue ? `🔊 ${{cue}}` : '';
    }}

    function showEnemyModal(e) {{
      alert(`Enemy: ${{e.name}}\\nHP: ${{e.hp}} | PP: ${{e.pp}} | Offense: ${{e.offense}} | Defense: ${{e.defense}}\\nExp: ${{e.exp}} | Money: $${{e.money}}\\nDropped: ${{e.dropped_item}}\\nBoss: ${{e.boss ? 'YES' : 'NO'}}`);
    }}

    function showItemModal(i) {{
      alert(`Item: ${{i.name}}\\nCost: ${{i.cost ? '$' + i.cost : 'Key Item'}}\\nFlags: ${{i.flags.join(', ')}}`);
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
      const r = DATA.routines[activeIndex];
      if (r && activePage < r.clean_pages.length - 1) {{
        activePage++;
        playBeep(640, 'square', 0.03);
        updateDialoguePage();
      }}
    }});

    document.getElementById('eb-next-prompt').addEventListener('click', () => {{
      const r = DATA.routines[activeIndex];
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
          const r = DATA.routines[activeIndex];
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

    // Copy Code Button
    document.getElementById('btn-copy-code').addEventListener('click', () => {{
      const r = DATA.routines[activeIndex];
      if (r) {{
        navigator.clipboard.writeText(r.raw_code);
        const btn = document.getElementById('btn-copy-code');
        btn.textContent = 'Copied!';
        setTimeout(() => {{ btn.textContent = 'Copy CCScript'; }}, 1500);
      }}
    }});

    // Sound Toggle
    document.getElementById('toggle-sound-btn').addEventListener('click', () => {{
      sfxEnabled = !sfxEnabled;
      document.getElementById('sfx-status').textContent = sfxEnabled ? 'ON' : 'OFF';
      document.getElementById('sfx-status').className = sfxEnabled ? 'text-emerald-400 font-semibold' : 'text-slate-500 font-semibold';
      if (sfxEnabled) playBeep(880, 'sine', 0.05);
    }});

    // Search and Filters
    document.getElementById('search-input').addEventListener('input', (e) => {{
      document.getElementById('clear-search-btn').classList.toggle('hidden', !e.target.value);
      renderResourceList();
    }});

    document.getElementById('clear-search-btn').addEventListener('click', () => {{
      document.getElementById('search-input').value = '';
      document.getElementById('clear-search-btn').classList.add('hidden');
      renderResourceList();
    }});

    document.getElementById('phase-filter-select').addEventListener('change', () => {{
      renderResourceList();
    }});

    // Nav Mode Switcher
    ['story', 'npcs', 'enemies', 'items'].forEach(m => {{
      document.getElementById('tab-nav-' + m).addEventListener('click', () => setNavMode(m));
    }});

    // Initial Load
    renderResourceList();
    updateInspector();
  </script>
</body>
</html>
"""
    return html


def run_cli_search(query: str, data: Dict[str, Any]):
    """Search dialogues from the command line."""
    query = query.lower()
    matches = []
    for r in data["routines"]:
        for p_idx, page in enumerate(r["clean_pages"]):
            if query in page.lower():
                matches.append((r, p_idx + 1, page))
    
    print(f"\nSearch results for '{query}' ({len(matches)} match(es)):\n" + "=" * 60)
    for r, p_num, text in matches:
        print(f"\n\033[1;36m[{r['file']}] {r['label']}\033[0m (Page {p_num}) - \033[33m{r['phase_id']}\033[0m")
        if r.get("bound_npc"):
            print(f"  \033[32mNPC:\033[0m {r['bound_npc']['desc']}")
        print(f"  \033[37m{text}\033[0m")
    print("\n" + "=" * 60)


def start_server(html_path: Path, port: int = 8765):
    """Serve the companion app locally and open default browser."""
    os.chdir(html_path.parent)
    handler = http.server.SimpleHTTPRequestHandler
    
    with socketserver.TCPServer(("", port), handler) as httpd:
        url = f"http://localhost:{port}/{html_path.name}"
        print(f"\n========================================================")
        print(f"  EarthBound: Zero Fault - Companion Server Running")
        print(f"  URL: {url}")
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
    parser = argparse.ArgumentParser(description="EarthBound: Zero Fault - Text & Script Explorer")
    parser.add_argument("--search", "-s", type=str, help="Search dialogue directly from CLI")
    parser.add_argument("--build", "-b", action="store_true", help="Rebuild HTML application without launching")
    parser.add_argument("--serve", action="store_true", help="Run local HTTP server and open browser")
    parser.add_argument("--port", "-p", type=int, default=8765, help="Server port (default: 8765)")
    args = parser.parse_args()

    data = build_companion_data()

    if args.search:
        run_cli_search(args.search, data)
        return

    html_content = generate_html_application(data)
    target_path = REPO_ROOT / "tools" / "zero_fault_companion.html"
    target_path.write_text(html_content, encoding="utf-8")
    print(f"Saved standalone companion application: {target_path} ({len(html_content)/1024:.1f} KB)")

    if args.serve or not args.build:
        if args.serve:
            start_server(target_path, args.port)
        else:
            print(f"Opening {target_path} in default browser...")
            try:
                subprocess.run(["xdg-open", str(target_path)], check=False)
            except Exception:
                webbrowser.open(f"file://{target_path}")


if __name__ == "__main__":
    main()
