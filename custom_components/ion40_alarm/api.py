"""Client for talking to the i-ON40 keypad web interface."""
from __future__ import annotations

import asyncio
import logging
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field

import aiohttp

from .const import ALARM_COLORS, DEFAULT_TIMEOUT, OK_COLORS, VKLEDS_ALARM_BITMASK, ZONES

_LOGGER = logging.getLogger(__name__)


class PanelError(Exception):
    """Raised when the panel cannot be reached or returns bad data."""


@dataclass
class PanelState:
    """A parsed snapshot of the keypad display."""

    lines: dict[str, str] = field(default_factory=dict)
    display_text: str = ""
    nav_color: str | None = None
    alarm_status: str = "unknown"  # "ok" | "alarm" | "unknown"
    led_bitmask: int | None = None
    zones: dict[str, int] = field(default_factory=dict)  # zone -> 2-bit value (0-3)
    raw_xml: str = ""


class Ion40PanelClient:
    """
    Thin async client wrapping keypad.cgx.

    NOTE: /vk.cgi is only the <form action="vk.cgi"> fallback the keypad
    page renders for browsers without JavaScript. The real JS client
    (confirmed from the panel's own onload_and_form_funcs.js /
    keypad.cgi page script) never POSTs to it. Instead, key presses are
    folded into the request body of the *next* poll to keypad.cgx:

        kp(key) -> ajaxPostMsg += "svkkey=" + key + uid + "&"
        ... later, the periodic poll sends:
        POST /keypad.cgx  body: "svkkey=<key><uid>&svkp_uid=<uid>"

    We replicate that here: async_send_key POSTs directly to keypad.cgx
    with both fields present, and returns the freshly parsed state from
    that same response (no extra poll needed).
    """

    def __init__(
        self,
        session: aiohttp.ClientSession,
        host: str,
        port: int,
        uid: str,
        use_https: bool = False,
    ) -> None:
        self._session = session
        scheme = "https" if use_https else "http"
        self._base_url = f"{scheme}://{host}:{port}"
        self._uid = uid

    @property
    def base_url(self) -> str:
        return self._base_url

    @property
    def uid(self) -> str:
        return self._uid

    def _cookies(self) -> dict[str, str]:
        return {"svkpuid": self._uid}

    async def _async_post_keypad(self, extra_data: dict[str, str]) -> PanelState:
        """POST to /keypad.cgx with svkp_uid plus any extra form fields."""
        url = f"{self._base_url}/keypad.cgx"
        data = {**extra_data, "svkp_uid": self._uid}
        try:
            async with self._session.post(
                url,
                data=data,
                cookies=self._cookies(),
                timeout=aiohttp.ClientTimeout(total=DEFAULT_TIMEOUT),
            ) as resp:
                resp.raise_for_status()
                text = await resp.text()
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise PanelError(f"Error communicating with panel: {err}") from err

        return self._parse_state(text)

    async def async_get_state(self) -> PanelState:
        """Poll /keypad.cgx and return the parsed panel state."""
        return await self._async_post_keypad({})

    async def async_send_key(self, key: str) -> PanelState:
        """
        Send a single key press.

        Matches the panel's own JS: svkkey=<key><uid>, POSTed to
        keypad.cgx (not vk.cgi - see class docstring). Returns the
        state parsed from the response, since the panel replies with
        a fresh XML snapshot to this request too.
        """
        return await self._async_post_keypad({"svkkey": f"{key}{self._uid}"})

    async def async_send_keys(self, keys: list[str], delay: float = 0.3) -> PanelState:
        """Send a sequence of key presses with a short delay between each."""
        state: PanelState | None = None
        for i, key in enumerate(keys):
            state = await self.async_send_key(key)
            if i < len(keys) - 1 and delay > 0:
                await asyncio.sleep(delay)
        return state

    @staticmethod
    def _parse_state(text: str) -> PanelState:
        """Parse the XML returned by keypad.cgx into a PanelState."""
        cleaned = text.strip()
        # The panel's XML fragment may or may not have a single root element
        # and may omit the XML declaration. Strip any declaration and wrap
        # in a synthetic root so ElementTree can always parse it.
        cleaned = re.sub(r"^<\?xml[^>]*\?>", "", cleaned).strip()
        wrapped = f"<root>{cleaned}</root>"

        try:
            root = ET.fromstring(wrapped)
        except ET.ParseError as err:
            raise PanelError(f"Could not parse panel XML: {err}") from err

        state = PanelState(raw_xml=text)

        # <text><id>rtm500</id><value>line1</value></text>
        lines: dict[str, str] = {}
        for text_el in root.findall(".//text"):
            id_el = text_el.find("id")
            val_el = text_el.find("value")
            if id_el is not None and val_el is not None:
                lines[id_el.text or ""] = val_el.text or ""
        state.lines = lines
        # Join lines in a stable, sorted-by-id order for a single display string.
        state.display_text = "\n".join(lines[k] for k in sorted(lines.keys()))

        # <vkleds><dummy/><value>3</value></vkleds>
        # This is the primary, protocol-confirmed source for both zone
        # states AND overall alarm/ok status - see VKLEDS_ALARM_BITMASK
        # in const.py for exactly how the panel's own JS derives the
        # nav key's alarm/ok appearance from this same integer.
        vkleds_el = root.find(".//vkleds")
        if vkleds_el is not None:
            val_el = vkleds_el.find("value")
            if val_el is not None and val_el.text and val_el.text.strip().lstrip("-").isdigit():
                bitmask = int(val_el.text.strip())
                state.led_bitmask = bitmask
                zones: dict[str, int] = {}
                for i, zone in enumerate(ZONES):
                    zones[zone] = (bitmask >> (i * 2)) & 0b11
                state.zones = zones

        # <bgcol><id>nk8</id><value>#00AA00</value></bgcol>
        # There can be multiple <bgcol> elements (one per nav button) - we
        # need specifically the one whose <id> is "nk8", not just the first
        # one found. Kept for diagnostics/fallback only - see below.
        for bgcol_el in root.findall(".//bgcol"):
            id_el = bgcol_el.find("id")
            val_el = bgcol_el.find("value")
            if id_el is not None and id_el.text == "nk8" and val_el is not None and val_el.text:
                state.nav_color = val_el.text
                break

        # Alarm/ok status: prefer the confirmed vkleds-bitmask signal.
        # NOTE: inverted from the initial reading of the panel's JS - real
        # world testing (forced telephone-line-fault) showed bits 1024/2048
        # set actually means "ok", and clear means "alarm". The JS branch
        # names (navKeyColour(1) vs (0)) apparently don't map to "alarm" vs
        # "ok" the way they read; only the bit meaning below is trustworthy.
        # Only fall back to bgcol colour-matching if we didn't get a usable
        # vkleds value at all (e.g. a firmware variant that omits it).
        if state.led_bitmask is not None:
            state.alarm_status = "ok" if state.led_bitmask & VKLEDS_ALARM_BITMASK else "alarm"
        elif state.nav_color:
            nav_color_upper = state.nav_color.upper()
            if nav_color_upper in OK_COLORS:
                state.alarm_status = "ok"
            elif nav_color_upper in ALARM_COLORS:
                state.alarm_status = "alarm"
            else:
                state.alarm_status = "unknown"

        return state
