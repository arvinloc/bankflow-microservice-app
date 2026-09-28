import time

from httpx import AsyncClient, HTTPError
from app.config import settings


class TransferRejected(Exception):
    """Класс, когда accounts service ответил, что перевод отклонент по причинам бизнес-логики"""

    def __init__(self, code):
        self.code = code


class AccountsUnavailable(Exception):
    """Исключение, когда счета не существует"""


class AccountsClient:
    def __init__(self) -> None:
        self._http = AsyncClient(
            base_url=settings.accounts_service_url,
            timeout=5.0
        )
        self._token: str | None = None
        self._expires_at = 0.0

    async def _get_token(self) -> str:
        if self._token and time.monotonic() < self._expires_at:
            return self._token

        response = await self._http.post(
            settings.keycloak_token_url,
            data={
                "grant_type": "client_credentials",
                "client_id": settings.keycloak_client_id,
                "client_secret": settings.keycloak_client_secret,
            },

        )

        response.raise_for_status()

        data = response.json()

        self._token = data["access_token"]

        self._expires_at = time.monotonic() + data["expires_in"] - 30

        return self._token

    async def apply_transfer(self, tx) -> None:
        try:
            token = await self._get_token()
            response = await self._http.post(
                "/internal/transfers",

                headers={"Authorization": f"Bearer {token}"},

                json={
                    "transaction_id": str(tx.id),
                    "user_id": str(tx.user_id),
                    "from_account_id": str(tx.from_account_id),
                    "to_account_number": tx.to_account_number,
                    "amount": str(tx.amount),
                    "currency": tx.currency,
                },
            )
        except HTTPError as e:
            raise AccountsUnavailable(str(e)) from e

        if response.status_code == 200:
            return
        if response.status_code == 409:
            raise TransferRejected(response.json()["detail"]["code"])
        raise AccountsUnavailable(
            f"accounts-service response: {response.status_code}")

    async def close(self) -> None:
        await self._http.aclose()


accounts_client = AccountsClient()
