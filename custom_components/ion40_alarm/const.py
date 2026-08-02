"""Constants for the i-ON40 Alarm Panel integration."""

DOMAIN = "ion40_alarm"

PLATFORMS = ["sensor", "binary_sensor"]

CONF_UID = "uid"
CONF_SCAN_INTERVAL = "scan_interval"

DEFAULT_PORT = 80
DEFAULT_SCAN_INTERVAL = 5  # seconds
DEFAULT_TIMEOUT = 10  # seconds

# --- Alarm/ok status detection ---
# The panel's own client-side JS (onload_and_form_funcs.js) toggles the
# nk8 nav key's sprite position based on these same vkleds bits:
#
#   function dovkleds(){
#     ...
#     if ((vkleds & 1024) || (vkleds & 2048)) navKeyColour(1);
#     else navKeyColour(0);
#     ...
#   }
#   function navKeyColour(col){
#     if (col == 0) { nk8.style.backgroundPosition = "0px 0px";
#     } else         { nk8.style.backgroundPosition = "-95px 0px"; }
#   }
#
# The JS itself doesn't label which sprite position is "ok" vs "alarm" -
# that mapping was confirmed by real-world testing (forcing a telephone
# line fault): bits 1024/2048 set means OK, and clear means ALARM. This is
# the authoritative, protocol-confirmed signal and is used as the primary
# alarm/ok indicator (see api.py::_parse_state).
VKLEDS_ALARM_BITMASK = 0x400 | 0x800  # bits 1024 and 2048 - set = ok, clear = alarm

# Colours reported in <bgcol> for the nk8 nav key, used only as a fallback
# if a given firmware/panel doesn't expose the same vkleds bits (or as
# a secondary sanity check). OK_COLORS confirmed against a real panel.
# No alarm-condition colour has been confirmed - if you trigger a real
# alarm and see a specific bgcol/nk8 value, add it to ALARM_COLORS below.
OK_COLORS = frozenset({"#00FF00"})
ALARM_COLORS: frozenset[str] = frozenset()

# Zones encoded in the vkleds bitmask, 2 bits each, in this order.
# Used only for labeling the binary_sensor entities/attributes below -
# unrelated to the case of the key characters sent to the panel.
ZONES = ["A", "B", "C", "D"]

# Valid keys accepted by keypad.cgx's svkkey field. Confirmed from the
# panel's own keypad.cgi page markup/JS: nav/function keys are uppercase,
# but the four zone keys are lowercase (a/b/c/d) - distinct from the
# uppercase "D" used for the nav "Down" key.
VALID_KEYS = list("0123456789") + ["U", "D", "L", "R", "X", "T", "E", "N", "a", "b", "c", "d", "*", "#"]

SERVICE_SEND_KEY = "send_key"
SERVICE_SEND_KEYS = "send_keys"
ATTR_KEY = "key"
ATTR_KEYS = "keys"
ATTR_DELAY = "delay"

MANUFACTURER = "i-ON40"
MODEL = "Alarm Keypad"
