# Daily Tech News YouTube Rework Plan v1

## 목표
Daily Tech News를 단순 자동 브리핑 채널에서, 클릭되고 유지되는 YouTube형 뉴스 포맷으로 전환한다.

## 1단계 범위
- YOUTUBE_RULES.md 개정
- story pack 생성 단계 추가
- audio_pipeline hook-first 구조 전환
- YouTube 기본 공개정책을 unlisted 우선으로 변경

## 비범위
- video_pipeline 대규모 리빌드
- Shorts 운영 자동화
- CTA 최적화
- 썸네일 자동 최종 선택
- Remotion 재도입

## 새 파이프라인 구조
1. 기사 수집
2. post.md / archive 생성
3. story pack 생성
4. hook-first 오디오 스크립트 생성
5. 이미지 생성
6. 비디오 생성
7. 유튜브 메타데이터 생성
8. unlisted 업로드
9. 수동 검수 후 public 전환

## story pack 역할
story pack은 웹용 단신과 유튜브용 패키징을 분리하는 중간 계층이다.

포함 요소:
- 메인 이슈
- supporting issue
- 훅 후보
- 제목 후보
- 썸네일 카피 후보
- narrative skeleton

## 성공 기준
- 브리핑형 제목 반복 감소
- 메인 이슈 중심 메타데이터 생성 가능
- 오디오 스크립트가 나열형에서 탈피
- 유튜브 업로드 기본값이 unlisted로 전환

## 다음 단계 후보
- video_pipeline에 인트로/자막/장면 템포 반영
- 썸네일 후보 자동 생성기 추가
- 주간 정리 영상 포맷 설계
