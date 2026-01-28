import urllib.request
import json

class FlomoPusher:
    def __init__(self, api_url):
        self.api_url = api_url

    def push(self, content):
        if not self.api_url:
            return False, "Missing flomo API URL"
        
        data = {
            "content": content
        }
        
        try:
            req = urllib.request.Request(
                self.api_url,
                data=json.dumps(data).encode('utf-8'),
                headers={'Content-Type': 'application/json'}
            )
            with urllib.request.urlopen(req) as response:
                result = response.read().decode('utf-8')
                return True, result
        except Exception as e:
            return False, str(e)
