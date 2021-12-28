import requests
from loguru import logger


class SocialSlack(object):

    """Social Messaging sink to output to Slack."""

    def __init__(self, **kwargs):
        self.web_hook = kwargs.get('webhook_url', '')
        if self.web_hook == '':
            raise ValueError('webhook_url parameter is not defined.')
        else:
            self.output_timestamp = kwargs.get('output_timestamp', False)

    def send_message(self, msg, timestamp):
        try:
            if self.output_timestamp:
                post_msg = '{} - {}'.format(msg, timestamp)
            else:
                post_msg = msg

            # We ignore the response body and headers of a successful post.
            requests.post(self.web_hook, json={'text': post_msg})
        except Exception as e:  # pragma: no cover
            logger.warning('Error posting to slack: {}'.format(e))
