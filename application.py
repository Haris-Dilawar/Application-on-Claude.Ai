from flask import Flask, render_template, request, redirect, url_for
from claude import claude_client, claude_wrapper
import pandas as pd
import json
import os
import warnings

warnings.simplefilter(action='ignore', category=FutureWarning)
app = Flask(__name__)

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    message = request.form['message']
    print(message)

    # Assuming the result.json is present in the folder "uploads"
    json_file_path = os.path.join('uploads', 'results.json')

    out_csv_path = transform(json_file_path, 'output.csv')
    response = answer('YOUR_API_KEY', out_csv_path, message)
    return render_template('results.html', response=json.dumps(response, indent=4))

def transform(json_file_path, out_csv_path):
    with open(json_file_path, 'r') as json_file:
        json_data = json.load(json_file)
    json_hits = json_data['hits']
    flattened_data = pd.json_normalize(json_hits)
    expanded_data = pd.DataFrame()
    for column in flattened_data.columns:
        if any(flattened_data[column].apply(lambda x: isinstance(x, list))):
            expanded_cols = flattened_data[column].apply(pd.Series)
            expanded_cols = expanded_cols.rename(columns=lambda x: f"{column}/{x}")
            expanded_data = pd.concat([expanded_data, expanded_cols], axis=1)
        else:
            expanded_data[column] = flattened_data[column]
    expanded_data.to_csv(out_csv_path, index=False)
    return out_csv_path

def answer(sessionkey, csv_file, message):
    client = claude_client.ClaudeClient(sessionkey)
    organizations = client.get_organizations()
    claude_obj = claude_wrapper.ClaudeWrapper(client, organization_uuid=organizations[0]['uuid'])
    new_conversation_data = claude_obj.start_new_conversation("New Conversation", "Hi Claude!")
    conversation_uuid = new_conversation_data['uuid']
    initial_response = new_conversation_data['response']
    chat_title = new_conversation_data['title']
    attachment = claude_obj.get_attachment(csv_file)
    response = claude_obj.send_message(message, attachments=[attachment], conversation_uuid=conversation_uuid)
    text = response['completion']
    print(text)
    return text

if __name__ == "__main__":
    app.run(host = "0.0.0.0")
