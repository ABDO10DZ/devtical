# devtical
![icon](https://raw.githubusercontent.com/ABDO10DZ/devtical/refs/heads/main/icon.ico)

* `main.py` is currently a Python [PySide6](https://wiki.qt.io/Qt_for_Python_PySide) based flash tool (requires [mtkclient](https://github.com/bkerler/mtkclient) / [edl client](https://github.com/bkerler/edl) / [avbtool](https://github.com/jcrutchvt10/AVBTOOL)).
* done : integrated with [SPDClient](https://github.com/ABDO10DZ/spdclient) and [XynClient](https://github.com/ABDO10DZ/XynClient) to create a multifunctional flash utility
* next : Integrated with [ffdm download manager](https://github.com/ABDO10DZ/ffdm) for mass/single automated downloading of firmware ROMs and tools, with auto usage to gain easy, free access for you—no server-side login required
* **Added `minimal-RomScarper.py`:**
  - A new minimal firmware ROM scraper tool for collecting downloadable ROMs from public databases such as [firmwarefile.com].
  - This tool uses respectful scraping techniques, extracting Google Drive, MediaFire, and Mega.nz download links for device firmware.
  - Will be enhanced to support more public firmware websites for broader ROM coverage.
* **Planned Integration:**
  - This minimal scraper will be integrated with `devtical/main.py` and the [ffdm tool](https://github.com/ABDO10DZ/ffdm) for seamless, automated bulk ROM download management.
  - Future updates will add more advanced scraping techniques and support for additional public ROM databases.

# Massive updates are coming

devtical is a toolkit that auto-mass downloads multi-regional ROMs, custom TWRPs, Sec_AUTH bypass, OEM unlock, `file_recovery.sh` (from TWRP root shell/Magisk), and `FRP.txt` aid for FRP bypass for Android/MTK, Qualcomm, SPD, XYN devices.

iPhone A11 - jailbreak/FRP iCloud bypass (auto download/auto exec)

The toolkit is based on physical device access.  
Soon, I hope to add custom boot patches, including computer boot BIOS firmware, phone BROM revive, and other custom patches.

Example of the supposed tree:
```
downloads/
└── xiaomi/
    └── redmi_9a/
        └── android_10/
            └── ui_12/
                ├── ROM/
                │   ├── global/
                │   │   ├── MIUI_12_9A_Global.zip
                │   │   └── frp.txt
                │   └── russian/
                │       └── MIUI_12_9A_RU.zip
                ├── OEM/
                │   └── oem_unlock.bin
                ├── TWRP/
                │   └── twrp_recovery.img
                ├── SEC_AUTH/
                │   └── auth_bypass.elf
                ├── FileRecovery/
                │   └── recover.sh
                └── readme.txt
```
