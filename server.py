from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
import re
from datetime import datetime
import random

KNOWLEDGE_FILE = "knowledge.json"
UPLOAD_FOLDER = "uploads"

# Luo uploads-kansio jos ei ole
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Lataa knowledge base
def load_knowledge():
    if not os.path.exists(KNOWLEDGE_FILE):
        with open(KNOWLEDGE_FILE, "w") as f:
            json.dump({}, f, ensure_ascii=False, indent=2)
    with open(KNOWLEDGE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

# Tallenna knowledge base
def save_knowledge(data):
    with open(KNOWLEDGE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# Prosessoi kysymys
def process_question(question):
    knowledge = load_knowledge()
    words = re.findall(r"\w+", question.lower())
    best_match = None
    score = 0
    for topic in knowledge:
        topic_words = topic.split()
        current_score = sum(1 for w in words if w in topic_words)
        if current_score > score:
            score = current_score
            best_match = topic
    if best_match:
        return knowledge[best_match]
    return "AIvora ei tiedä tätä vielä. Käytä opetus-ominaisuutta (/teach) opettaaksesi sen."

# Opeta uusi aihe
def teach_topic(topic, explanation):
    knowledge = load_knowledge()
    knowledge[topic.lower()] = explanation
    save_knowledge(knowledge)
    return f"AIvora oppi aiheen: {topic}"

# Luo quiz
def generate_quiz(topic):
    knowledge = load_knowledge()
    if topic.lower() not in knowledge:
        return f"AIvora ei tunne aihetta '{topic}'. Opeta se ensin."
    question = f"Mitä aihe '{topic}' tarkoittaa?"
    correct_answer = knowledge[topic.lower()]
    others = list(knowledge.values())
    if correct_answer in others:
        others.remove(correct_answer)
    options = random.sample(others, min(3, len(others)))  # 3 väärää
    options.append(correct_answer)
    random.shuffle(options)
    return {"question": question, "options": options, "answer": correct_answer}

# Luo flashcard
def generate_flashcard(topic):
    knowledge = load_knowledge()
    if topic.lower() not in knowledge:
        return f"AIvora ei tunne aihetta '{topic}'. Opeta se ensin."
    return {"front": topic, "back": knowledge[topic.lower()]}

# Tallentaa läksykuvan
def save_upload(filename, data):
    path = os.path.join(UPLOAD_FOLDER, filename)
    with open(path, "wb") as f:
        f.write(data)
    return f"Tiedosto tallennettu: {filename}"

# HTTPServer handler
class AIvoraHandler(BaseHTTPRequestHandler):

    # CORS headers
    def _set_headers(self, content_type="application/json"):
        self.send_header("Content-Type", content_type + "; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    # Lähetä JSON-vastaus
    def _send_json(self, data):
        self.send_response(200)
        self._set_headers()
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode())

    # GET-request
    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self._set_headers("text/plain")
            self.end_headers()
            self.wfile.write(b"AIvora backend toimii!")
        else:
            self.send_response(404)
            self.end_headers()

    # OPTIONS-request (preflight CORS)
    def do_OPTIONS(self):
        self.send_response(200)
        self._set_headers()
        self.end_headers()

    # POST-request
    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length)
        content_type = self.headers.get('Content-Type', '')

        if "application/json" in content_type:
            data = json.loads(body)
            path = self.path

            if path == "/ask":
                question = data.get("question", "")
                answer = process_question(question)
                self._send_json({"answer": answer})

            elif path == "/teach":
                topic = data.get("topic", "")
                explanation = data.get("explanation", "")
                result = teach_topic(topic, explanation)
                self._send_json({"status": result})

            elif path == "/quiz":
                topic = data.get("topic", "")
                quiz = generate_quiz(topic)
                self._send_json(quiz)

            elif path == "/flashcards":
                topic = data.get("topic", "")
                card = generate_flashcard(topic)
                self._send_json(card)

            else:
                self.send_response(404)
                self.end_headers()

        elif "application/octet-stream" in content_type or "image" in content_type:
            filename = f"homework_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            status = save_upload(filename, body)
            self._send_json({"status": status})

        else:
            self.send_response(400)
            self.end_headers()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    server = HTTPServer(("0.0.0.0", port), AIvoraHandler)
    print(f"AIvora backend toimii portissa {port}")
    server.serve_forever()
