# fonts/ — 제안 슬라이드 글꼴 (자동 설치)

`install.sh`가 스킬과 함께 설치한다. 따로 하려면 `bash fonts/install-fonts.sh` (Windows는 `install-fonts.ps1`을 부른다).
관리자 권한이 없어도 된다 — 현재 사용자 계정에만 설치된다. 설치 뒤 Figma·PowerPoint·브라우저를 다시 열면 보인다.

| 글꼴 | 굵기 | 쓰는 곳 | 출처 | 라이선스 |
|---|---|---|---|---|
| **Freesentation** | 1 Thin ~ 9 Black (9종, TTF) | **제안 슬라이드 기본 글꼴**(`deck.md` §4 — 실측 3덱 전부 이 글꼴). 제목·라벨 7 Bold, 본문 4 Regular·5 Medium, 쪽번호 3 Light, 큰 숫자 9 Black. 한글 Noto Sans KR + 영문 Roboto(Heebo) 계열 | 이주임(freesentation.blog) · 사본 [fonts-archive/Freesentation](https://github.com/fonts-archive/Freesentation) | SIL OFL 1.1 |
| **Paperlogy** | 1 Thin ~ 9 Black (9종, TTF) | 같은 제작자의 두 번째 발표용 글꼴. 한글 지마켓산스 + 영문 Montserrat 계열로 기하학적이고 폭이 넓다. **표지·PART 구분·큰 숫자 같은 표시용**으로 쓰거나, 발주처 분위기가 더 부드러울 때 Freesentation 대신 본문에 쓴다. 한 덱 안에서 둘을 섞으면 표시(Paperlogy) / 본문(Freesentation)으로 역할을 나눈다 | 이주임(freesentation.blog) · 사본 [fonts-archive/Paperlogy](https://github.com/fonts-archive/Paperlogy) | SIL OFL 1.1 |

OFL 1.1은 상업 이용·수정·재배포를 허용하고, 글꼴 단독 판매와 라이선스 변경만 막는다(`OFL.txt`). 그래서 이 저장소에 담아 배포할 수 있다.
각 폴더의 `README-upstream.md`는 원본 저장소의 안내문 그대로다. woff·otf는 넣지 않았다(HTML 초안은 회사 토큰 글꼴을 쓰고, 슬라이드는 Figma·PowerPoint에 설치된 TTF를 쓴다).

## 정본 관계
- HTML 초안(`render_html.py`)의 글꼴은 회사 토큰(Geist → Pretendard)이다. 이 폴더의 글꼴은 **Figma 슬라이드·발표자료** 단계에서 쓴다.
- Figma 파일에 글꼴이 없다고 나오면 이 설치가 안 된 것이다. `bash fonts/install-fonts.sh --force` 후 Figma를 다시 연다.
