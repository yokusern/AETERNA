#!/usr/bin/env python3
"""
Pinterest API Client - For automatic pin creation
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()


class PinterestClient:
    """Pinterest API v5 client for creating pins"""

    API_BASE = "https://api.pinterest.com/v5"

    def __init__(self):
        self.access_token = os.getenv("PINTEREST_ACCESS_TOKEN")
        self.board_id = os.getenv("PINTEREST_BOARD_ID")
        self.app_id = os.getenv("PINTEREST_APP_ID")
        self.app_secret = os.getenv("PINTEREST_APP_SECRET")

    def is_configured(self) -> bool:
        """Check if Pinterest API is configured"""
        return bool(self.access_token and self.board_id)

    def _headers(self) -> dict:
        """Get authorization headers"""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

    def get_boards(self) -> list:
        """Get list of user's boards"""
        resp = requests.get(
            f"{self.API_BASE}/boards",
            headers=self._headers(),
            params={"page_size": 50}
        )
        resp.raise_for_status()
        return resp.json().get("items", [])

    def create_pin(
        self,
        title: str,
        description: str,
        link: str,
        image_url: str = None,
        board_id: str = None,
    ) -> dict:
        """Create a pin on Pinterest
        
        Args:
            title: Pin title (max 100 chars)
            description: Pin description (max 800 chars)
            link: Destination URL (Gumroad product link)
            image_url: Publicly accessible image URL (2:3 ratio recommended)
            board_id: Board ID to post to (uses default if not provided)
        
        Returns:
            Created pin data
        """
        target_board = board_id or self.board_id
        if not target_board:
            raise ValueError("No board_id provided and no default set")

        payload = {
            "board_id": target_board,
            "title": title[:100],
            "description": description[:800],
            "link": link,
        }

        if image_url:
            payload["media_source"] = {
                "source_type": "image_url",
                "url": image_url,
            }

        resp = requests.post(
            f"{self.API_BASE}/pins",
            headers=self._headers(),
            json=payload,
        )
        resp.raise_for_status()
        data = resp.json()
        print(f"[Pin Created] {title} (ID: {data['id']})")
        return data

    def get_pin(self, pin_id: str) -> dict:
        """Get pin details"""
        resp = requests.get(
            f"{self.API_BASE}/pins/{pin_id}",
            headers=self._headers(),
        )
        resp.raise_for_status()
        return resp.json()

    def refresh_access_token(self, refresh_token: str) -> dict:
        """Refresh access token using refresh token"""
        resp = requests.post(
            f"{self.API_BASE}/oauth/token",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": self.app_id,
                "client_secret": self.app_secret,
            },
        )
        resp.raise_for_status()
        return resp.json()


def main():
    """Test Pinterest client"""
    client = PinterestClient()

    if not client.access_token:
        print("⚠️ PINTEREST_ACCESS_TOKEN が未設定です")
        return

    print("📋 ボード一覧を取得中...")
    try:
        boards = client.get_boards()
        if not boards:
            print("ボードが見つかりません。Pinterestでボードを作成してください。")
            return
        for board in boards:
            print(f"  ボード名: {board['name']}")
            print(f"  ID: {board['id']}")
            print()
        print("👆 使いたいボードのIDを .env の PINTEREST_BOARD_ID= に貼ってください")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
