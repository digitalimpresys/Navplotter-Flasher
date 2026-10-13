#!/usr/bin/env python3
"""Builds every NavPlotter firmware and prepares the files the web flasher page serves.

For each board: runs PlatformIO in its project, merges boot loader, partition table and application into
one image (firmware/<id>.bin) and writes the manifest ESP Web Tools reads (firmware/<id>.json).
The Pico W is not an ESP board: its .uf2 file is copied as it is, to be dragged onto the RPI-RP2 drive.

Run from anywhere: python3 tools/build.py [--no-build]
"""
import json, os, re, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "firmware")
PROJECTS = os.path.abspath(os.path.join(HERE, "..", ".."))
PIO = os.path.expanduser("~/.platformio/penv/bin/pio")
PY = os.path.expanduser("~/.platformio/penv/bin/python")
ESPTOOL = os.path.expanduser("~/.platformio/packages/tool-esptoolpy/esptool.py")
BOOT_APP0 = os.path.expanduser("~/.platformio/packages/framework-arduinoespressif32/tools/partitions/boot_app0.bin")

# id, name shown on the page, project folder, PlatformIO environment, chip family, chip name for esptool
BOARDS = [
    ("tdeck-plus", "NavPlotter T-Deck Plus", "plotter-tdeck", "T-Deck", "ESP32-S3", "esp32s3"),
    ("heltec-v3-node", "NavPlotter node, Heltec V3", "plotter-tdeck/navplotter-heltec", "heltec_wifi_lora_32_V3", "ESP32-S3", "esp32s3"),
    ("heltec-v2-node", "NavPlotter node, Heltec V2", "plotter-tdeck/navplotter-heltec", "heltec_wifi_lora_32_V2", "ESP32", "esp32"),
    ("heltec-v3-segnalatore", "Segnalatore, Heltec V3", "navplotter-segnalatore", "heltec_wifi_lora_32_V3", "ESP32-S3", "esp32s3"),
    ("heltec-v2-segnalatore", "Segnalatore, Heltec V2", "navplotter-segnalatore", "heltec_wifi_lora_32_V2", "ESP32", "esp32"),
    ("esp32-32e", "NavPlotter ESP32-32E", "navplotter-esp32-32e", "esp32-32e", "ESP32", "esp32"),
    ("waveshare-lcd4", "NavPlotter display, Waveshare LCD 4", "navplotter-waveshare-lcd4", "waveshare-lcd4", "ESP32-S3", "esp32s3"),
]
PICO = ("pico-w", "navplotter-pico-w", "pico-w")


def version_of(project):
    text = open(os.path.join(PROJECTS, project, "src", "main.cpp"), encoding="utf-8", errors="replace").read()
    m = re.search(r'#define\s+(?:FW_VERSION|FIRMWARE_VERSION)\s+"([^"]+)"', text)
    if m:
        return m.group(1)
    # No version in the source: the date of the last commit that touched it
    top = project.split("/")[0]
    date = subprocess.run(["git", "-C", os.path.join(PROJECTS, top), "log", "-1", "--format=%cs"], capture_output=True, text=True).stdout.strip()
    return date or "unknown"


def run(cmd, cwd=None):
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit("FAILED: %s\n%s\n%s" % (" ".join(cmd), r.stdout[-2000:], r.stderr[-2000:]))


def main():
    build = "--no-build" not in sys.argv
    os.makedirs(OUT, exist_ok=True)
    summary = []
    for bid, name, project, env, family, chip in BOARDS:
        pdir = os.path.join(PROJECTS, project)
        if build:
            print("building", project, env, flush=True)
            run([PIO, "run", "-e", env], cwd=pdir)
        bdir = os.path.join(pdir, ".pio", "build", env)
        image = os.path.join(OUT, bid + ".bin")
        # The boot loader sits at 0x1000 on the ESP32 and at 0 on the ESP32-S3
        run([PY, ESPTOOL, "--chip", chip, "merge_bin", "-o", image,
             "0x1000" if chip == "esp32" else "0x0", os.path.join(bdir, "bootloader.bin"),
             "0x8000", os.path.join(bdir, "partitions.bin"),
             "0xe000", BOOT_APP0,
             "0x10000", os.path.join(bdir, "firmware.bin")])
        version = version_of(project)
        manifest = {"name": name, "version": version, "new_install_prompt_erase": True,
                    "builds": [{"chipFamily": family, "parts": [{"path": bid + ".bin", "offset": 0}]}]}
        json.dump(manifest, open(os.path.join(OUT, bid + ".json"), "w"), indent=1)
        summary.append({"id": bid, "name": name, "version": version, "size": os.path.getsize(image)})
        print("  %-24s %-8s %7d bytes" % (bid, version, os.path.getsize(image)), flush=True)

    bid, project, env = PICO
    pdir = os.path.join(PROJECTS, project)
    if build:
        print("building", project, env, flush=True)
        run([PIO, "run", "-e", env], cwd=pdir)
    uf2 = os.path.join(pdir, ".pio", "build", env, "firmware.uf2")
    shutil.copy(uf2, os.path.join(OUT, bid + ".uf2"))
    summary.append({"id": bid, "name": "NavPlotter node, Raspberry Pi Pico W", "version": version_of(project), "size": os.path.getsize(uf2)})
    print("  %-24s %-8s %7d bytes" % (bid, summary[-1]["version"], os.path.getsize(uf2)), flush=True)
    json.dump(summary, open(os.path.join(OUT, "versions.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
