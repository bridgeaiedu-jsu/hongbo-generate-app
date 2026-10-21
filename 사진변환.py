from datetime import date
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps

SIZE = 1080
BASE = Path(__file__).parent
SOURCE = BASE / "자료"
OUTPUT = BASE / "완성"


LOGO_FILE = SOURCE / "로고.png"
LOGO_RATIO = 0.15   # 사진 가로 폭의 15%
MARGIN = 40         # 사진 가장자리에서 안쪽으로 40픽셀
PADDING = 14        # 로고 둘레 흰 여백
RADIUS = 14         # 흰 라벨 모서리 둥글기
LABEL_ALPHA = 130   # 흰색 불투명도 (255가 완전 불투명, 130은 약 50% 투명)


def load_logo():
    """로고 파일이 있으면 라벨 모양으로 만들어 돌려주고, 없거나 열 수 없으면 None."""
    if not LOGO_FILE.exists():
        print(f"{LOGO_FILE.name} 파일이 없어서 로고 없이 진행해요.")
        return None
    try:
        with Image.open(LOGO_FILE) as img:
            logo = ImageOps.exif_transpose(img).convert("RGBA")  # 투명한 부분은 투명 그대로
    except Exception:
        print(f"{LOGO_FILE.name}를 열 수 없어서 로고 없이 진행해요.")
        return None
    width = round(SIZE * LOGO_RATIO)
    height = max(1, round(logo.height * width / logo.width))
    logo = logo.resize((width, height), Image.LANCZOS)
    label = Image.new("RGBA", (width + PADDING * 2, height + PADDING * 2), (0, 0, 0, 0))
    ImageDraw.Draw(label).rounded_rectangle(
        (0, 0, label.width - 1, label.height - 1), RADIUS, fill=(255, 255, 255, LABEL_ALPHA)
    )
    label.alpha_composite(logo, (PADDING, PADDING))
    return label


def put_logo(photo, label):
    """사진 오른쪽 아래에 로고 라벨을 얹는다."""
    photo = photo.convert("RGBA")
    pos = (photo.width - MARGIN - label.width, photo.height - MARGIN - label.height)
    photo.alpha_composite(label, pos)
    return photo.convert("RGB")


# ---- 이번 주 인스타그램 문구 (자료\가게 정보.txt 내용이 바뀌면 여기를 새로 쓴다) ----
# 말투: 자료\내 말투.txt처럼 짧은 문장, "~습니다" 체, 과장 없이. 이모지는 문구마다 2~3개.
CAPTIONS = [
    ("감성형",
     "오늘부터 흑임자 라떼를 시작합니다. ☕\n"
     "국산 흑임자를 직접 갈아서 넣었습니다.\n"
     "고소하고, 달지 않습니다.\n"
     "\n"
     "조용한 1인 좌석이 많습니다.\n"
     "혼자 오셔도 편합니다.\n"
     "일하다 잠깐 쉬고 싶을 때 천천히 드시고 가세요. 🌿\n"
     "광주 북구 비엔날레 지구에 있습니다. 📍"),
    ("정보형",
     "이번 주 신메뉴를 알려드립니다. 📍\n"
     "흑임자 라떼, 5,500원입니다.\n"
     "국산 흑임자를 직접 갈아서 넣었습니다.\n"
     "고소하고, 달지 않습니다.\n"
     "\n"
     "직접 로스팅한 스페셜티 커피는 그대로입니다.\n"
     "조용한 1인 좌석도 그대로입니다.\n"
     "광주 북구 비엔날레 지구에 있습니다. ☕"),
    ("이벤트형",
     "오전 11시 이전에 오시면 아메리카노를 500원 할인해 드립니다. ⏰\n"
     "출근길에 한 잔 사 가셔도 됩니다.\n"
     "\n"
     "이번 주 새로 나온 흑임자 라떼는 5,500원입니다.\n"
     "직접 볶은 원두로 내려 드립니다. ☕\n"
     "오전에 편하게 들러 주세요."),
]

HASHTAGS = [
    "#광주카페", "#북구카페", "#비엔날레카페", "#광주비엔날레", "#광주스페셜티",
    "#스페셜티커피", "#직접로스팅", "#흑임자라떼", "#아메리카노할인", "#브릿지커피",
]


BLOG_TITLE = "[브릿지 커피] 흑임자 라떼를 시작합니다"

BLOG_BODY = """이번 주부터 새 메뉴를 시작합니다.
흑임자 라떼입니다. 가격은 5,500원입니다.

■ 흑임자 라떼
국산 흑임자를 사용했습니다.
흑임자는 매장에서 직접 갈아서 넣었습니다.
맛은 고소합니다. 달지 않습니다.
단 음료가 부담스러웠던 분도 드실 수 있습니다.
하루 중에 천천히 한 잔 마시고 싶을 때 좋습니다.
과장해서 말씀드리고 싶지는 않습니다.
한 번 드셔 보시고 편하게 판단해 주세요.

■ 직접 로스팅하는 커피
브릿지 커피는 스페셜티 커피를 직접 로스팅합니다.
원두를 고르고 볶는 일부터 잔에 담는 일까지 가게에서 직접 합니다.
흑임자 라떼가 낯설게 느껴지면 평소 드시던 커피로 오셔도 됩니다.
직접 볶은 원두의 맛을 천천히 느껴 보실 수 있습니다.

■ 조용한 1인 좌석
조용한 1인 좌석이 많습니다.
일하다 잠깐 머리를 식히고 싶을 때 앉으시면 됩니다.
혼자 책을 읽거나 생각을 정리하기에도 편합니다.
근처 사무실에 다니시는 분들도 점심 전후로 들러 가세요.
바쁜 날일수록 쉬는 시간이 필요하다고 생각합니다.

■ 오전 11시 이전 아메리카노 500원 할인
오전 11시 이전에 오시면 아메리카노를 500원 할인해 드립니다.
출근길에 한 잔 사 가셔도 됩니다.
오전에 여유롭게 앉아서 드셔도 됩니다.
오전에는 아메리카노로 시작하시고, 다음에는 흑임자 라떼를 드셔 보세요.

■ 위치
브릿지 커피는 광주 북구 비엔날레 지구에 있습니다.
근처에 오실 일이 있으면 들러 주세요.
천천히 쉬어 가실 수 있게 준비하고 기다리겠습니다."""

KAKAO = [
    "이번 주 신메뉴 '흑임자 라떼'를 시작합니다. 5,500원입니다.",
    "오전 11시 이전에 오시면 아메리카노를 500원 할인해 드립니다.",
    "광주 북구 비엔날레 지구에서 기다리겠습니다.",
]

DIVIDER = "=" * 40


def write_captions():
    """채널별(인스타그램/블로그/카카오톡) 홍보 문구를 완성\\홍보문구.txt로 저장한다."""
    lines = [DIVIDER, "1. 인스타그램용", DIVIDER, ""]
    for name, text in CAPTIONS:
        lines += [f"[{name}] ({len(text)}자)", text, ""]
    lines += ["[해시태그]", " ".join(HASHTAGS), ""]

    blog_len = len(BLOG_BODY)
    lines += [DIVIDER, f"2. 네이버 블로그용 (본문 {blog_len}자)", DIVIDER, ""]
    lines += ["[제목]", BLOG_TITLE, "", "[본문]", BLOG_BODY, "", "[해시태그]", " ".join(HASHTAGS), ""]

    lines += [DIVIDER, "3. 카카오톡 단골 공지용 (3줄)", DIVIDER, ""]
    lines += KAKAO + [""]
    out = OUTPUT / "홍보문구.txt"
    out.write_text("\n".join(lines), encoding="utf-8-sig")
    print(f"홍보문구 -> {out.name}")


def next_number(prefix):
    """오늘 날짜로 이미 저장된 파일 다음 번호를 구한다 (덮어쓰기 방지)."""
    used = []
    for f in OUTPUT.glob(f"{prefix}_*.jpg"):
        tail = f.stem.rsplit("_", 1)[-1]
        if tail.isdigit():
            used.append(int(tail))
    return max(used, default=0) + 1


def main():
    OUTPUT.mkdir(exist_ok=True)
    files = sorted(
        p for p in SOURCE.iterdir()
        if p.is_file() and p.suffix.lower() in (".jpg", ".jpeg", ".png") and p != LOGO_FILE
    )
    if not files:
        print("자료 폴더에 사진이 없어요.")
        return

    label = load_logo()
    prefix = date.today().isoformat()
    number = next_number(prefix)

    for path in files:
        with Image.open(path) as img:
            img = ImageOps.exif_transpose(img)  # 폰 사진 방향 바로잡기
            if img.mode in ("RGBA", "LA", "P"):
                img = img.convert("RGBA")
                bg = Image.new("RGB", img.size, (255, 255, 255))
                bg.paste(img, mask=img.split()[-1])  # 투명한 부분은 흰색
                img = bg
            else:
                img = img.convert("RGB")
            # 가운데 기준으로 정사각형 자르기 + 1080 크기 (늘리거나 찌그러뜨리지 않음)
            result = ImageOps.fit(img, (SIZE, SIZE), Image.LANCZOS, centering=(0.5, 0.5))
            if label is not None:
                result = put_logo(result, label)
            out = OUTPUT / f"{prefix}_{number:02d}.jpg"
            result.save(out, "JPEG", quality=95)
        print(f"{path.name} -> {out.name}")
        number += 1

    write_captions()
    print(f"끝! 사진 {len(files)}장과 홍보문구를 '완성' 폴더에 저장했어요.")


if __name__ == "__main__":
    main()
