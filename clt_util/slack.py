import logging

from slackclient import SlackClient


logger = logging.getLogger(__name__)


class Slack:
    """
    Thin wrapper over slackclient for oauth, with support for web hooks.

    Using webhooks allows sending messages to multiple slack channels without enabling
    chat bot permissions.

    Slack Apps are configured at https://api.slack.com/apps, new apps can be created
    or additional web hooks added to an existing app, to use oauth the `chat:write:bot`
    permission is required.

    :param auth_token: Slack app OAuth token.
    :param enabled: Enable/Disable slack messaging.
    :param slack_channel: Optional default slack_channel to use.
    """
    def __init__(self, auth_token, enabled=False, slack_channel=None):
        self.enabled = enabled
        self.client = SlackClient(auth_token)
        self.slack_channel = slack_channel

    def post_messages(self, messages, slack_channel=None):
        """
        Send messages to Slack using OAuth.

        :param messages: List of messages to send.
        :param slack_channel: Optional override to configured default channel.
        """
        self.post_message("\n".join(messages), slack_channel=slack_channel)

    def post_message(self, message, slack_channel=None):
        """
        Send a message to Slack using OAuth.

        :param messages: Message to send.
        :param slack_channel: Optional override to configured default channel.
        """
        slack_channel = slack_channel or self.slack_channel
        if slack_channel is None:
            logger.error("Error sending message, no slack channel provided.")
            return

        if self.enabled:
            msg = "Error sending message to channel %s"
            try:
                response = self.client.api_call(
                    "chat.postMessage",
                    channel=slack_channel,
                    text=message,
                )
            except Exception:
                logger.exception(msg, slack_channel)
            else:
                if not response["ok"]:
                    logger.error(msg, slack_channel, extra={"response": response, "text": message})
        else:
            logger.debug("Slack messaging disabled, ignoring slack message")
