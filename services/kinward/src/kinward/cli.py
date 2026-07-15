from __future__ import annotations

import argparse
import asyncio
import sys

from kinward.application.integration_tokens import create_token, list_tokens, revoke_token
from kinward.config import get_settings
from kinward.persistence.session import create_session_factory


async def _create(name: str) -> None:
    factory = create_session_factory(get_settings())
    async with factory() as session:
        record, plaintext = await create_token(session, name)
        await session.commit()
    print("Integration token created. This value is shown only once - store it now.")
    print(f"  id:    {record.id}")
    print(f"  name:  {record.name}")
    print(f"  token: {plaintext}")


async def _list() -> None:
    factory = create_session_factory(get_settings())
    async with factory() as session:
        records = await list_tokens(session)
    if not records:
        print("No integration tokens exist.")
        return
    for record in records:
        state = "revoked" if record.revoked_at else "active"
        last_used = record.last_used_at.isoformat() if record.last_used_at else "never"
        print(f"{record.id}  {state:8}  {record.name!r}  last_used={last_used}")


async def _revoke(token_id: str) -> None:
    factory = create_session_factory(get_settings())
    async with factory() as session:
        revoked = await revoke_token(session, token_id)
        await session.commit()
    if not revoked:
        print(f"No active token with id {token_id!r} was found.", file=sys.stderr)
        raise SystemExit(1)
    print(f"Token {token_id} revoked.")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="python -m kinward.cli")
    subparsers = parser.add_subparsers(dest="command", required=True)

    create_parser = subparsers.add_parser(
        "create-integration-token", help="Mint a new Home Assistant integration service token."
    )
    create_parser.add_argument("--name", required=True, help="A label to identify this token later.")

    subparsers.add_parser("list-integration-tokens", help="List integration tokens.")

    revoke_parser = subparsers.add_parser(
        "revoke-integration-token", help="Revoke an integration token."
    )
    revoke_parser.add_argument("token_id", help="The token id to revoke.")

    args = parser.parse_args(argv)

    if args.command == "create-integration-token":
        asyncio.run(_create(args.name))
    elif args.command == "list-integration-tokens":
        asyncio.run(_list())
    elif args.command == "revoke-integration-token":
        asyncio.run(_revoke(args.token_id))


if __name__ == "__main__":
    main()
