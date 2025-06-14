## Pixel Multiverse Service for Batocera

The **Pixel Multiverse** project provides a daemon and utilities for managing LED matrix displays and illuminated buttons on a RetroPie-based arcade
machine.

### Components

1. **Installer (`install.sh`)**
   - Installs the service and its dependencies.
   - Clones the `visuals` repository for display assets.
   - Sets up the service.
   - Ensures necessary permissions.

2. **Service (`service.py`)**
   - Runs as a daemon to listen for events via a Unix socket.
   - Handles display and button actions based on configured events.

3. **Settings (`pixel_multiverse.yml`)**
   - Configuration for the service.
   - Includes logging, display, and button settings.

4. **Event Script (`esscript.py`)**
   - Allows event triggering via symbolic links.
   - Generates JSON payloads based on script arguments and sends them to the service.

5. **Dependencies (`requirements.txt`)**
   - Specifies required Python libraries.

6. **Init.d Script (`pixel_multiverse.sh`)**
   - Controls the starting and stopping of the service python script.

7. **udev Rules (`99-picoled.rules`)**
   - Create device files for plasma controller, and galactic unicorn.
---

### Installation

1. Clone the repository or copy the files to your system.
2. Run the installer script:

   ```bash
   bash install.sh
   ```

   The installer performs the following:
   - Creates necessary directories under `/userdata/pixel_multiverse`.
   - Sets up a Python virtual environment and installs dependencies (`requirements.txt`).
   - Clones the `visuals` repository for assets.
   - Copies configuration files (e.g., `pixel-multiverse.yml`).
   - Installs the systemd service and starts it.

3. Verify the service is running:

   ```bash
   batocera status pixel_multiverse
   ```

4. Configure the yml for the device, or copy the 99-picoled.rules to /etc/udev/rules, and save the overlay.

---

### Configuration (`pixel_multiverse.yml`)

Located at `/userdata/configs/pixel_multiverse/pixel_multiverse.yml`, this file controls the behavior of the service.

#### Example Configuration

```yaml
general:
  logging:
    level: INFO
marquee:
  enabled: True
  type: i75_128x32
  color_order: GBR
  connection: /dev/i75
  image_path: /userdata/pixel_multiverse/visuals/marquee
  image_extensions:
    - gif
    - png
    - jpg
  create_placeholders: True
  default_image: /userdata/pixel_multiverse/default.png
buttons:
  enabled: True
  connection: /dev/plasmabuttons
  map_path: /userdata/pixel_multiverse/visuals/buttons
  button_map:
    P1:START: 14
    P1:A: 13
    P1:B: 11
    ...
```

- **Marquee Configuration**:
  - `enabled`: Enables/disables the marquee display.
  - `type`: Display type (`i75_128x32` or `galactic_unicorn`).
  - `connection`: Serial port for the display.
  - `image_path`: Directory for visuals.
  - `create_placeholders`: Generate placeholders for missing images.

- **Buttons Configuration**:
  - `enabled`: Enables/disables button illumination.
  - `connection`: Serial port for buttons.
  - `button_map`: Maps buttons to their identifiers.

---

### Event Script (`esscript.py`)

The script is symlinked from directories under `~/configs/emulationstation/scripts/<event_name>/`. When executed, it determines the event name from the
 symlink's directory and sends the appropriate JSON payload to the service.

#### Example Usage

1. Create a symlink for an event:

   ```bash
   ln -s /userdata/pixel_multiverse/esscript.py ~/configs/emulationstation/scripts/game-start/script.sh
   ```

2. Execute the script with arguments:

   ```bash
   ~/configs/emulationstation/scripts/game-start/script.sh "system_name" "rom_path" "game_name" "access_type"
   ```

   Sends the following JSON payload to the service:
   ```json
   {
       "event": "game-start",
       "arguments": {
           "system_name": "system_name",
           "rom_path": "rom_path",
           "game_name": "game_name",
           "access_type": "access_type"
       }
   }
   ```

---

### Requirements

The `requirements.txt` file lists all Python dependencies:

```
pixel-multiverse
PyYAML
pillow
```

These are installed in the virtual environment created by the installer.

---

### Systemd Service

The service runs as a user service and listens on a Unix socket (`/run/pixel_multiverse.sock`) for events.

- **Service Name**: `pixel_multiverse`
- Installed to `~/services/pixel_multiverse`.

#### Commands

- **Start the Service**:
  ```bash
  sudo batocera-services start pixel_multiverse
  ```

- **Stop the Service**:
  ```bash
  sudo batocera-services stop pixel_multiverse
  ```

- **View Logs**:
  ```bash
  more ~/logs/pixel_multiverse.log
  ```

---

### Troubleshooting

1. **Service Fails to Start**:
   - Check the log
   - Verify the configuration file syntax and paths.

2. **Event Script Errors**:
   - Ensure symlinks are correctly created.
   - Verify arguments passed to the script.

3. **Display Issues**:
   - Confirm the serial connection and settings in `pixel_multiverse.yml`.
