"""Generate the README animated preview GIF for ARIA public v0.2.

The output is intentionally deterministic: no network calls, no external
assets, and no random state. It renders a short visual story of the public
release: runtime orchestration, Phase 11 vendor boundaries, and Phase 12 replay
contracts.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "Docs" / "English" / "phases" / "aria-v02-runtime-preview.gif"

WIDTH = 960
HEIGHT = 540
SCALE = 2
FPS = 9
FRAME_COUNT = 54
DURATION_MS = int(1000 / FPS)


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        Path("C:/Windows/Fonts/seguisb.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf"),
        Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size * SCALE)
    return ImageFont.load_default()


FONT_TITLE = font(36, bold=True)
FONT_SUBTITLE = font(15, bold=True)
FONT_LABEL = font(17, bold=True)
FONT_SMALL = font(12, bold=True)
FONT_TINY = font(10, bold=True)


def ease(value: float) -> float:
    value = max(0.0, min(1.0, value))
    return value * value * (3 - 2 * value)


def stage(frame: int, start: int, end: int) -> float:
    if frame <= start:
        return 0.0
    if frame >= end:
        return 1.0
    return ease((frame - start) / (end - start))


def color_mix(a: tuple[int, int, int], b: tuple[int, int, int], amount: float) -> tuple[int, int, int]:
    amount = max(0.0, min(1.0, amount))
    return tuple(int(a[i] + (b[i] - a[i]) * amount) for i in range(3))


def xy(rect: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    return tuple(v * SCALE for v in rect)


def point(p: tuple[int, int]) -> tuple[int, int]:
    return p[0] * SCALE, p[1] * SCALE


def text(draw: ImageDraw.ImageDraw, pos: tuple[int, int], value: str, fill: tuple[int, int, int], fnt: ImageFont.FreeTypeFont, anchor: str = "la") -> None:
    draw.text(point(pos), value, font=fnt, fill=fill, anchor=anchor)


def round_rect(
    draw: ImageDraw.ImageDraw,
    rect: tuple[int, int, int, int],
    radius: int,
    fill: tuple[int, int, int],
    outline: tuple[int, int, int] | None = None,
    width: int = 1,
) -> None:
    draw.rounded_rectangle(xy(rect), radius=radius * SCALE, fill=fill, outline=outline, width=width * SCALE)


def draw_background(draw: ImageDraw.ImageDraw) -> None:
    top = (7, 16, 31)
    bottom = (11, 47, 58)
    for y in range(HEIGHT * SCALE):
        t = y / (HEIGHT * SCALE - 1)
        draw.line([(0, y), (WIDTH * SCALE, y)], fill=color_mix(top, bottom, t))
    grid = (255, 255, 255)
    for x in range(0, WIDTH + 1, 48):
        draw.line([(x * SCALE, 0), (x * SCALE, HEIGHT * SCALE)], fill=(*grid, 9), width=SCALE)
    for y in range(0, HEIGHT + 1, 48):
        draw.line([(0, y * SCALE), (WIDTH * SCALE, y * SCALE)], fill=(*grid, 8), width=SCALE)


def alpha_layer(base: Image.Image) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    return layer, ImageDraw.Draw(layer, "RGBA")


def composite(base: Image.Image, layer: Image.Image, alpha: float = 1.0) -> Image.Image:
    alpha = max(0.0, min(1.0, alpha))
    if alpha < 1.0:
        layer = layer.copy()
        mask = layer.getchannel("A").point(lambda value: int(value * alpha))
        layer.putalpha(mask)
    return Image.alpha_composite(base, layer)


def draw_glow_line(draw: ImageDraw.ImageDraw, start: tuple[int, int], end: tuple[int, int], progress: float, color: tuple[int, int, int]) -> None:
    progress = max(0.0, min(1.0, progress))
    sx, sy = start
    ex, ey = end
    mx = sx + (ex - sx) * progress
    my = sy + (ey - sy) * progress
    base = [(sx * SCALE, sy * SCALE), (ex * SCALE, ey * SCALE)]
    active = [(sx * SCALE, sy * SCALE), (int(mx * SCALE), int(my * SCALE))]
    draw.line(base, fill=(36, 57, 78), width=5 * SCALE)
    if progress > 0:
        draw.line(active, fill=color, width=7 * SCALE)
        draw.ellipse(
            (int(mx * SCALE - 7 * SCALE), int(my * SCALE - 7 * SCALE), int(mx * SCALE + 7 * SCALE), int(my * SCALE + 7 * SCALE)),
            fill=(247, 211, 109),
        )


def draw_node(
    draw: ImageDraw.ImageDraw,
    center: tuple[int, int],
    label: str,
    icon: str,
    active: float,
    accent: tuple[int, int, int],
) -> None:
    cx, cy = center
    fill = color_mix((19, 38, 61), (248, 251, 255), active * 0.12)
    outline = color_mix((58, 88, 118), accent, active)
    round_rect(draw, (cx - 56, cy - 48, cx + 56, cy + 48), 22, fill, outline, 2)
    draw.ellipse(xy((cx - 24, cy - 30, cx + 24, cy + 18)), fill=color_mix((29, 61, 90), accent, active), outline=None)
    text(draw, (cx, cy - 6), icon, (255, 255, 255), FONT_LABEL, anchor="mm")
    text(draw, (cx, cy + 34), label, (232, 242, 252), FONT_SMALL, anchor="mm")


def draw_chip(draw: ImageDraw.ImageDraw, rect: tuple[int, int, int, int], label: str, active: float, accent: tuple[int, int, int]) -> None:
    fill = color_mix((223, 238, 248), (245, 252, 255), active)
    outline = color_mix((78, 121, 154), accent, active)
    round_rect(draw, rect, 12, fill, outline, 1)
    x1, y1, x2, y2 = rect
    text(draw, ((x1 + x2) // 2, (y1 + y2) // 2 + 1), label, (18, 67, 103), FONT_SMALL, anchor="mm")


def draw_contract(draw: ImageDraw.ImageDraw, rect: tuple[int, int, int, int], label: str, active: float) -> None:
    fill = color_mix((222, 244, 231), (248, 255, 250), active)
    outline = color_mix((54, 127, 91), (128, 223, 160), active)
    round_rect(draw, rect, 12, fill, outline, 1)
    x1, y1, x2, y2 = rect
    text(draw, ((x1 + x2) // 2, (y1 + y2) // 2 + 1), label, (18, 70, 53), FONT_SMALL, anchor="mm")


def render(frame: int) -> Image.Image:
    img = Image.new("RGBA", (WIDTH * SCALE, HEIGHT * SCALE), (0, 0, 0, 255))
    draw = ImageDraw.Draw(img, "RGBA")
    draw_background(draw)

    flow = stage(frame, 1, 18)
    vendor = stage(frame, 15, 31)
    replay = stage(frame, 29, 45)
    finale = stage(frame, 40, 53)

    text(draw, (480, 54), "ARIA v0.2 Public Preview", (248, 251, 255), FONT_TITLE, anchor="mm")
    text(draw, (480, 88), "From controlled automation to replay-aware agent infrastructure", (197, 216, 234), FONT_SUBTITLE, anchor="mm")

    nodes = [
        ((118, 196), "Goal", "G"),
        ((256, 196), "Brain", "B"),
        ((394, 196), "Eye", "E"),
        ((532, 196), "Hand", "H"),
        ((670, 196), "Safety", "S"),
        ((808, 196), "Replay", "R"),
    ]
    accent = (86, 199, 220)
    for index in range(len(nodes) - 1):
        p = max(0.0, min(1.0, flow * (len(nodes) - 1) - index))
        draw_glow_line(draw, nodes[index][0], nodes[index + 1][0], p, accent)
    for index, (center, label, icon) in enumerate(nodes):
        active = max(0.0, min(1.0, flow * len(nodes) - index))
        draw_node(draw, center, label, icon, active, accent)

    vendor_layer, vd = alpha_layer(img)
    round_rect(vd, (54, 292, 438, 490), 26, (247, 251, 255), (78, 169, 205), 2)
    round_rect(vd, (54, 292, 438, 350), 26, (49, 158, 204), None, 1)
    vd.rectangle(xy((54, 322, 438, 350)), fill=(49, 158, 204))
    text(vd, (82, 309), "PHASE 11", (222, 248, 255), FONT_SMALL, anchor="lt")
    text(vd, (82, 329), "Vendor Boundary", (255, 255, 255), FONT_LABEL, anchor="lt")
    for i, label in enumerate(["AIHawk", "Skyvern", "OpenAdapt", "browser-use"]):
        x = 82 + (i % 2) * 174
        y = 374 + (i // 2) * 44
        draw_chip(vd, (x, y, x + 150, y + 30), label, max(0.0, min(1.0, vendor * 4 - i)), (86, 199, 220))
    text(vd, (82, 458), "Adapters normalize vendor output.", (24, 50, 72), FONT_TINY)
    text(vd, (82, 474), "Safety and HITL remain authoritative.", (24, 50, 72), FONT_TINY)
    img = composite(img, vendor_layer, vendor)
    draw = ImageDraw.Draw(img, "RGBA")

    replay_layer, rd = alpha_layer(img)
    round_rect(rd, (522, 292, 906, 490), 26, (248, 255, 250), (92, 198, 128), 2)
    round_rect(rd, (522, 292, 906, 350), 26, (62, 185, 119), None, 1)
    rd.rectangle(xy((522, 322, 906, 350)), fill=(62, 185, 119))
    text(rd, (550, 309), "PHASE 12", (237, 255, 243), FONT_SMALL, anchor="lt")
    text(rd, (550, 329), "Replay Contract", (255, 255, 255), FONT_LABEL, anchor="lt")
    for i, label in enumerate(["TraceEnvelope", "StepRecord", "ReplayRequest"]):
        x = 550 + i * 116
        draw_contract(rd, (x, 378, x + 98, 414), label, max(0.0, min(1.0, replay * 3 - i)))
    text(rd, (550, 458), "Deterministic hashes verify traces.", (25, 74, 57), FONT_TINY)
    text(rd, (550, 474), "Invariant tests keep replay safe.", (25, 74, 57), FONT_TINY)
    img = composite(img, replay_layer, replay)
    draw = ImageDraw.Draw(img, "RGBA")

    final_alpha = int(235 * finale)
    if final_alpha:
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        od = ImageDraw.Draw(overlay, "RGBA")
        round_rect(od, (230, 500, 730, 528), 14, (248, 251, 255), None, 1)
        text(od, (480, 515), "Public docs stay clean; private traces and credentials stay out.", (24, 50, 72), FONT_TINY, anchor="mm")
        img = composite(img, overlay, final_alpha / 235)

    img = img.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS).convert("RGB")
    return img


def main() -> None:
    frames = [render(i) for i in range(FRAME_COUNT)]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(
        OUT,
        save_all=True,
        append_images=frames[1:],
        duration=DURATION_MS,
        loop=0,
        optimize=True,
        disposal=2,
    )
    print(f"wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
