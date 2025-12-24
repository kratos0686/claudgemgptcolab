# Acer Chromebook R11 (Cyan): Modernization Guide (BalenaEtcher Method)

**Target OS:** ChromeOS (via Brunch Framework)  
**Recovery Image:** rammus (Recommended for Intel Braswell)  
**Tooling:** BalenaEtcher + Linux Mint Cinnamon ISO

**Note:** You must disable hardware Write Protection (WP) to install custom firmware.

## Phase 1: Hardware Preparation (One-Time)

1. **Remove Bottom Cover:** Unscrew the bottom panel of the R11.
2. **Remove WP Screw:** Locate and remove the specific Write Protect screw on the motherboard.
3. **Reassemble:** Replace the cover.

## Phase 2: Firmware Update (MrChromebox)

1. **Developer Mode:** `Esc` + `Refresh` + `Power` -> `Ctrl+D`.
2. **Terminal:** `Ctrl+Alt+T` -> `shell`.
3. **Script:** 

   ```bash
   cd; curl -LO mrchromebox.tech/firmware-util.sh && sudo bash firmware-util.sh
   ```
4. **Action:** Select "Install/Update UEFI (Full ROM) Firmware".
5. **Result:** The device will power off. It is now a standard laptop.

## Phase 3: Creating the Bootable USB

**On your Windows/Mac PC:**

1. **Download:** Get the Linux Mint Cinnamon Edition ISO file.
2. **Open BalenaEtcher:**
   - **Flash from file:** Select the Linux Mint ISO.
   - **Select target:** Select your USB drive.
   - **Flash!:** Wait for it to finish.

**Note:** If Windows asks to "Format" the drive after flashing, **CLICK CANCEL**. Windows just doesn't understand the Linux format.

## Phase 4: Downloading Files & Installing (On the R11)

This is the specific file location workflow.

### Boot Linux Mint:Acer Chromebook R11 (Cyan): Modernization Guide (BalenaEtcher Method)
Target OS: ChromeOS (via Brunch Framework)
Recovery Image: rammus (Recommended for Intel Braswell)
Tooling: BalenaEtcher + Linux Mint Cinnamon ISO

Note: You must disable hardware Write Protection (WP) to install custom firmware.

Phase 1: Hardware Preparation (One-Time)
Remove Bottom Cover: Unscrew the bottom panel of the R11.
Remove WP Screw: Locate and remove the specific Write Protect screw on the motherboard.
Reassemble: Replace the cover.
Phase 2: Firmware Update (MrChromebox)
Developer Mode: Esc + Refresh + Power -> Ctrl+D.
Terminal: Ctrl+Alt+T -> shell.
Script:
cd; curl -LO mrchromebox.tech/firmware-util.sh && sudo bash firmware-util.sh
Action: Select "Install/Update UEFI (Full ROM) Firmware".
Result: The device will power off. It is now a standard laptop.
Phase 3: Creating the Bootable USB
On your Windows/Mac PC:

**Step A: Extract the Brunch tools**
Type this and hit Enter:
Flash from file: Select the Linux Mint ISO.
Select target: Select your USB drive.
Flash!: Wait for it to finish.
Note: If Windows asks to "Format" the drive after flashing, CLICK CANCEL. Windows just doesn't understand the Linux format.

**Step B: Unzip the Recovery Image**
Type this and hit Enter:

Boot Linux Mint:
Insert USB into R11. Power on.
Press Esc (or F2/F12) to select the USB boot option.
Select "Start Linux Mint".
**Step C: Rename the Recovery Image (To make it easy to type)**
Type this and hit Enter:
Download Files (Directly to the R11 RAM):
Open the Firefox browser inside Linux Mint.
Download Brunch (latest stable .tar.gz) from GitHub.
Download ChromeOS Rammus Recovery Image (latest .bin.zip).
**Step D: Identify your Hard Drive**
Type this and hit Enter:
Open the file manager (folder icon on taskbar).
Go to Downloads. You should see your two downloaded files there.
Right-click in the empty white space of the window and choose "Open Terminal Here".
Execute Commands (Step-by-Step):
Step A: Extract the Brunch tools Type this and hit Enter:
**Step E: The Installation Command**
Type this exactly:
Files like chromeos-install.sh will appear in the folder.

Step B: Unzip the Recovery Image Type this and hit Enter:

unzip chromeos_*.zip
A large .bin file will appear.

Step C: Rename the Recovery Image (To make it easy to type) Type this and hit Enter:

mv chromeos_*.bin rammus.bin
Step D: Identify your Hard Drive Type this and hit Enter:

lsblk -e7
Look for the largest drive (usually 14GB or 29GB). It is almost certainly named mmcblk0.

Step E: The Installation Command Type this exactly:

sudo bash chromeos-install.sh -src rammus.bin -dst /dev/mmcblk0
Step F: Confirm

Type yes when asked to proceed.
Wait for the progress bar to complete.
Finish:
Once it says "ChromeOS installed," shut down the R11.
Remove the USB drive.
Power on to start your new ChromeOS.
1. Insert USB into R11. Power on.
2. Press `Esc` (or `F2`/`F12`) to select the USB boot option.
3. Select "Start Linux Mint".

### Connect to Internet:
1. Once the Mint desktop loads, click the network icon (bottom right) and connect to Wi-Fi.

### Download Files (Directly to the R11 RAM):
1. Open the Firefox browser inside Linux Mint.
2. Download **Brunch** (latest stable `.tar.gz`) from GitHub.
3. Download **ChromeOS Rammus Recovery Image** (latest `.bin.zip`).
   - By default, these will save to the `/home/mint/Downloads` folder.

### Open Terminal at the Correct Location:
1. Open the file manager (folder icon on taskbar).
2. Go to **Downloads**. You should see your two downloaded files there.
3. Right-click in the empty white space of the window and choose "Open Terminal Here".

### Execute Commands (Step-by-Step):

**Step A: Extract the Brunch tools**
Type this and hit Enter:
```bash
tar -zxvf brunch_r*.tar.gz
```
Files like `chromeos-install.sh` will appear in the folder.

**Step B: Unzip the Recovery Image**
Type this and hit Enter:
```bash
unzip chromeos_*.zip
```
A large `.bin` file will appear.

**Step C: Rename the Recovery Image (To make it easy to type)**
Type this and hit Enter:
```bash
mv chromeos_*.bin rammus.bin
```

**Step D: Identify your Hard Drive**
Type this and hit Enter:
```bash
lsblk -e7
```
Look for the largest drive (usually 14GB or 29GB). It is almost certainly named `mmcblk0`.

**Step E: The Installation Command**
Type this exactly:
```bash
sudo bash chromeos-install.sh -src rammus.bin -dst /dev/mmcblk0
```

**Step F: Confirm**
1. Type `yes` when asked to proceed.
2. Wait for the progress bar to complete.

### Finish:
1. Once it says "ChromeOS installed," shut down the R11.
2. Remove the USB drive.
3. Power on to start your new ChromeOS.
