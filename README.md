# i-ON40 Alarm Panel — Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![Validate](https://github.com/nvvliet/ION-console/actions/workflows/validate.yml/badge.svg)](https://github.com/nvvliet/ION-console/actions/workflows/validate.yml)

A custom integration that polls the keypad web interface (`keypad.cgx`) and
lets you send key presses (also via `keypad.cgx` — see **Protocol notes**
below) from Home Assistant.

## What it does

- **Sensor: Display** — the current keypad display text (all `<text>` lines joined).
  Each line is also available individually in the `lines` attribute (keyed by
  `rtm500`, `rtm501`, etc.).
- **Sensor: Alarm Status** — `ok`, `alarm`, or `unknown`, derived from the
  `<bgcol>` nav-key colour. Raw colour and the raw LED bitmask are exposed as
  attributes.
- **Binary sensors: Zone A–D** — one per zone, decoded from the `vkleds`
  bitmask (2 bits per zone). See **Remaining assumptions** below — you'll likely want
  to tune the on/off logic once you've seen real values.
- **Services**:
  - `ion40_alarm.send_key` — send a single key.
  - `ion40_alarm.send_keys` — send a sequence of keys (e.g. a PIN + accept),
    with a configurable delay between presses.

## Install

### Via HACS (recommended)

This repo isn't in the default HACS store, so add it as a custom repository:

1. In Home Assistant, open **HACS → Integrations**.
2. Click the **⋮** menu (top right) → **Custom repositories**.
3. Add your repo URL (e.g. `https://github.com/nvvliet/ION-console`),
   set the category to **Integration**, and click **Add**.
4. Find "i-ON40 Alarm Panel" in HACS and click **Download**.
5. Restart Home Assistant.
6. Go to **Settings → Devices & Services → Add Integration**, search for
   "i-ON40 Alarm Panel", and enter the panel's IP/host, port (default 80),
   and desired polling interval (default 5s).

Once installed via HACS, updates show up automatically when you push new
tagged releases to the repo.

### Manual

1. Copy the `custom_components/ion40_alarm` folder into your Home
   Assistant `config/custom_components/` directory, so you end up with:
   ```
   config/custom_components/ion40_alarm/__init__.py
   config/custom_components/ion40_alarm/manifest.json
   ...
   ```
2. Restart Home Assistant.
3. Go to **Settings → Devices & Services → Add Integration**, search for
   "i-ON40 Alarm Panel", and enter the panel's IP/host, port
   (default 80), and desired polling interval (default 5s).
4. A device with the Display sensor, Alarm Status sensor, and four zone
   binary sensors will be created.

The 5-digit client UID is generated once during setup and stored in the
config entry, so it stays stable across restarts (matching "generated once
per client" in the panel's protocol).

## Using the services

Find your panel's config entry via the device picker in the service call UI
(Developer Tools → Actions → search "i-ON40"). Example to unset/disarm
with a 4-digit PIN:

```yaml
action: ion40_alarm.send_keys
data:
  entry_id: <your entry id>
  keys: ["1", "2", "3", "4", "N"]
  delay: 0.3
```

To operate zone A–D keys, use lowercase: `"a"`, `"b"`, `"c"`, `"d"`
(uppercase `D` is reserved for the nav "Down" key — see below).

## Dashboard

A full example dashboard: a display card with a glowing gradient background,
a nav cluster (arrows + cancel/accept/menu/unset), zone A–D indicators that
turn red when active, and a full keypad grid (numbers + zones A–D).

**Requires [card-mod](https://github.com/thomasloven/lovelace-card-mod)**
(install via HACS → Frontend → search "card-mod") for the display card's
gradient/glow background and the red/gray zone-indicator colouring. The
layout still works without it, just without those visual effects.

### Finding your `entry_id`

Every button below needs your panel's config entry ID in place of
`YOUR_ENTRY_ID`. To find it:

1. Go to **Developer Tools → Actions**.
2. Pick `ion40_alarm.send_key` in the action picker.
3. Select your panel in the **Panel** field.
4. Switch to **YAML mode** (the `</>` icon, top-right of that field/card).
   It will show something like:
   ```yaml
   entry_id: 01HXXXXXXXXXXXXXXXXXXXXX
   key: "1"
   ```
5. Copy that `entry_id` value.

Then either paste it in place of every `YOUR_ENTRY_ID` below, or (easier for
future edits) use your editor's find-and-replace across the whole YAML block
before pasting it into Lovelace.

### Finding your entity IDs

The YAML below uses placeholder entity IDs containing `YOUR_PANEL_ID`, e.g.
`sensor.alarm_panel_YOUR_PANEL_ID_display`,
`sensor.alarm_panel_YOUR_PANEL_ID_alarm_status`, and
`binary_sensor.alarm_panel_YOUR_PANEL_ID_zone_a` (…`_zone_b`, `_zone_c`,
`_zone_d`). `YOUR_PANEL_ID` is a stand-in for whatever Home Assistant
actually slugified your panel's name into (often something derived from its
IP, e.g. `192_168_1_50`, but it depends on the device/config entry name you
gave it) — it is **not** a value you type in verbatim.

To find your real entity IDs:

1. Go to **Developer Tools → States**.
2. In the entity filter box, type `alarm_panel` (or `ion40`).
3. You'll see a list of matching entities — note the exact ID for each:
   - the **Display** sensor (`sensor.alarm_panel_..._display`)
   - the **Alarm Status** sensor (`sensor.alarm_panel_..._alarm_status`)
   - the four **Zone** binary sensors (`binary_sensor.alarm_panel_..._zone_a`
     through `_zone_d`)
4. Find-and-replace every `YOUR_PANEL_ID` in the YAML below with the exact
   segment your entities use (copy it precisely — don't guess the slug).

If your entity IDs don't follow this `alarm_panel_..._display` pattern at
all (e.g. you renamed the device), just replace each full entity ID in the
YAML with the correct one from Developer Tools → States instead.

### YAML

Edit your dashboard → **⋮ → Edit Dashboard → ⋮ → Raw configuration editor**,
and add this as a card:

```yaml
type: vertical-stack
cards:
  - type: markdown
    content: >-
      <div class="led-text">{{states('sensor.alarm_panel_YOUR_PANEL_ID_display'}}</div>
      Status: {{ states('sensor.alarm_panel_YOUR_PANEL_ID_alarm_status') | upper }}
    card_mod:
      style: |
        ha-card {
        /* Glowing LED-style multi-color gradient background */
        background: radial-gradient(circle, #00eecc 0%, #00bbcc 70%, #0099cc 100%);
        box-shadow: 0 0 5px rgba(0, 0, 85, 0.6);
        border: 2px solid #00008b;
        border-radius: 12px;
        padding: 1px;
        white-space: pre-line;
        font-weight: bold;
        font-size: 14pt;
        text-align: center
        }
  - type: horizontal-stack
    cards:
      - square: false
        type: grid
        cards:
          - type: markdown
            content: " "
            text_only: true
          - show_name: false
            show_icon: true
            type: button
            icon: mdi:chevron-up
            tap_action:
              action: call-service
              service: ion40_alarm.send_key
              service_data:
                entry_id: YOUR_ENTRY_ID
                key: U
            card_mod:
              style: |
                :host {
                  {% if states('sensor.alarm_panel_YOUR_PANEL_ID_alarm_status') == 'alarm' %}
                    --paper-item-icon-color: red;
                    --card-mod-icon-color: red;
                     color: red;
                   {% elif states('sensor.alarm_panel_YOUR_PANEL_ID_alarm_status') == 'ok' %}
                    --paper-item-icon-color: #00FF00;
                    --card-mod-icon-color: #00FF00;
                     color: #00FF00;
                  {% else %}
                    --paper-item-icon-color: gray;
                    --card-mod-icon-color: gray;
                    color: gray;
                   {% endif %}
                }    
          - type: markdown
            content: " "
            text_only: true
          - show_name: false
            show_icon: true
            type: button
            icon: mdi:chevron-left
            tap_action:
              action: call-service
              service: ion40_alarm.send_key
              service_data:
                entry_id: YOUR_ENTRY_ID
                key: L
            card_mod:
              style: |
                :host {
                  {% if states('sensor.alarm_panel_YOUR_PANEL_ID_alarm_status') == 'alarm' %}
                    --paper-item-icon-color: red;
                    --card-mod-icon-color: red;
                     color: red;
                   {% elif states('sensor.alarm_panel_YOUR_PANEL_ID_alarm_status') == 'ok' %}
                    --paper-item-icon-color: #00FF00;
                    --card-mod-icon-color: #00FF00;
                     color: #00FF00;
                  {% else %}
                    --paper-item-icon-color: gray;
                    --card-mod-icon-color: gray;
                    color: gray;
                   {% endif %}
                }    
          - show_name: false
            show_icon: true
            type: button
            icon: mdi:checkbox-blank-circle-outline
            name: " "
            tap_action:
              action: none
            card_mod:
              style: |
                :host {
                  {% if states('sensor.alarm_panel_YOUR_PANEL_ID_alarm_status') == 'alarm' %}
                    --paper-item-icon-color: red;
                    --card-mod-icon-color: red;
                     color: red;
                   {% elif states('sensor.alarm_panel_YOUR_PANEL_ID_alarm_status') == 'ok' %}
                    --paper-item-icon-color: #00FF00;
                    --card-mod-icon-color: #00FF00;
                     color: #00FF00;
                  {% else %}
                    --paper-item-icon-color: gray;
                    --card-mod-icon-color: gray;
                    color: gray;
                   {% endif %}
                }    
          - show_name: false
            show_icon: true
            type: button
            icon: mdi:chevron-right
            tap_action:
              action: call-service
              service: ion40_alarm.send_key
              service_data:
                entry_id: YOUR_ENTRY_ID
                key: R
            card_mod:
              style: |
                :host {
                  {% if states('sensor.alarm_panel_YOUR_PANEL_ID_alarm_status') == 'alarm' %}
                    --paper-item-icon-color: red;
                    --card-mod-icon-color: red;
                     color: red;
                   {% elif states('sensor.alarm_panel_YOUR_PANEL_ID_alarm_status') == 'ok' %}
                    --paper-item-icon-color: #00FF00;
                    --card-mod-icon-color: #00FF00;
                     color: #00FF00;
                  {% else %}
                    --paper-item-icon-color: gray;
                    --card-mod-icon-color: gray;
                    color: gray;
                   {% endif %}
                }    
          - type: markdown
            content: " "
            text_only: true
          - show_name: false
            show_icon: true
            type: button
            icon: mdi:chevron-down
            tap_action:
              action: call-service
              service: ion40_alarm.send_key
              service_data:
                entry_id: YOUR_ENTRY_ID
                key: D
            card_mod:
              style: |
                :host {
                  {% if states('sensor.alarm_panel_YOUR_PANEL_ID_alarm_status') == 'alarm' %}
                    --paper-item-icon-color: red;
                    --card-mod-icon-color: red;
                     color: red;
                   {% elif states('sensor.alarm_panel_YOUR_PANEL_ID_alarm_status') == 'ok' %}
                    --paper-item-icon-color: #00FF00;
                    --card-mod-icon-color: #00FF00;
                     color: #00FF00;
                  {% else %}
                    --paper-item-icon-color: gray;
                    --card-mod-icon-color: gray;
                    color: gray;
                   {% endif %}
                }    
          - type: markdown
            content: " "
            text_only: true
        columns: 3
      - type: vertical-stack
        cards:
          - show_name: true
            show_icon: true
            show_state: false
            type: glance
            entities:
              - entity: sensor.alarm_panel_YOUR_PANEL_ID_alarm_status
                name: " "
                card_mod:
                  style: |
                    :host {
                     {% if states('sensor.alarm_panel_YOUR_PANEL_ID_alarm_status') == 'alarm' %}
                       --paper-item-icon-color: red;
                       --card-mod-icon-color: red;
                       --card-mod-icon: mdi:alarm-light;
                        color: red;
                        {% elif states('sensor.alarm_panel_YOUR_PANEL_ID_alarm_status') == 'ok' %}
                       --paper-item-icon-color: #00FF00;
                       --card-mod-icon-color: #00FF00;
                        color: #00FF00;
                       {% else %}
                        --paper-item-icon-color: gray;
                       --card-mod-icon-color: gray;
                       color: gray;
                      {% endif %}
                     }
              - entity: binary_sensor.alarm_panel_YOUR_PANEL_ID_zone_a
                name: A
                icon: mdi:circle-slice-8
                card_mod:
                  style: |
                    :host {
                      {% if states('binary_sensor.alarm_panel_YOUR_PANEL_ID_zone_a') == 'on' %}
                        --paper-item-icon-color: red;
                        --card-mod-icon-color: red;
                        color: red;
                      {% elif states('binary_sensor.alarm_panel_YOUR_PANEL_ID_zone_a') == 'off' %}
                        --paper-item-icon-color: gray;
                        --card-mod-icon-color: gray;
                        color: darkblue;
                      {% else %}
                        --paper-item-icon-color: orange;
                        color: orange;
                      {% endif %}
                    }    
              - entity: binary_sensor.alarm_panel_YOUR_PANEL_ID_zone_b
                name: B
                icon: mdi:circle-slice-8
                card_mod:
                  style: |
                    :host {
                      {% if states('binary_sensor.alarm_panel_YOUR_PANEL_ID_zone_b') == 'on' %}
                        --paper-item-icon-color: red;
                        --card-mod-icon-color: red;
                        color: red;
                      {% elif states('binary_sensor.alarm_panel_YOUR_PANEL_ID_zone_b') == 'off' %}
                        --paper-item-icon-color: gray;
                        --card-mod-icon-color: gray;
                        color: darkblue;
                      {% else %}
                        --paper-item-icon-color: orange;
                        color: orange;
                      {% endif %}
                    }    
              - entity: binary_sensor.alarm_panel_YOUR_PANEL_ID_zone_c
                name: C
                icon: mdi:circle-slice-8
                card_mod:
                  style: |
                    :host {
                      {% if states('binary_sensor.alarm_panel_YOUR_PANEL_ID_zone_c') == 'on' %}
                        --paper-item-icon-color: red;
                        --card-mod-icon-color: red;
                        color: red;
                      {% elif states('binary_sensor.alarm_panel_YOUR_PANEL_ID_zone_c') == 'off' %}
                        --paper-item-icon-color: gray;
                        --card-mod-icon-color: gray;
                        color: darkblue;
                      {% else %}
                        --paper-item-icon-color: orange;
                        color: orange;
                      {% endif %}
                    }    
              - entity: binary_sensor.alarm_panel_YOUR_PANEL_ID_zone_d
                name: D
                icon: mdi:circle-slice-8
                card_mod:
                  style: |
                    :host {
                      {% if states('binary_sensor.alarm_panel_YOUR_PANEL_ID_zone_d') == 'on' %}
                        --paper-item-icon-color: red;
                        --card-mod-icon-color: red;
                        color: red;
                      {% elif states('binary_sensor.alarm_panel_YOUR_PANEL_ID_zone_d') == 'off' %}
                        --paper-item-icon-color: gray;
                        --card-mod-icon-color: gray;
                        color: darkblue;
                      {% else %}
                        --paper-item-icon-color: orange;
                        color: orange;
                      {% endif %}
                    }    
            state_color: true
          - square: true
            type: grid
            columns: 4
            cards:
              - show_name: false
                show_icon: true
                type: button
                icon: mdi:close
                tap_action:
                  action: call-service
                  service: ion40_alarm.send_key
                  service_data:
                    entry_id: YOUR_ENTRY_ID
                    key: X
              - show_name: false
                show_icon: true
                type: button
                icon: mdi:check
                tap_action:
                  action: call-service
                  service: ion40_alarm.send_key
                  service_data:
                    entry_id: YOUR_ENTRY_ID
                    key: T
              - show_name: false
                show_icon: true
                type: button
                icon: mdi:menu
                tap_action:
                  action: call-service
                  service: ion40_alarm.send_key
                  service_data:
                    entry_id: YOUR_ENTRY_ID
                    key: E
              - show_name: false
                show_icon: true
                type: button
                icon: mdi:lock-open-variant
                tap_action:
                  action: call-service
                  service: ion40_alarm.send_key
                  service_data:
                    entry_id: YOUR_ENTRY_ID
                    key: "N"
  - square: false
    type: grid
    cards:
      - type: button
        name: A
        show_state: false
        tap_action:
          action: call-service
          service: ion40_alarm.send_key
          service_data:
            entry_id: YOUR_ENTRY_ID
            key: a
      - type: button
        name: "1"
        show_state: false
        tap_action:
          action: call-service
          service: ion40_alarm.send_key
          service_data:
            entry_id: YOUR_ENTRY_ID
            key: "1"
      - type: button
        name: "2"
        tap_action:
          action: call-service
          service: ion40_alarm.send_key
          service_data:
            entry_id: YOUR_ENTRY_ID
            key: "2"
      - type: button
        name: "3"
        tap_action:
          action: call-service
          service: ion40_alarm.send_key
          service_data:
            entry_id: YOUR_ENTRY_ID
            key: "3"
      - show_name: true
        show_icon: true
        type: button
        name: B
        tap_action:
          action: call-service
          service: ion40_alarm.send_key
          service_data:
            entry_id: YOUR_ENTRY_ID
            key: b
      - type: button
        name: "4"
        tap_action:
          action: call-service
          service: ion40_alarm.send_key
          service_data:
            entry_id: YOUR_ENTRY_ID
            key: "4"
      - type: button
        name: "5"
        tap_action:
          action: call-service
          service: ion40_alarm.send_key
          service_data:
            entry_id: YOUR_ENTRY_ID
            key: "5"
      - type: button
        name: "6"
        tap_action:
          action: call-service
          service: ion40_alarm.send_key
          service_data:
            entry_id: YOUR_ENTRY_ID
            key: "6"
      - show_name: true
        show_icon: true
        type: button
        name: C
        tap_action:
          action: call-service
          service: ion40_alarm.send_key
          service_data:
            entry_id: YOUR_ENTRY_ID
            key: c
      - type: button
        name: "7"
        tap_action:
          action: call-service
          service: ion40_alarm.send_key
          service_data:
            entry_id: YOUR_ENTRY_ID
            key: "7"
      - type: button
        name: "8"
        tap_action:
          action: call-service
          service: ion40_alarm.send_key
          service_data:
            entry_id: YOUR_ENTRY_ID
            key: "8"
      - type: button
        name: "9"
        tap_action:
          action: call-service
          service: ion40_alarm.send_key
          service_data:
            entry_id: YOUR_ENTRY_ID
            key: "9"
      - show_name: true
        show_icon: true
        type: button
        name: D
        tap_action:
          action: call-service
          service: ion40_alarm.send_key
          service_data:
            entry_id: YOUR_ENTRY_ID
            key: d
      - type: button
        name: "*"
        tap_action:
          action: call-service
          service: ion40_alarm.send_key
          service_data:
            entry_id: YOUR_ENTRY_ID
            key: "*"
      - type: button
        name: "0"
        tap_action:
          action: call-service
          service: ion40_alarm.send_key
          service_data:
            entry_id: YOUR_ENTRY_ID
            key: "0"
      - type: button
        name: "#"
        tap_action:
          action: call-service
          service: ion40_alarm.send_key
          service_data:
            entry_id: YOUR_ENTRY_ID
            key: "#"
    columns: 4
```

### About the display card's styling

The display card only styles `ha-card` itself (background gradient, border,
glow) via `card_mod`. It does **not** attempt to style the text/font of the
display value.

The reason: the markdown card's rendered text sits two shadow-roots deep
(`ha-card` → `ha-markdown` → `ha-markdown-element`), and a flat `card_mod:
style: |` string can only reach the first one (`ha-card`) — which is exactly
why the card's background/border/glow apply but text styling doesn't. In
principle card-mod supports piercing further in via a nested-selector `style:`
dict (see [card-mod's README](https://github.com/thomasloven/lovelace-card-mod)
for the `$` shadow-root syntax), but the exact internal element names differ
across Home Assistant frontend versions, which made it unreliable here.

If you want to try it yourself: install card-mod, add `debug_cardmod: true`
to the card's `card_mod:` block, and check your browser console (F12) — it
logs each shadow-root-traversal step, showing you the actual element names
to target in your specific HA version. Alternatively, a
[template card](https://www.home-assistant.io/dashboards/template/) or a
custom `type: custom:...` LED/LCD card from HACS may get you a real
7-segment/LED look more reliably than fighting shadow-DOM boundaries with
card-mod.

## Protocol notes (confirmed from the panel's own web UI)

Comparing against the panel's real `keypad.cgi` page confirmed two details:

- **Key presses go to `keypad.cgx`, not `vk.cgi`.** The page's own `kp(key)`
  function never submits the `<form action="vk.cgi">` — that form is only a
  no-JS fallback. The real client appends `svkkey=<key><uid>&` to a buffer
  that gets folded into the body of the *next* POST to `keypad.cgx`, along
  with `svkp_uid=<uid>`. This integration replicates that: `async_send_key`
  POSTs directly to `keypad.cgx` with both fields, and updates all entities
  from the state returned in that same response — no extra poll needed.
- **Zone keys are lowercase**: `kp('a')`, `kp('b')`, `kp('c')`, `kp('d')` in
  the real markup — not uppercase. Uppercase `A`–`D` are not used; uppercase
  `D` is the nav "Down" key, distinct from lowercase `d` (zone D).
- **Alarm/ok status is NOT a `<bgcol>` colour at all.** A second web archive
  (captured with a forced telephone-line-fault condition active) let us pull
  the actual client-side logic, and it's different from the original
  spec's assumption:

  ```js
  function dovkleds(){
    ...
    if ((vkleds & 1024) || (vkleds & 2048)) navKeyColour(1);
    else navKeyColour(0);
    ...
  }
  function navKeyColour(col){
    if (col == 0) { nk8.style.backgroundPosition = "0px 0px";
    } else         { nk8.style.backgroundPosition = "-95px 0px"; }
  }
  ```

  The nav key's ok/alarm appearance is driven by **bits 1024 (`0x400`) and
  2048 (`0x800`) of the same `vkleds` integer** that also encodes the zone
  A–D states — it just flips a sprite-image position, not a CSS colour. The
  JS itself doesn't label which sprite position means what; that mapping
  was confirmed by real-world testing (forcing a telephone line fault):
  **bits set means OK, bits clear means alarm** — the opposite of what the
  branch naming (`navKeyColour(1)` vs `(0)`) might suggest. This integration
  uses that bitmask as the primary, protocol-confirmed signal for the Alarm
  Status sensor (`ok` if either bit is set, otherwise `alarm`). The
  `<bgcol>`/`nk8` colour-matching from `const.py`
  (`OK_COLORS`/`ALARM_COLORS`) is kept only as a fallback for firmware
  variants that might not expose `vkleds`, or for diagnostics — it's
  exposed as the `nav_color` attribute on the Alarm Status sensor either
  way.

## Remaining assumptions you should verify against your real panel

Most of the original guesses were confirmed against a real web archive of
the panel's `keypad.cgi` page (see **Protocol notes** above). What's left
unverified:

1. **XML root element**: the panel's response snippets didn't show a wrapping
   root tag, so the parser wraps whatever is returned in `<root>...</root>`
   before parsing. If the real response already has a root element, this is
   harmless (just adds a level), but if it turns out to be a different shape
   you may need to adjust `api.py::_parse_state`.
2. **Zone bitmask meaning**: the 2-bit value per zone (0–3) isn't documented,
   so each `Zone A–D` binary sensor currently just reports "on" if its 2-bit
   value is non-zero, and exposes the raw 0–3 value as an attribute. Once you
   observe what each of the 4 possible values actually means (e.g. ready /
   open / bypassed / alarm) you can refine the `is_on` logic in
   `binary_sensor.py`, or split each zone into a proper 4-state sensor.

## Repo layout

```
.
├── custom_components/
│   └── ion40_alarm/
│       ├── __init__.py       # setup/teardown, service registration
│       ├── api.py            # HTTP + XML client for keypad.cgx
│       ├── binary_sensor.py  # zone A-D binary sensors
│       ├── config_flow.py    # UI setup flow (host/port/scan interval)
│       ├── const.py          # constants, key list, colour assumptions
│       ├── coordinator.py    # polling coordinator
│       ├── manifest.json
│       ├── sensor.py         # display + alarm status sensors
│       ├── services.yaml     # send_key / send_keys service schemas
│       ├── strings.json
│       └── translations/
│           ├── en.json
│           └── nl.json
├── .github/
│   └── workflows/
│       └── validate.yml      # hassfest + HACS validation on push/PR
├── hacs.json                 # HACS repository metadata
├── LICENSE
└── README.md
```