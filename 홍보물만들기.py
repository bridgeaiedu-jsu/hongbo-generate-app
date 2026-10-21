import os
import shutil
import traceback
from datetime import datetime

import 사진변환


def archive_old_results():
    """완성 폴더에 있던 이전 결과를 완성\\이전\\날짜_시간 폴더로 옮긴다 (지우지 않음)."""
    out = 사진변환.OUTPUT
    if not out.exists():
        return
    old = [p for p in out.iterdir() if p.is_file()]
    if not old:
        return
    dest = out / "이전" / datetime.now().strftime("%Y-%m-%d_%H%M%S")
    dest.mkdir(parents=True)
    for p in old:
        shutil.move(str(p), str(dest / p.name))
    print(f"이전 결과 {len(old)}개를 '완성\\이전' 폴더로 옮겼어요.")


def main():
    archive_old_results()
    사진변환.main()
    if 사진변환.OUTPUT.exists():
        os.startfile(사진변환.OUTPUT)  # 완성 폴더 열기


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print("문제가 생겼어요. 아래 내용을 Claude에게 알려주세요.")
        traceback.print_exc()
    input("\n끝났어요. 엔터를 누르면 창이 닫혀요.")
