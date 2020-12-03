from unittest import mock

from clt_util import slack


class TestSlackClient:
    def test_init(self):
        s = slack.Slack("auth_token", enabled=True, slack_channel="slack_channel")
        assert s.enabled is True
        assert s.slack_channel == "slack_channel"

    def test_slack_handles_failures(self, monkeypatch):
        monkeypatch.setattr(slack.logger, "error", mock.Mock())
        monkeypatch.setattr(slack.SlackClient, "api_call", mock.Mock(return_value={"ok": False}))

        s = slack.Slack("auth_token", enabled=True)
        s.post_message("message", "slack-channel")

        assert slack.logger.error.call_args == mock.call(
            "Error sending message to channel %s",
            "slack-channel",
            extra={"text": "message", "response": {"ok": False}},
        )

    def test_slack_handles_exceptions(self, monkeypatch):
        monkeypatch.setattr(slack.logger, "exception", mock.Mock())
        monkeypatch.setattr(slack.SlackClient, "api_call", mock.Mock(side_effect=Exception))

        s = slack.Slack("auth_token", enabled=True)
        s.post_message("message", "slack-channel")

        assert slack.logger.exception.call_args == mock.call(
            "Error sending message to channel %s", "slack-channel",
        )

    def test_slack_handles_success(self, monkeypatch):
        monkeypatch.setattr(slack.logger, "error", mock.Mock())
        monkeypatch.setattr(slack.SlackClient, "api_call", mock.Mock(return_value={"ok": True}))

        s = slack.Slack("auth_token", enabled=True)
        s.post_message("message", "slack-channel")

        assert slack.logger.error.call_args is None

    def test_slack_post_messages(self, monkeypatch):
        monkeypatch.setattr(slack.Slack, "post_message", mock.Mock())

        s = slack.Slack("auth_token", enabled=True)
        s.post_messages(["message", "message2"], "slack-channel")

        assert s.post_message.call_args == mock.call("message\nmessage2", slack_channel="slack-channel")

    def test_slack_honours_enabled_flag(self, monkeypatch):
        monkeypatch.setattr(slack.logger, "debug", mock.Mock())

        s = slack.Slack("auth_token", enabled=False)
        s.post_messages(["message", "message2"], "slack-channel")

        assert slack.logger.debug.call_args == mock.call("Slack messaging disabled, ignoring slack message")

    def test_slack_warns_if_no_channel_provided(self, monkeypatch):
        monkeypatch.setattr(slack.logger, "error", mock.Mock())

        s = slack.Slack("auth_token", enabled=True)
        s.post_messages(["message", "message2"])

        assert slack.logger.error.call_args == mock.call("Error sending message, no slack channel provided.")

    def test_slack_posts_to_default_channel(self, monkeypatch):
        monkeypatch.setattr(slack.SlackClient, "api_call", mock.Mock(return_value={"ok": True}))

        s = slack.Slack("auth_token", enabled=True, slack_channel="default-channel")
        s.post_message("message")

        assert s.client.api_call.call_args == mock.call(
            "chat.postMessage",
            channel="default-channel",
            text="message",
        )

    def test_slack_posts_to_override_channel(self, monkeypatch):
        monkeypatch.setattr(slack.SlackClient, "api_call", mock.Mock(return_value={"ok": True}))

        s = slack.Slack("auth_token", enabled=True, slack_channel="default-channel")
        s.post_message("message", slack_channel="slack-channel")

        assert s.client.api_call.call_args == mock.call(
            "chat.postMessage",
            channel="slack-channel",
            text="message",
        )
