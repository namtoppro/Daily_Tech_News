#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YouTube upload pipeline for Daily Tech News.
- Reads today's generated mp4 + metadata json
- Uses OAuth installed-app flow for YouTube Data API v3
- Uploads with privacyStatus defaulting to configured env policy
- Keeps upload isolated from text/audio/image/video generation
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

load_dotenv()

TODAY = datetime.now().strftime('%Y-%m-%d')
ARCHIVE_DIR = Path(os.getenv('ARCHIVE_DIR', 'archive'))
SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
YOUTUBE_CLIENT_SECRET_FILE = os.getenv('YOUTUBE_CLIENT_SECRET_FILE', 'youtube_client_secret.json')
YOUTUBE_TOKEN_FILE = os.getenv('YOUTUBE_TOKEN_FILE', 'youtube_token.json')
YOUTUBE_DEFAULT_PRIVACY = os.getenv('YOUTUBE_DEFAULT_PRIVACY', 'unlisted').strip().lower() or 'unlisted'
YOUTUBE_DEFAULT_CATEGORY_ID = os.getenv('YOUTUBE_DEFAULT_CATEGORY_ID', '28').strip() or '28'
YOUTUBE_DEFAULT_LANGUAGE = os.getenv('YOUTUBE_DEFAULT_LANGUAGE', 'ko').strip() or 'ko'
YOUTUBE_DEFAULT_PLAYLIST = os.getenv('YOUTUBE_DEFAULT_PLAYLIST', 'Daily Tech News').strip() or 'Daily Tech News'


def load_metadata() -> dict:
    meta_path = ARCHIVE_DIR / f'{TODAY}-youtube-metadata.json'
    if not meta_path.exists():
        raise RuntimeError(f'메타데이터 파일이 없습니다: {meta_path}')
    data = json.loads(meta_path.read_text(encoding='utf-8'))
    data['_meta_path'] = str(meta_path)
    return data


def get_video_path(metadata: dict) -> Path:
    video_path = Path(metadata.get('videoFile', '')).expanduser()
    if not video_path.is_absolute():
        video_path = Path.cwd() / video_path
    if not video_path.exists():
        raise RuntimeError(f'업로드할 영상 파일이 없습니다: {video_path}')
    return video_path


def get_credentials() -> Credentials:
    token_path = Path(YOUTUBE_TOKEN_FILE)
    secret_path = Path(YOUTUBE_CLIENT_SECRET_FILE)

    if not secret_path.exists():
        raise RuntimeError(
            'youtube_client_secret.json 이 없습니다. '\
            'Google Cloud Console에서 OAuth client secret을 받아 프로젝트 루트에 두거나 '\
            'YOUTUBE_CLIENT_SECRET_FILE 환경변수로 경로를 지정하세요.'
        )

    creds = None
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if creds and creds.valid:
        return creds

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(str(secret_path), SCOPES)
        creds = flow.run_local_server(port=0)

    token_path.write_text(creds.to_json(), encoding='utf-8')
    return creds


def build_description(metadata: dict) -> str:
    description = str(metadata.get('description', '')).strip()
    hashtags = metadata.get('hashtags', []) or []

    if hashtags:
        hashtag_line = ' '.join([tag for tag in hashtags if str(tag).startswith('#')])
        if hashtag_line and hashtag_line not in description:
            description = description.rstrip() + '\n' + hashtag_line
    return description.strip()


def build_tags(metadata: dict) -> list[str]:
    tags = []
    for item in metadata.get('keywords', []) or []:
        item = str(item).strip()
        if item:
            tags.append(item)
    for item in metadata.get('hashtags', []) or []:
        item = str(item).strip()
        if item.startswith('#'):
            tags.append(item.lstrip('#'))
    deduped = []
    seen = set()
    for item in tags:
        key = item.lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped[:15]


def ensure_safe_privacy(metadata: dict) -> str:
    privacy = str(metadata.get('privacyStatus', YOUTUBE_DEFAULT_PRIVACY)).strip().lower()
    if privacy not in {'private', 'unlisted', 'public'}:
        privacy = YOUTUBE_DEFAULT_PRIVACY
    if os.getenv('YOUTUBE_ALLOW_AUTO_PUBLIC', '').strip().lower() not in {'1', 'true', 'yes'} and privacy == 'public':
        raise RuntimeError('자동 업로드에서 public 공개는 차단되어 있습니다. unlisted/private를 사용하거나 YOUTUBE_ALLOW_AUTO_PUBLIC=true 를 명시하세요.')
    return privacy


def upload_video(metadata: dict) -> dict:
    creds = get_credentials()
    youtube = build('youtube', 'v3', credentials=creds)
    video_path = get_video_path(metadata)

    privacy = ensure_safe_privacy(metadata)

    title = str(metadata.get('title', '')).strip()
    if not title:
        raise RuntimeError('title 값이 비어 있습니다.')

    body = {
        'snippet': {
            'title': title,
            'description': build_description(metadata),
            'tags': build_tags(metadata),
            'categoryId': str(metadata.get('categoryId', YOUTUBE_DEFAULT_CATEGORY_ID) or YOUTUBE_DEFAULT_CATEGORY_ID),
            'defaultLanguage': str(metadata.get('defaultLanguage', YOUTUBE_DEFAULT_LANGUAGE) or YOUTUBE_DEFAULT_LANGUAGE),
        },
        'status': {
            'privacyStatus': privacy,
            'selfDeclaredMadeForKids': False,
        },
    }

    media = MediaFileUpload(str(video_path), chunksize=-1, resumable=True, mimetype='video/mp4')
    request = youtube.videos().insert(part='snippet,status', body=body, media_body=media)
    response = request.execute()

    return {
        'date': TODAY,
        'uploaded': True,
        'videoId': response.get('id'),
        'privacyStatus': privacy,
        'title': title,
        'playlistSuggestion': str(metadata.get('playlistSuggestion', YOUTUBE_DEFAULT_PLAYLIST) or YOUTUBE_DEFAULT_PLAYLIST),
        'videoFile': str(video_path),
        'metadataFile': metadata.get('_meta_path'),
        'url': f"https://www.youtube.com/watch?v={response.get('id')}" if response.get('id') else '',
    }


def save_receipt(receipt: dict) -> Path:
    out = ARCHIVE_DIR / f'{TODAY}-youtube-upload.json'
    out.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return out


def main():
    metadata = load_metadata()
    receipt = upload_video(metadata)
    receipt_path = save_receipt(receipt)
    print(f"YOUTUBE_UPLOAD_RECEIPT={receipt_path}")
    print(f"YOUTUBE_VIDEO_ID={receipt.get('videoId', '')}")
    print(f"YOUTUBE_URL={receipt.get('url', '')}")
    print(f"YOUTUBE_PRIVACY={receipt.get('privacyStatus', '')}")


if __name__ == '__main__':
    main()
