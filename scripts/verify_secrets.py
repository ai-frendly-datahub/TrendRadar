#!/usr/bin/env python3
"""GitHub Secrets 검증 스크립트

TrendRadar에 필요한 모든 환경 변수(API 키)가 올바르게 설정되었는지 검증합니다.

사용법:
    # 로컬 환경 검증
    export NAVER_CLIENT_ID="your_id"
    export NAVER_CLIENT_SECRET="your_secret"
    python scripts/verify_secrets.py

    # GitHub Actions에서 자동 실행 (워크플로우에 포함)
    python scripts/verify_secrets.py
"""

from __future__ import annotations

import os
import sys
from typing import NamedTuple


class SecretInfo(NamedTuple):
    name: str
    required: bool
    category: str
    description: str


SECRETS = [
    SecretInfo(
        name="NAVER_CLIENT_ID",
        required=True,
        category="Naver DataLab",
        description="네이버 데이터랩 API Client ID",
    ),
    SecretInfo(
        name="NAVER_CLIENT_SECRET",
        required=True,
        category="Naver DataLab",
        description="네이버 데이터랩 API Client Secret",
    ),
    SecretInfo(
        name="YOUTUBE_API_KEY",
        required=False,
        category="YouTube",
        description="YouTube Data API v3 키",
    ),
    SecretInfo(
        name="REDDIT_CLIENT_ID",
        required=False,
        category="Reddit",
        description="Reddit API Client ID",
    ),
    SecretInfo(
        name="REDDIT_CLIENT_SECRET",
        required=False,
        category="Reddit",
        description="Reddit API Client Secret",
    ),
    SecretInfo(
        name="REDDIT_USER_AGENT",
        required=False,
        category="Reddit",
        description="Reddit API User-Agent",
    ),
]


def mask_value(value: str) -> str:
    if len(value) <= 4:
        return "***"
    return f"{value[:4]}***"


def verify_secret(secret: SecretInfo) -> bool:
    value = os.getenv(secret.name)

    if value:
        masked = mask_value(value)
        print(f"  ✅ {secret.name}: {masked}")
        print(f"     {secret.description}")
        return True
    elif secret.required:
        print(f"  ❌ {secret.name}: 설정되지 않음 (필수)")
        print(f"     {secret.description}")
        return False
    else:
        print(f"  ⚠️  {secret.name}: 설정되지 않음 (선택)")
        print(f"     {secret.description}")
        return True


def verify_reddit_user_agent() -> bool:
    user_agent = os.getenv("REDDIT_USER_AGENT")
    if not user_agent:
        return True

    required_parts = [":", "(by /u/"]

    if all(part in user_agent for part in required_parts):
        print("\n  ℹ️  Reddit User-Agent 형식이 올바릅니다.")
        return True
    else:
        print("\n  ⚠️  Reddit User-Agent 형식이 권장 형식과 다릅니다.")
        print("     권장: <platform>:<app_id>:<version> (by /u/<username>)")
        print(f"     현재: {user_agent}")
        print("     계속 진행하지만, Reddit API가 차단될 수 있습니다.")
        return True


def main() -> int:
    print("=" * 60)
    print("TrendRadar GitHub Secrets 검증")
    print("=" * 60)

    categories: dict[str, list[SecretInfo]] = {}
    for secret in SECRETS:
        if secret.category not in categories:
            categories[secret.category] = []
        categories[secret.category].append(secret)

    results = []

    for category, secrets in categories.items():
        is_required = any(s.required for s in secrets)
        priority = "🔴 필수" if is_required else "🟡 선택"

        print(f"\n{priority}: {category}")
        print("-" * 60)

        for secret in secrets:
            results.append(verify_secret(secret))

    verify_reddit_user_agent()

    print("\n" + "=" * 60)
    print("검증 결과 요약")
    print("=" * 60)

    required_secrets = [s for s in SECRETS if s.required]
    optional_secrets = [s for s in SECRETS if not s.required]

    required_set = all(os.getenv(s.name) for s in required_secrets)
    optional_count = sum(1 for s in optional_secrets if os.getenv(s.name))

    if required_set:
        print("✅ 필수 Secret 모두 설정됨")
    else:
        print("❌ 일부 필수 Secret 누락")
        print("\n   누락된 Secret:")
        for secret in required_secrets:
            if not os.getenv(secret.name):
                print(f"   - {secret.name}: {secret.description}")

    print(f"\n🟡 선택 Secret: {optional_count}/{len(optional_secrets)}개 설정됨")

    print("\n" + "=" * 60)
    if required_set:
        print("🎉 검증 완료!")
        print("\n다음 단계:")
        print("  1. GitHub 리포지토리 Settings > Secrets에 동일하게 추가")
        print("  2. GitHub Actions 워크플로우 실행")
        print("  3. TrendRadar 데이터 수집 시작")

        if optional_count < len(optional_secrets):
            print("\n선택 Secret을 추가하면 더 많은 데이터 소스를 사용할 수 있습니다:")
            for secret in optional_secrets:
                if not os.getenv(secret.name):
                    print(f"  - {secret.name}: {secret.description}")

        return 0
    else:
        print("⚠️  필수 Secret이 누락되었습니다.")
        print("\n다음 단계:")
        print("  1. 누락된 API 키 발급:")
        print("     - docs/API_KEYS.md 참조")
        print("  2. 환경 변수 설정:")
        print("     - 로컬: .env 파일 생성")
        print("     - GitHub: Settings > Secrets 추가")
        print("  3. 다시 검증 실행:")
        print("     - python scripts/verify_secrets.py")
        return 1


if __name__ == "__main__":
    sys.exit(main())
