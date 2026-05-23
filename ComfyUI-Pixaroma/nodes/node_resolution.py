"""Resolution Pixaroma — outputs width + height ints chosen via the JS UI.

Adds optional width/height passthrough inputs. When passthrough is enabled,
connected width/height values are returned unchanged; when disabled, the node
uses its normal JS UI ResolutionState.
"""

import json
from typing import Optional, Tuple

DEFAULT_STATE = {
    "mode": "preset",
    "ratio": "1:1",
    "w": 1024,
    "h": 1024,
    "custom_w": 1024,
    "custom_h": 1024,
    # Custom Ratio mode — kept in sync with DEFAULT_STATE in
    # js/resolution/index.js (CLAUDE.md Pattern #3).
    "custom_ratio_w": 4,
    "custom_ratio_h": 3,
    "snap": 16,
}


def _clamp(n: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, n))


def _resolution_from_state(ResolutionState: str) -> Tuple[int, int]:
    try:
        state = json.loads(ResolutionState)
        w = int(state.get("w", 1024))
        h = int(state.get("h", 1024))
    except Exception:
        print("[PixaromaResolution] Malformed state, falling back to 1024x1024")
        w, h = 1024, 1024

    w = _clamp(w, 64, 16384)
    h = _clamp(h, 64, 16384)
    return (w, h)


class PixaromaResolution:
    DESCRIPTION = (
        "Resolution Pixaroma - a one-click resolution picker. The on-node UI "
        "shows a 3x3 ratio chip grid (1:1, 16:9, 9:16, 2:1, 3:2, 2:3, 4:3, 3:4, "
        "4:5) with the 8 most-popular sizes for each ratio. Covers SDXL, AI "
        "video, and social-media-ready dimensions. Click a chip, click a size, "
        "done.\n\n"
        "Custom Ratio mode lets you type any W:H (21:9, 16:10, anything) and "
        "get auto-computed AI-friendly sizes. Custom Resolution mode lets you "
        "type exact dimensions; math expressions like '1024+128' or '512*2' "
        "work in the W / H fields. The Snap chips (16 / 32 / 64 / no snap) "
        "round outputs to multiples that VAE encoders prefer.\n\n"
        "Outputs width and height as INT. State saves and restores with the "
        "workflow. Optional width and height inputs can be passed through by "
        "turning passthrough on.\n\n"
        "All UI lives on the JS side; the only Python input used by the picker "
        "mode is a hidden serialized state string that gets injected at "
        "execution time."
    )

    @classmethod
    def INPUT_TYPES(cls):
        # ResolutionState is `hidden`, NOT `required`. Hidden inputs do NOT
        # produce a widget OR an input slot in the Vue frontend (the auto-
        # created input dot for required STRING widgets is what the original
        # implementation had to fight against). The JS frontend stores state
        # in node.properties.resolutionState and injects it into the API
        # prompt at execution time via app.graphToPrompt.
        #
        # `passthrough` is a normal widget so it appears on the node above the
        # JS-rendered resolution buttons in standard ComfyUI layouts.
        #
        # `width` and `height` are optional input slots. The node can still run
        # without them when passthrough is off.
        return {
            "required": {
                "passthrough": (
                    "BOOLEAN",
                    {
                        "default": False,
                        "label_on": "on",
                        "label_off": "off",
                    },
                ),
            },
            "optional": {
                "width": ("INT",),
                "height": ("INT",),
            },
            "hidden": {
                "ResolutionState": (
                    "STRING",
                    {"default": json.dumps(DEFAULT_STATE)},
                ),
            },
        }

    RETURN_TYPES = ("INT", "INT")
    RETURN_NAMES = ("width", "height")
    OUTPUT_TOOLTIPS = ("The chosen width in pixels.", "The chosen height in pixels.")
    FUNCTION = "get_resolution"
    CATEGORY = "👑 Pixaroma"

    def get_resolution(
        self,
        ResolutionState: str,
        passthrough: bool = False,
        width: Optional[int] = None,
        height: Optional[int] = None,
    ):
        state_w, state_h = _resolution_from_state(ResolutionState)

        if passthrough:
            # Pass connected input values through unchanged. If only one optional
            # input is connected, fall back to the UI-selected value for the
            # missing side so the node still executes predictably.
            out_w = width if width is not None else state_w
            out_h = height if height is not None else state_h
            return (out_w, out_h)

        return (state_w, state_h)


NODE_CLASS_MAPPINGS = {"PixaromaResolution": PixaromaResolution}
NODE_DISPLAY_NAME_MAPPINGS = {"PixaromaResolution": "Resolution Pixaroma"}
