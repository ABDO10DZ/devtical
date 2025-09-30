# devtical
* `main.py` is currently a Python [PySide6](https://wiki.qt.io/Qt_for_Python_PySide) based flash tool (requires [mtkclient](https://github.com/bkerler/mtkclient) / [edl client](https://github.com/bkerler/edl))
* Next, I'll update it to integrate with [SPDClient](https://github.com/ABDO10DZ/spdclient) and [XynClient](https://github.com/ABDO10DZ/XynClient) to create a multifunctional flash utility
* Integrated with [ffdm download manager](https://github.com/ABDO10DZ/ffdm) for mass/single automated downloading of firmware ROMs and tools, with auto usage to gain easy, free access for you—no need for Hydra or other paid/kiddy tools on the market anymore. Everything they can do you'll be able to do with **one click**.

# Massive updates are coming

devtical is a toolkit that auto-mass downloads multi-regional ROMs, custom TWRPs, Sec_AUTH bypass, OEM unlock, `file_recovery.sh` (from TWRP root shell/Magisk), and `FRP.txt` aid for FRP bypass for a specific device—**all-in-one** with the ability to auto flash/patch through ADB (required).

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
