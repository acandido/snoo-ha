# Snoo Premium for Home Assistant

A custom Home Assistant integration that replicates **all** Snoo Premium subscription features, including those behind the $19.99/month paywall. Comes with a custom Lovelace card that mimics the Snoo iOS app.

## Features

### All Official Integration Features (free tier)
- Real-time state monitoring (Baseline, Level 1-4, Timeout, etc.)
- Level control (set intensity)
- Level Lock (hold at current level)
- Sleepytime Sounds
- Start/Stop button
- Safety clip status
- Event monitoring (cry, command, safety clip changes, etc.)

### Premium Features (normally $19.99/month)
- **Weaning Mode** - Stops baseline rocking; baby only gets motion when crying
- **Motion Limiter** - Caps motion at Level 2 (sound still goes to Level 4)
- **Car Ride Mode** - Extra bouncing to mimic a car ride
- **Responsiveness** - Normal or Increased sensitivity to fussing
- **Motion Start Level** - Set a higher starting baseline (Baseline, Level 1, or Level 2)
- **Session Duration** - Real-time session timer

### Custom Dashboard Card
- Mobile-friendly dark UI mimicking the Snoo iOS app
- Color-coded circular level indicator (Blue/Purple/Green/Yellow/Red)
- Touch-friendly level controls
- Status badges for active modes (M/W/C)
- Tap toggles for all premium settings

## Installation

### Option 1: HACS (Recommended)

1. Open HACS in your Home Assistant instance
2. Click the three dots menu (top right) > **Custom repositories**
3. Add this repository URL: `https://github.com/acandido/snoo-ha`
4. Category: **Integration**
5. Click **Add**
6. Search for "Snoo Premium" in HACS and install it
7. Restart Home Assistant

### Option 2: Manual Installation

1. Copy the `custom_components/snoo_premium` folder to your Home Assistant `config/custom_components/` directory:

```bash
# If you have SSH/terminal access:
cd /config
mkdir -p custom_components
cp -r /path/to/snoo-ha/custom_components/snoo_premium custom_components/
```

2. Copy the dashboard card:
```bash
cp /path/to/snoo-ha/www/snoo-card.js /config/www/
```

3. Restart Home Assistant

## Setup

### 1. Disable the Official Snoo Integration (if installed)

Since this integration replaces the official one, you should disable it first:

1. Go to **Settings > Devices & Services**
2. Find "Happiest Baby Snoo"
3. Click the three dots > **Disable**

### 2. Add Snoo Premium Integration

1. Go to **Settings > Devices & Services**
2. Click **+ Add Integration**
3. Search for "Snoo Premium"
4. Enter your Happiest Baby email and password
5. The integration will discover your Snoo device(s) automatically

### 3. Install the Dashboard Card

1. Go to **Settings > Dashboards > Resources** (or the three-dot menu > Resources)
2. Click **+ Add Resource**
3. URL: `/local/snoo-card.js`
4. Resource type: **JavaScript Module**
5. Click **Create**

### 4. Add the Dashboard

**Option A: Use the custom card (recommended)**

1. Go to your dashboard
2. Click the pencil icon (edit mode)
3. Click **+ Add Card**
4. Scroll to the bottom and select **Manual** (YAML)
5. Paste:
```yaml
type: custom:snoo-card
```

**Option B: Import the full dashboard**

1. Go to **Settings > Dashboards**
2. Click **+ Add Dashboard**
3. Choose **YAML** mode
4. Point it to the `dashboard/snoo-dashboard.yaml` file, or paste its contents

**Option C: Use native HA entity cards (no custom JS needed)**

If you prefer not to use the custom card, all entities work with standard HA cards:

```yaml
type: entities
title: Snoo Controls
entities:
  - entity: sensor.snoo_premium_state
  - entity: sensor.snoo_premium_session_duration
  - entity: select.snoo_premium_intensity
  - entity: switch.snoo_premium_hold
  - entity: button.snoo_premium_start
  - type: divider
  - entity: switch.snoo_premium_motion_limiter
  - entity: switch.snoo_premium_weaning
  - entity: switch.snoo_premium_car_ride_mode
  - entity: switch.snoo_premium_sticky_white_noise
  - type: divider
  - entity: select.snoo_premium_responsiveness
  - entity: select.snoo_premium_motion_start_level
  - type: divider
  - entity: binary_sensor.snoo_premium_left_clip
  - entity: binary_sensor.snoo_premium_right_clip
```

## Entities Created

| Entity | Type | Description |
|--------|------|-------------|
| `sensor.snoo_premium_state` | Sensor | Current state (baseline, level1-4, stop, etc.) |
| `sensor.snoo_premium_time_left` | Sensor | Time left on current level timer |
| `sensor.snoo_premium_session_duration` | Sensor | Current session duration (H:MM:SS) |
| `select.snoo_premium_intensity` | Select | Set soothing level |
| `select.snoo_premium_responsiveness` | Select | Normal or Increased responsiveness |
| `select.snoo_premium_motion_start_level` | Select | Starting motion level |
| `switch.snoo_premium_hold` | Switch | Level lock (cruise control) |
| `switch.snoo_premium_sticky_white_noise` | Switch | Sleepytime sounds |
| `switch.snoo_premium_motion_limiter` | Switch | Motion limiter |
| `switch.snoo_premium_car_ride_mode` | Switch | Car ride mode |
| `switch.snoo_premium_weaning` | Switch | Weaning mode |
| `button.snoo_premium_start` | Button | Start the Snoo |
| `binary_sensor.snoo_premium_left_clip` | Binary Sensor | Left safety clip status |
| `binary_sensor.snoo_premium_right_clip` | Binary Sensor | Right safety clip status |
| `event.snoo_premium_event` | Event | Snoo events (cry, command, etc.) |

## Automation Examples

### Night light when baby wakes
```yaml
automation:
  - alias: "Snoo - Baby woke up"
    trigger:
      - platform: state
        entity_id: sensor.snoo_premium_state
        to: "timeout"
    condition:
      - condition: time
        after: "19:00:00"
        before: "07:00:00"
    action:
      - service: light.turn_on
        target:
          entity_id: light.nursery
        data:
          brightness: 30
          color_temp: 500
```

### Notification when Snoo reaches Level 4
```yaml
automation:
  - alias: "Snoo - Level 4 Alert"
    trigger:
      - platform: state
        entity_id: sensor.snoo_premium_state
        to: "level4"
    action:
      - service: notify.mobile_app
        data:
          title: "Snoo Alert"
          message: "Baby has reached Level 4 soothing"
```

## How It Works

This integration uses the same `python-snoo` library as the official HA integration for real-time MQTT state updates and commands. For premium settings (motion limiter, car ride mode, responsiveness, etc.), it makes direct REST API calls to the Happiest Baby API -- the same endpoints the iOS/Android app uses.

**Important:** You use your existing Happiest Baby account credentials. The integration communicates with Happiest Baby's cloud servers (AWS) for authentication and control, just like the official app.

## File Structure

```
snoo-ha/
├── custom_components/
│   └── snoo_premium/
│       ├── __init__.py          # Integration setup
│       ├── api.py               # Direct REST API for premium settings
│       ├── binary_sensor.py     # Safety clip sensors
│       ├── button.py            # Start button
│       ├── config_flow.py       # UI configuration
│       ├── const.py             # Constants and API URLs
│       ├── coordinator.py       # Data coordinator
│       ├── entity.py            # Base entity class
│       ├── event.py             # Event entity
│       ├── manifest.json        # Integration manifest
│       ├── select.py            # Intensity, responsiveness, start level
│       ├── sensor.py            # State, time left, session duration
│       ├── strings.json         # Entity names and translations
│       └── switch.py            # All toggle switches
├── www/
│   └── snoo-card.js             # Custom Lovelace card
├── dashboard/
│   └── snoo-dashboard.yaml      # Example dashboard
├── hacs.json                    # HACS metadata
├── LICENSE
└── README.md
```

## Troubleshooting

**"Premium settings show as unavailable"**
- The integration needs your baby's ID to read/write settings. If you have multiple babies configured, it uses the first one. Check the HA logs for errors.

**"Entity names don't match what's in this README"**
- Entity IDs are based on your device name. If your Snoo is named "Baby's Snoo", entities will be like `sensor.baby_s_snoo_state`. The README uses `snoo_premium_` as a generic prefix.

**"I still have the official Snoo integration"**
- You can run both simultaneously, but they'll create duplicate entities. Disable the official one under Settings > Devices & Services.

**"Settings changes don't take effect"**
- Premium settings (motion limiter, weaning, car ride mode, responsiveness, start level) are sent to the Happiest Baby cloud API. There may be a few seconds of delay before the Snoo acknowledges the change.

## Credits

- [python-snoo](https://github.com/Lash-L/python-snoo) by Lash-L - The underlying Python library
- [Official Snoo HA Integration](https://www.home-assistant.io/integrations/snoo/) - Architecture reference
- Happiest Baby / Dr. Harvey Karp - The Snoo hardware and cloud API
