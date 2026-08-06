# 매장 사진을 인스타그램용 정사각형(1080x1080) 사진으로 자동 변환하는 스크립트
# 실행: python 인스타변환.py

import re
from pathlib import Path
from datetime import date
from PIL import Image, ImageStat

BASE_DIR = Path(__file__).parent
INPUT_DIR = BASE_DIR / "사진"
자료_DIR = BASE_DIR / "자료"
OUTPUT_DIR = BASE_DIR / "완성"
SIZE = 1080
지원확장자 = (".jpg", ".jpeg", ".png")
로고_후보 = (BASE_DIR / "로고.jpg", BASE_DIR / "로고.png")
로고_비율 = 0.15  # 사진 가로폭 대비 로고 크기
로고_여백 = 40  # 가장자리에서 안쪽으로 띄울 픽셀
로고_불투명도 = 0.9  # 로고 진하기(90% 불투명)
밝기_기준 = 128  # 0~255, 이보다 배경이 어두우면 흰 로고, 밝으면 검은 로고
가게정보_후보 = (
    BASE_DIR / "가게정보.txt",
    BASE_DIR / "가게 정보.txt",
    자료_DIR / "가게정보.txt",
    자료_DIR / "가게 정보.txt",
)


def 로고_찾기():
    for 경로 in 로고_후보:
        if 경로.is_file():
            return 경로
    return None


def 로고_합성(img: Image.Image, 로고경로: Path) -> Image.Image:
    with Image.open(로고경로) as 원본로고:
        원본로고 = 원본로고.convert("RGBA")

        로고_가로 = int(SIZE * 로고_비율)
        로고_세로 = int(원본로고.height * (로고_가로 / 원본로고.width))
        원본로고 = 원본로고.resize((로고_가로, 로고_세로), Image.LANCZOS)

        x = SIZE - 로고_여백 - 로고_가로
        y = SIZE - 로고_여백 - 로고_세로

        # 로고가 들어갈 자리의 배경이 밝은지 어두운지 살펴보기
        배경자리 = img.convert("RGB").crop((x, y, x + 로고_가로, y + 로고_세로))
        평균밝기 = ImageStat.Stat(배경자리.convert("L")).mean[0]
        로고_색 = (255, 255, 255) if 평균밝기 < 밝기_기준 else (20, 20, 20)

        # 로고 모양(알파 채널)은 그대로 두고, 색만 배경에 맞춰 바꾸기
        알파 = 원본로고.split()[-1].point(lambda a: int(a * 로고_불투명도))
        색바뀐_로고 = Image.new("RGBA", 원본로고.size, 로고_색 + (0,))
        색바뀐_로고.putalpha(알파)

        img = img.convert("RGBA")
        img.paste(색바뀐_로고, (x, y), mask=색바뀐_로고)
        return img.convert("RGB")


def 정사각형으로_자르고_키우기(img: Image.Image) -> Image.Image:
    # 투명 배경(PNG)은 흰색 배경으로 바꿔줌
    if img.mode in ("RGBA", "P"):
        배경 = Image.new("RGB", img.size, (255, 255, 255))
        배경.paste(img.convert("RGBA"), mask=img.convert("RGBA").split()[-1])
        img = 배경
    else:
        img = img.convert("RGB")

    # 가운데 기준으로 짧은 변에 맞춰 정사각형으로 자르기 (찌그러짐 없음)
    가로, 세로 = img.size
    한변 = min(가로, 세로)
    왼쪽 = (가로 - 한변) // 2
    위 = (세로 - 한변) // 2
    img = img.crop((왼쪽, 위, 왼쪽 + 한변, 위 + 한변))

    # 1080x1080으로 맞추기
    img = img.resize((SIZE, SIZE), Image.LANCZOS)
    return img


def 가게정보_찾기():
    for 경로 in 가게정보_후보:
        if 경로.is_file():
            return 경로
    return None


def 가게정보_읽기(경로: Path):
    try:
        원문 = 경로.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        원문 = 경로.read_text(encoding="cp949")

    라벨값 = {}
    프로모목록 = []
    프로모_섹션인가 = False

    for 줄 in 원문.splitlines():
        줄 = 줄.strip()
        if not 줄:
            프로모_섹션인가 = False
            continue
        if 줄.startswith("이번 주 홍보할 것"):
            프로모_섹션인가 = True
            continue
        if 프로모_섹션인가 and 줄.startswith("-"):
            프로모목록.append(줄.lstrip("-").strip())
            continue
        if ":" in 줄:
            프로모_섹션인가 = False
            라벨, 값 = 줄.split(":", 1)
            라벨값[라벨.strip()] = 값.strip()

    return 라벨값, 프로모목록


def 지역_키워드(위치: str):
    토큰 = 위치.split()
    결과 = []
    if len(토큰) >= 2:
        결과.append(토큰[0] + 토큰[1])
    if 토큰:
        결과.append(토큰[0])
    if len(토큰) > 2:
        결과.append("".join(토큰[2:]))
    return [t for t in dict.fromkeys(결과) if t]


def 업종_키워드(특징: str):
    결과 = ["카페"]
    if "로스팅" in 특징 or "로스터리" in 특징:
        결과.append("로스터리카페")
    if "스페셜티" in 특징:
        결과.append("스페셜티커피")
    if "베이커리" in 특징 or "빵" in 특징:
        결과.append("베이커리카페")
    return 결과


def 메뉴_키워드(프로모목록, 특징: str):
    합친텍스트 = " ".join(프로모목록) + " " + 특징
    후보 = re.findall(r"['\"]([^'\"]{1,10})['\"]", 합친텍스트)
    일반메뉴 = ["아메리카노", "라떼", "콜드브루", "에스프레소", "카푸치노", "마키아토", "디카페인"]
    for 단어 in 일반메뉴:
        if 단어 in 합친텍스트 and 단어 not in 후보:
            후보.append(단어)
    return [m.replace(" ", "") for m in 후보]


def 해시태그_만들기(위치: str, 특징: str, 프로모목록):
    태그모음 = []
    for t in 지역_키워드(위치):
        태그모음.append(f"#{t}카페")
    for t in 메뉴_키워드(프로모목록, 특징):
        태그모음.append(f"#{t}")
    for t in 업종_키워드(특징):
        태그모음.append(f"#{t}")

    여분 = ["#카페스타그램", "#커피스타그램", "#동네카페", "#카페추천", "#오늘의커피", "#카페그램", "#커피있는일상"]
    for t in 여분:
        if len(태그모음) >= 10:
            break
        태그모음.append(t)

    최종 = list(dict.fromkeys(태그모음))
    return 최종[:10]


def 다듬기(문장: str, 최대: int = 170) -> str:
    if len(문장) <= 최대:
        return 문장
    잘림 = 문장[:최대]
    마지막공백 = 잘림.rfind(" ")
    if 마지막공백 > 0:
        잘림 = 잘림[:마지막공백]
    return 잘림.rstrip(",.、 ") + "…"


def 감성형_문구(이름, 위치, 특징):
    특징문장 = 특징 if 특징 else "정성껏 커피를 준비합니다"
    문장 = (
        f"{위치}에 위치한 {이름}입니다.\n"
        f"{특징문장}.\n"
        f"조용히 앉아 쉬어가기 좋은 자리를 마련해두었습니다.\n"
        f"편하게 들러주시기 바랍니다."
    )
    return 다듬기(문장)


def 정보형_문구(이름, 위치, 프로모목록):
    if 프로모목록:
        프로모줄 = "\n".join(f"{p}." for p in 프로모목록[:2])
    else:
        프로모줄 = "이번 주에도 좋은 재료로 메뉴를 준비했습니다."
    문장 = (
        f"{이름} 소식을 전해드립니다.\n"
        f"{프로모줄}\n"
        f"많은 이용 부탁드립니다."
    )
    return 다듬기(문장)


def 이벤트형_문구(이름, 위치, 프로모목록):
    if 프로모목록:
        프로모줄 = "\n".join(f"{p}." for p in 프로모목록[:2])
    else:
        프로모줄 = "이번 주 소식을 준비했습니다."
    문장 = (
        f"이번 주 {이름} 소식입니다.\n"
        f"{프로모줄}\n"
        f"{위치}에서 기다리겠습니다."
    )
    return 다듬기(문장)


def 네이버블로그_문구(이름, 위치, 특징, 고객층, 프로모목록):
    특징문장 = 특징 if 특징 else "정성껏 커피를 준비하는 곳입니다"
    고객층문장 = f" {고객층}이 자주 찾아주십니다." if 고객층 else ""

    if 프로모목록:
        프로모문장 = " ".join(f"{p}." for p in 프로모목록)
    else:
        프로모문장 = "이번 주에도 좋은 재료로 정성껏 메뉴를 준비했습니다."

    문장 = (
        f"{위치}에 자리한 {이름}를 소개합니다.\n"
        f"{특징문장}.{고객층문장}\n"
        f"조용히 앉아 커피 한 잔 즐기기 좋은 공간입니다.\n\n"
        f"이번 주 소식도 전해드립니다.\n{프로모문장}\n"
        f"근처를 지나신다면 편하게 들러주시기 바랍니다."
    )
    return 다듬기(문장, 320)


def 카카오톡_공지(이름, 프로모목록):
    줄들 = [f"안녕하세요, {이름}입니다."]
    if 프로모목록:
        줄들.append(프로모목록[0] + ".")
    else:
        줄들.append("이번 주에도 좋은 메뉴로 찾아뵙겠습니다.")
    줄들.append("항상 찾아주셔서 감사합니다.")
    return "\n".join(줄들[:3])


def 홍보문구_만들기():
    경로 = 가게정보_찾기()
    if not 경로:
        return None

    라벨값, 프로모목록 = 가게정보_읽기(경로)
    이름 = 라벨값.get("가게 이름", "저희 가게")
    위치 = 라벨값.get("위치", "")
    특징 = 라벨값.get("가게 특징", "")
    고객층 = 라벨값.get("주 고객층", "")

    감성형 = 감성형_문구(이름, 위치, 특징)
    정보형 = 정보형_문구(이름, 위치, 프로모목록)
    이벤트형 = 이벤트형_문구(이름, 위치, 프로모목록)
    해시태그 = 해시태그_만들기(위치, 특징, 프로모목록)
    블로그문구 = 네이버블로그_문구(이름, 위치, 특징, 고객층, 프로모목록)
    카톡문구 = 카카오톡_공지(이름, 프로모목록)

    내용 = (
        f"=== 인스타그램용 ===\n\n"
        f"[감성형]\n{감성형}\n\n"
        f"[정보형]\n{정보형}\n\n"
        f"[이벤트형]\n{이벤트형}\n\n"
        f"[해시태그]\n{' '.join(해시태그)}\n\n"
        f"=== 네이버 블로그용 ===\n\n"
        f"{블로그문구}\n\n"
        f"=== 카카오톡 단골 공지용 ===\n\n"
        f"{카톡문구}\n"
    )

    저장경로 = OUTPUT_DIR / "홍보문구.txt"
    저장경로.write_text(내용, encoding="utf-8")
    return 저장경로


def main():
    INPUT_DIR.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(exist_ok=True)

    로고파일이름 = {경로.name for 경로 in 로고_후보}

    파일목록 = []
    for 폴더 in (INPUT_DIR, 자료_DIR):
        if not 폴더.is_dir():
            continue
        for f in sorted(폴더.iterdir()):
            if f.is_file() and f.suffix.lower() in 지원확장자 and f.name not in 로고파일이름:
                파일목록.append(f)

    if not 파일목록:
        print(f"'{INPUT_DIR.name}' 폴더와 '{자료_DIR.name}' 폴더에 사진이 없어요. 사진을 넣고 다시 실행해 주세요.")
    else:
        오늘 = date.today().strftime("%Y%m%d")
        성공 = 0

        로고경로 = 로고_찾기()
        if 로고경로:
            print(f"로고 파일을 찾았어요: {로고경로.name} (사진마다 오른쪽 아래에 넣을게요)")

        for i, 파일 in enumerate(파일목록, start=1):
            try:
                with Image.open(파일) as img:
                    결과 = 정사각형으로_자르고_키우기(img)
                    if 로고경로:
                        결과 = 로고_합성(결과, 로고경로)
                    저장이름 = f"{오늘}_{i:02d}.jpg"
                    결과.save(OUTPUT_DIR / 저장이름, "JPEG", quality=90)
                    성공 += 1
                    print(f"완료: {파일.name} -> {저장이름}")
            except Exception as e:
                print(f"이 사진은 처리할 수 없어요 ({파일.name}): {e}")

        print(f"총 {성공}장을 '{OUTPUT_DIR.name}' 폴더에 저장했어요.")

    문구경로 = 홍보문구_만들기()
    if 문구경로:
        print(f"\n홍보 문구도 만들었어요: {문구경로.name} (감성형/정보형/이벤트형 + 해시태그)")
    else:
        print(f"\n'가게정보.txt' 파일이 없어서 홍보 문구는 건너뛰었어요.")


if __name__ == "__main__":
    main()
