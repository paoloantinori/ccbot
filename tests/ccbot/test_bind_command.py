"""Tests for bind_command: attach an existing tmux window to this topic."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def _make_update(text: str, user_id: int = 1, thread_id: int = 42) -> MagicMock:
    """Build a minimal mock Update with message text in a forum topic."""
    update = MagicMock()
    update.effective_user = MagicMock()
    update.effective_user.id = user_id
    update.message = MagicMock()
    update.message.text = text
    update.message.message_thread_id = thread_id
    update.message.chat = MagicMock()
    update.message.chat.type = "supergroup"
    update.message.chat.id = -1004294176884
    return update


def _make_context(args: list) -> MagicMock:
    context = MagicMock()
    context.bot = AsyncMock()
    context.user_data = {}
    context.args = args
    return context


def _window(wid: str, name: str) -> MagicMock:
    w = MagicMock()
    w.window_id = wid
    w.window_name = name
    return w


class TestBindCommand:
    @pytest.mark.asyncio
    async def test_bind_by_name_displaces_stale_bindings(self):
        """/bind planner binds topic->@6 and unbinds other topics on @6."""
        update = _make_update("/bind planner")
        context = _make_context(["planner"])
        window = _window("@6", "planner")

        with (
            patch("ccbot.bot.is_user_allowed", return_value=True),
            patch("ccbot.bot.session_manager") as mock_sm,
            patch("ccbot.bot.tmux_manager") as mock_tmux,
            patch("ccbot.bot.safe_reply", new_callable=AsyncMock) as mock_reply,
            patch("ccbot.bot.clear_topic_state", new_callable=AsyncMock),
        ):
            mock_sm.iter_thread_bindings.return_value = [
                (1, 999, "@6"),   # stale topic on the same window
                (1, 42, "@1"),   # this topic's previous window
            ]
            mock_sm.get_window_for_thread.return_value = "@1"
            mock_tmux.find_window_by_name = AsyncMock(return_value=window)
            mock_tmux.find_window_by_id = AsyncMock(return_value=None)
            mock_tmux.list_windows = AsyncMock(return_value=[window])

            from ccbot.bot import bind_command

            await bind_command(update, context)

            mock_sm.set_group_chat_id.assert_called_once_with(1, 42, -1004294176884)
            mock_sm.unbind_thread.assert_called_once_with(1, 999)
            mock_sm.bind_thread.assert_called_once_with(1, 42, "@6")
            assert "planner" in mock_reply.call_args[0][1]

    @pytest.mark.asyncio
    async def test_bind_by_window_id(self):
        """/bind @6 resolves by id when the name lookup misses."""
        update = _make_update("/bind @6")
        context = _make_context(["@6"])
        window = _window("@6", "planner")

        with (
            patch("ccbot.bot.is_user_allowed", return_value=True),
            patch("ccbot.bot.session_manager") as mock_sm,
            patch("ccbot.bot.tmux_manager") as mock_tmux,
            patch("ccbot.bot.safe_reply", new_callable=AsyncMock),
            patch("ccbot.bot.clear_topic_state", new_callable=AsyncMock),
        ):
            mock_sm.iter_thread_bindings.return_value = []
            mock_sm.get_window_for_thread.return_value = None
            mock_tmux.find_window_by_id = AsyncMock(return_value=window)
            mock_tmux.find_window_by_name = AsyncMock(return_value=None)

            from ccbot.bot import bind_command

            await bind_command(update, context)

            mock_sm.bind_thread.assert_called_once_with(1, 42, "@6")

    @pytest.mark.asyncio
    async def test_bind_unknown_window_lists_available(self):
        """/bind nosuch replies with the available window names."""
        update = _make_update("/bind nosuch")
        context = _make_context(["nosuch"])

        with (
            patch("ccbot.bot.is_user_allowed", return_value=True),
            patch("ccbot.bot.session_manager") as mock_sm,
            patch("ccbot.bot.tmux_manager") as mock_tmux,
            patch("ccbot.bot.safe_reply", new_callable=AsyncMock) as mock_reply,
        ):
            mock_tmux.find_window_by_name = AsyncMock(return_value=None)
            mock_tmux.find_window_by_id = AsyncMock(return_value=None)
            mock_tmux.list_windows = AsyncMock(
                return_value=[_window("@6", "planner"), _window("@1", "local_ai")]
            )

            from ccbot.bot import bind_command

            await bind_command(update, context)

            mock_sm.bind_thread.assert_not_called()
            assert "planner" in mock_reply.call_args[0][1]

    @pytest.mark.asyncio
    async def test_bind_requires_topic(self):
        """Outside a topic the command refuses."""
        update = _make_update("/bind planner", thread_id=None)
        context = _make_context(["planner"])

        with (
            patch("ccbot.bot.is_user_allowed", return_value=True),
            patch("ccbot.bot.safe_reply", new_callable=AsyncMock) as mock_reply,
        ):
            from ccbot.bot import bind_command

            await bind_command(update, context)

            assert "topic" in mock_reply.call_args[0][1]
