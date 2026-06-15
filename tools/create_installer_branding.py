from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "resources" / "logo" / "ye-ruka-512.png"
OUTPUT = ROOT / "packaging" / "assets"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    name = "segoeuib.ttf" if bold else "segoeui.ttf"
    return ImageFont.truetype(str(Path("C:/Windows/Fonts") / name), size)


def build_wizard_image(logo: Image.Image) -> None:
    scale = 3
    width, height = 164 * scale, 314 * scale
    image = Image.new("RGB", (width, height), "#101826")
    draw = ImageDraw.Draw(image)

    draw.rectangle((0, 0, 12, height), fill="#5B8CFF")
    draw.rectangle((12, height - 12, width, height), fill="#735CFF")

    mark = logo.resize((330, 330), Image.Resampling.LANCZOS)
    image.paste(mark, ((width - 330) // 2 + 6, 92), mark)

    draw.text((54, 504), "Є-РУКА", font=font(52, bold=True), fill="#F5F7FF")
    draw.text((56, 573), "РОБОТИЗОВАНА КИСТЬ", font=font(19, bold=True), fill="#6FB7FF")
    draw.line((56, 629, width - 48, 629), fill="#28364D", width=3)
    draw.text((56, 667), "BY KICO", font=font(22, bold=True), fill="#C8D1E2")
    draw.text((56, 708), "VERSION 2.2.0", font=font(15), fill="#74839C")

    image.resize((164, 314), Image.Resampling.LANCZOS).save(
        OUTPUT / "installer-wizard.bmp"
    )


def build_small_image(logo: Image.Image) -> None:
    size = 58
    image = Image.new("RGB", (size, size), "#101826")
    mark = logo.resize((52, 52), Image.Resampling.LANCZOS)
    image.paste(mark, (3, 3), mark)
    image.save(OUTPUT / "installer-small.bmp")


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    logo = Image.open(SOURCE).convert("RGBA")
    build_wizard_image(logo)
    build_small_image(logo)
    print(f"Installer branding created in {OUTPUT}")


if __name__ == "__main__":
    main()
