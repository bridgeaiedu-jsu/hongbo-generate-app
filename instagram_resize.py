import re
from datetime import date
from pathlib import Path

from PIL import Image, ImageOps

BASE_DIR = Path(__file__).resolve().parent
SOURCE_DIR = BASE_DIR / "자료"
OUTPUT_DIR = BASE_DIR / "완성"
LOGO_PATH = SOURCE_DIR / "로고.png"
STORE_INFO_PATH = SOURCE_DIR / "가게 정보.txt"
CAPTION_OUTPUT_PATH = OUTPUT_DIR / "홍보문구.txt"
TARGET_SIZE = 1080
VALID_EXTENSIONS = {".jpg", ".jpeg", ".png"}
LOGO_WIDTH_RATIO = 0.15
LOGO_MARGIN = 40
LOGO_BOX_PADDING = 16
LOGO_BOX_OPACITY = 0.85


def crop_to_square(image: Image.Image) -> Image.Image:
    width, height = image.size
    side = min(width, height)
    left = (width - side) // 2
    top = (height - side) // 2
    return image.crop((left, top, left + side, top + side))


def apply_logo(square: Image.Image) -> Image.Image:
    if not LOGO_PATH.exists():
        return square

    with Image.open(LOGO_PATH) as logo_raw:
        logo = logo_raw.convert("RGBA")

    logo_width = int(square.width * LOGO_WIDTH_RATIO)
    logo_height = int(logo.height * (logo_width / logo.width))
    logo = logo.resize((logo_width, logo_height), Image.LANCZOS)

    box_width = logo_width + LOGO_BOX_PADDING * 2
    box_height = logo_height + LOGO_BOX_PADDING * 2
    box = Image.new("RGBA", (box_width, box_height), (255, 255, 255, int(255 * LOGO_BOX_OPACITY)))

    base = square.convert("RGBA")
    box_x = base.width - box_width - LOGO_MARGIN
    box_y = base.height - box_height - LOGO_MARGIN
    base.paste(box, (box_x, box_y), box)
    base.paste(logo, (box_x + LOGO_BOX_PADDING, box_y + LOGO_BOX_PADDING), logo)
    return base.convert("RGB")


def parse_store_info(path: Path) -> dict:
    info = {
        "name": "", "location": "", "features": "",
        "audience": "", "promos": [], "tone": "",
    }
    section = None
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("가게 이름:"):
            info["name"] = line.split(":", 1)[1].strip()
        elif line.startswith("위치:"):
            info["location"] = line.split(":", 1)[1].strip()
        elif line.startswith("가게 특징:"):
            info["features"] = line.split(":", 1)[1].strip()
        elif line.startswith("주 고객층:"):
            info["audience"] = line.split(":", 1)[1].strip()
        elif line.startswith("이번 주 홍보할 것"):
            section = "promos"
        elif line.startswith("말투 느낌:"):
            info["tone"] = line.split(":", 1)[1].strip()
            section = None
        elif line.startswith("-") and section == "promos":
            info["promos"].append(line.lstrip("- ").strip())
    return info


def has_batchim(word: str) -> bool:
    if not word:
        return False
    code = ord(word[-1]) - 0xAC00
    if 0 <= code <= 11171:
        return code % 28 != 0
    return False


def josa(word: str, with_batchim: str, without_batchim: str) -> str:
    return with_batchim if has_batchim(word) else without_batchim


def to_formal_sentences(detail: str) -> str:
    sentences = []
    for clause in detail.split(","):
        clause = clause.strip()
        if not clause:
            continue
        if clause.endswith("음"):
            clause = clause[:-1] + "습니다"
        elif not clause.endswith(("습니다", "니다")):
            clause = clause + "습니다"
        sentences.append(clause)
    return " ".join(s if s.endswith(".") else s + "." for s in sentences)


def parse_menu(promo: str) -> tuple:
    match = re.match(r"신메뉴\s*'([^']+)'\s*([\d,]+원)?,?\s*(.*)", promo)
    if match:
        name, price, detail = match.groups()
        return name, price or "", (detail or "").strip()
    return promo, "", ""


def parse_discount(promo: str) -> tuple:
    match = re.search(r"(.*?)(?:방문\s*시\s*)?(아메리카노|라떼|카페라떼|에스프레소)\s*([\d,]+원)?\s*할인", promo)
    if match:
        condition, item, price = match.groups()
        return (condition or "").strip(), item, price or ""
    return "", promo, ""


def build_hashtags(info: dict) -> list:
    location_tokens = info["location"].split()
    region_tags = []
    if location_tokens:
        region_tags.append(location_tokens[0])
    if len(location_tokens) >= 2:
        region_tags.append(location_tokens[0] + location_tokens[1])
    if len(location_tokens) >= 3:
        region_tags.append(location_tokens[2])

    business_tags = ["카페", "커피맛집", "스페셜티커피"]

    promo_text = " ".join(info["promos"])
    menu_names = re.findall(r"'([^']+)'", promo_text)
    menu_names += re.findall(r"(아메리카노|라떼|에스프레소|카페라떼)", promo_text)

    candidates = []
    for name in region_tags:
        candidates.append(name + "카페")
        candidates.append(name + "맛집")
    candidates += business_tags
    candidates += [m.replace(" ", "") for m in menu_names]

    hashtags = []
    for tag in candidates:
        clean = "#" + tag.replace(" ", "")
        if clean not in hashtags:
            hashtags.append(clean)
    return hashtags[:10]


def generate_captions(info: dict) -> str:
    name = info["name"] or "저희 가게"
    location = info["location"] or "동네"

    menu_name, menu_price, menu_detail = (
        parse_menu(info["promos"][0]) if len(info["promos"]) > 0 else ("", "", "")
    )
    menu_price_part = f" {menu_price}" if menu_price else ""
    menu_detail_sentence = to_formal_sentences(menu_detail) if menu_detail else ""

    discount_condition, discount_item, discount_price = (
        parse_discount(info["promos"][1]) if len(info["promos"]) > 1 else ("", "", "")
    )
    discount_price_part = f" {discount_price}" if discount_price else ""
    discount_condition_part = f"{discount_condition} " if discount_condition else ""

    hashtags = " ".join(build_hashtags(info))

    instagram = {
        "감성형": (
            f"오늘은 {menu_name}를 새로 냈습니다.\n"
            f"{menu_detail_sentence}\n"
            f"{discount_condition_part}방문하시면 {discount_item}{discount_price_part} 할인됩니다."
        ),
        "정보형": (
            f"이번 주 소식입니다.\n"
            f"신메뉴 {menu_name}, {menu_price}입니다.\n"
            f"{discount_condition_part}방문 시 {discount_item}{discount_price_part} 할인됩니다."
        ),
        "이벤트형": (
            f"이번 주까지 안내드립니다.\n"
            f"{discount_condition_part}방문하시면 {discount_item}{discount_price_part} 할인됩니다.\n"
            f"신메뉴 {menu_name}도 함께 준비했습니다."
        ),
    }

    naver_blog = {
        "감성형": (
            f"오늘은 {menu_name}를 새로 냈습니다. {menu_detail_sentence} "
            f"로스팅을 마치고 바로 내려봤는데 생각보다 잘 어울렸습니다. "
            f"{discount_condition_part}방문하시면 {discount_item}{discount_price_part}도 할인해 드립니다. "
            f"편하게 들러주시면 좋겠습니다."
        ),
        "정보형": (
            f"이번 주 안내드립니다. 신메뉴로 {menu_name}를 냈습니다. 가격은 {menu_price}입니다. "
            f"{menu_detail_sentence} "
            f"그리고 {discount_condition_part}방문하시면 {discount_item}{discount_price_part} 할인해 드립니다. "
            f"두 가지 모두 이번 주부터 적용됩니다. 참고 부탁드립니다."
        ),
        "이벤트형": (
            f"이번 주 한정으로 두 가지를 안내드립니다. 첫째, 신메뉴 {menu_name}입니다. {menu_detail_sentence} "
            f"둘째, {discount_condition_part}방문 시 {discount_item}{discount_price_part} 할인입니다. "
            f"두 가지 모두 이번 주까지만 진행합니다. {location}{josa(location, '을', '를')} 지나시다 생각나시면 들러주세요."
        ),
    }

    kakao = {
        "감성형": f"{menu_name}를 새로 냈습니다.\n{menu_detail_sentence}\n편하게 들러주세요.",
        "정보형": (
            f"이번 주 안내드립니다.\n"
            f"{menu_name} {menu_price} / {discount_condition_part}{discount_item}{discount_price_part} 할인\n"
            f"참고 부탁드립니다."
        ),
        "이벤트형": (
            f"이번 주까지 안내드립니다.\n"
            f"{menu_name} 신메뉴 / {discount_condition_part}{discount_item} 할인\n"
            f"감사합니다."
        ),
    }

    lines = []

    lines.append("[인스타그램용]")
    for style, text in instagram.items():
        lines.append(f"--- {style} ---")
        lines.append(text)
        lines.append(hashtags)
    lines.append("")

    lines.append("[네이버 블로그용]")
    for style, text in naver_blog.items():
        lines.append(f"--- {style} ---")
        lines.append(text)
    lines.append("")

    lines.append("[카카오톡 단골 공지용]")
    for style, text in kakao.items():
        lines.append(f"--- {style} ---")
        lines.append(text)
    lines.append("")

    return "\n".join(lines).strip() + "\n"


def main() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)

    source_files = sorted(
        f for f in SOURCE_DIR.iterdir()
        if f.is_file()
        and f.suffix.lower() in VALID_EXTENSIONS
        and f.resolve() != LOGO_PATH.resolve()
    )

    if not source_files:
        print("자료 폴더에 jpg, png 사진이 없습니다.")
        return

    today = date.today().strftime("%Y%m%d")

    for index, source_path in enumerate(source_files, start=1):
        with Image.open(source_path) as image:
            image = ImageOps.exif_transpose(image)
            image = image.convert("RGB")
            square = crop_to_square(image)
            square = square.resize((TARGET_SIZE, TARGET_SIZE), Image.LANCZOS)
            square = apply_logo(square)

            output_path = OUTPUT_DIR / f"{today}_{index:02d}.jpg"
            square.save(output_path, "JPEG", quality=90)
            print(f"완료: {source_path.name} -> {output_path.name}")

    print(f"\n총 {len(source_files)}장을 '완성' 폴더에 저장했습니다.")

    if STORE_INFO_PATH.exists():
        info = parse_store_info(STORE_INFO_PATH)
        captions = generate_captions(info)
        CAPTION_OUTPUT_PATH.write_text(captions, encoding="utf-8-sig")
        print(f"홍보 문구를 '{CAPTION_OUTPUT_PATH.name}'로 저장했습니다.")
    else:
        print("'가게 정보.txt' 파일이 없어 홍보 문구 생성은 건너뜁니다.")


if __name__ == "__main__":
    main()
