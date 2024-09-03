import http.client
from html.parser import HTMLParser
import json
from http.server import BaseHTTPRequestHandler, HTTPServer


# Step 1: Fetch HTML content from time.com
def fetch_html():
    conn = http.client.HTTPSConnection("time.com")
    conn.request("GET", "/")
    response = conn.getresponse()
    html = response.read().decode('utf-8')
    conn.close()
    return html


# Step 2: Parse HTML to extract titles and links of the latest 6 stories
class TimeHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_latest_stories = False
        self.in_story_item = False
        self.stories = []
        self.current_story = {}
        self.story_count = 0

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)

        # Detect the start of the latest stories section
        if tag == "div" and "class" in attrs_dict and "latest-stories" in attrs_dict["class"]:
            self.in_latest_stories = True
            print("Entered latest stories section.")

        # Detect each story item within the latest stories section
        if self.in_latest_stories and tag == "li" and "class" in attrs_dict and "latest-stories__item" in attrs_dict["class"]:
            self.in_story_item = True
            self.current_story = {}
            print("Found a new story item.")

        # Capture links within story items
        if self.in_story_item and tag == "a" and "href" in attrs_dict:
            self.current_story["link"] = "https://time.com" + attrs_dict["href"]
            print(f"Found story link: {self.current_story['link']}")

    def handle_endtag(self, tag):
        if tag == "li" and self.in_story_item:
            self.in_story_item = False

            # Once we have a complete story, store it
            if len(self.current_story) == 2:
                self.stories.append(self.current_story)
                print(f"Added story: {self.current_story['title']}")
                self.story_count += 1

            # Stop after capturing 6 stories
            if self.story_count >= 6:
                self.in_latest_stories = False

    def handle_data(self, data):
        if self.in_story_item and "title" not in self.current_story and data.strip():
            self.current_story["title"] = data.strip()
            print(f"Found story title: {self.current_story['title']}")


def get_latest_stories():
    html = fetch_html()
    parser = TimeHTMLParser()
    parser.feed(html)
    print(f"Total stories found: {len(parser.stories)}")
    return parser.stories


# Step 3: Create a Simple HTTP Server to serve the API
class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/getTimeStories':
            stories = get_latest_stories()
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(stories).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()


def run(server_class=HTTPServer, handler_class=RequestHandler, port=8000):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f'Starting server on port {port}...')
    httpd.serve_forever()


if __name__ == "__main__":
    run()
