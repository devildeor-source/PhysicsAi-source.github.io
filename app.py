import os
import json
from flask import Flask, request, jsonify, render_template_string, session

app = Flask(__name__)
# This key is required so the server can "remember" which answer you just saw
app.config['SECRET_KEY'] = 'physics_support_key_2026'

# --- THE FRONTEND (HTML/CSS/JS) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { background: #0b0e14; color: white; height: 100vh; display: flex; align-items: center; justify-content: center; font-family: sans-serif; }
        .glass { background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(15px); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 30px; }
    </style>
</head>
<body>
    <div class="glass w-full max-w-sm p-8 text-center shadow-2xl">
        <div id="ai-display" class="h-72 flex flex-col items-center justify-center border-b border-white/10 mb-6 overflow-y-auto">
            <h2 class="text-gray-500 italic">Ready for your physics question...</h2>
        </div>
        <form onsubmit="event.preventDefault(); askAI(false);" class="relative">
            <input id="user-input" type="text" placeholder="Search (e.g. Reflecting Surface)" 
                class="w-full bg-white/10 p-4 rounded-full outline-none border border-white/20 focus:border-indigo-500 text-white text-center">
            <button type="submit" class="absolute right-2 top-2 bg-indigo-600 w-10 h-10 rounded-full flex items-center justify-center">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M5 10l7-7m0 0l7 7m-7-7v18" stroke-width="2" stroke-linecap="round"></path></svg>
            </button>
        </form>
    </div>
    <script>
        let currentTopic = "";
        async function askAI(isRetry) {
            const input = document.getElementById('user-input');
            const display = document.getElementById('ai-display');
            const query = isRetry ? currentTopic : input.value.trim();
            if(!query) return;
            currentTopic = query;
            display.innerHTML = '<p class="text-indigo-400 animate-pulse">Searching Records...</p>';
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ message: query, retry: isRetry })
            });
            const data = await response.json();
            display.innerHTML = data.reply;
            if(!isRetry) input.value = "";
        }
    </script>
</body>
</html>
"""

# --- THE BACKEND (Logic for ordering and changing answers) ---
@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    query = data.get("message", "").lower().strip()
    is_retry = data.get("retry", False)

    # Load data from the json file
    if os.path.exists('physics_data.json'):
        with open('physics_data.json', 'r') as f:
            db = json.load(f)
    else:
        return jsonify({"reply": "Database file missing."})

    # FILTERING: Find all matches for the specific topic
    matches = [i for i in db['entries'] if query in i['quantity'].lower()]

    if not matches:
        return jsonify({"reply": "<p class='text-gray-400'>No data found for this topic.</p>"})

    # ROTATION: Remember where we are in the list for this topic
    session_key = f"pos_{query.replace(' ', '_')}"
    idx = session.get(session_key, 0)

    if is_retry:
        idx = (idx + 1) % len(matches) # Change to next answer
    else:
        idx = 0 # Start at the beginning for a new search

    session[session_key] = idx
    item = matches[idx]

    reply = f'''
        <div class="w-full">
            <p class="text-indigo-400 text-[10px] font-bold uppercase mb-2">Result {idx+1} of {len(matches)}</p>
            <h3 class="text-xl font-bold mb-1">{item['quantity']}</h3>
            <p class="text-xs text-gray-400 italic mb-4">{item.get('formula', 'No formula')}</p>
            <div class="bg-indigo-500/10 p-4 rounded-xl border border-indigo-500/30 text-sm text-left">
                {item.get('dimension', 'No details available.')}
            </div>
            <button onclick="askAI(true)" class="mt-4 text-[11px] text-gray-500 underline hover:text-indigo-400 cursor-pointer">
                Not satisfied? Try another answer →
            </button>
        </div>
    '''
    return jsonify({"reply": reply})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
  
