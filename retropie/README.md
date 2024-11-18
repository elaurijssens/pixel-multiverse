## Pixel Multiverse Service for RetroPie

The **Pixel Multiverse** project provides a daemon and utilities for managing LED matrix displays and illuminated buttons on a RetroPie-based arcadesudo -i
machine.

### Components

1. **Installer (`install.sh`)**
   - Installs the service and its dependencies.
   - Clones the `visuals` repository for display assets.
   - Sets up the systemd service.
   - Ensures necessary permissions.

2. **Service (`service.py`)**
   - Runs as a daemon to listen for events via a Unix socket.
   - Handles display and button actions based on configured events.

3. **Settings (`pixel-multiverse.yml`)**
   - Configuration for the service.
   - Includes logging, display, and button settings.

4. **Event Script (`esscript.py`)**
   - Allows event triggering via symbolic links.
   - Generates JSON payloads based on script arguments and sends them to the service.

5. **Dependencies (`requirements.txt`)**
   - Specifies required Python libraries.

---

### Installation

1. Clone the repository or copy the files to your system.
2. Run the installer script:

   ```bash
   sudo bash install.sh
   ```

   The installer performs the following:
   - Creates necessary directories under `/opt/pixel-multiverse`.
   - Sets up a Python virtual environment and installs dependencies (`requirements.txt`).
   - Clones the `visuals` repository for assets.
   - Copies configuration files (e.g., `pixel-multiverse.yml`).
   - Installs the systemd service and starts it.

3. Verify the service is running:

   ```bash
   sudo systemctl status pixel-multiverse
   ```

---

### Configuration (`pixel-multiverse.yml`)

Located at `/opt/pixel-multiverse/pixel-multiverse.yml`, this file controls the behavior of the service.

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
  image_path: /opt/pixel-multiverse/visuals/marquee
  image_extensions:
    - gif
    - png
    - jpg
  create_placeholders: True
  default_image: /opt/pixel-multiverse/default.png
buttons:
  enabled: True
  connection: /dev/plasmabuttons
  map_path: /opt/pixel-multiverse/visuals/buttons
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

The script is symlinked from directories under `~/.emulationstation/scripts/<event_name>/`. When executed, it determines the event name from the symlink's directory and sends the appropriate JSON payload to the service.

#### Example Usage

1. Create a symlink for an event:

   ```bash
   ln -s /opt/pixel-multiverse/esscript.py ~/.emulationstation/scripts/game-start/script.sh
   ```

2. Execute the script with arguments:

   ```bash
   ~/.emulationstation/scripts/game-start/script.sh "system_name" "rom_path" "game_name" "access_type"
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

The service runs under `systemd` and listens on a Unix socket (`/tmp/pixel_multiverse.sock`) for events.

- **Service Name**: `pixel-multiverse`
- **Systemd Unit File**:
  Installed to `/etc/systemd/system/pixel-multiverse.service`.

#### Commands

- **Start the Service**:
  ```bash
  sudo systemctl start pixel-multiverse
  ```

- **Stop the Service**:
  ```bash
  sudo systemctl stop pixel-multiverse
  ```

- **View Logs**:
  ```bash
  journalctl -u pixel-multiverse
  ```

---

### Troubleshooting

1. **Service Fails to Start**:
   - Check the logs: `journalctl -xe`.
   - Verify the configuration file syntax and paths.

2. **Event Script Errors**:
   - Ensure symlinks are correctly created.
   - Verify arguments passed to the script.

3. **Display Issues**:
   - Confirm the serial connection and settings in `pixel-multiverse.yml`.

