import gradio as gr
from fastapi import FastAPI, Request
import requests, time, logging
API_KEY = "04P6iV05fXEeWCtMeAqc3b5CHXGqT1Jr"   # Replace with your API key
BRAND_ID = "68903bb1c7bf7c84edf79256"        # Replace with your brand_id from Predis
BASE_URL = "https://brain.predis.ai/predis_api/v1"
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
completed_results = {}
fastapi_app = FastAPI()
@fastapi_app.post("/webhook")
async def predis_webhook(request: Request):
    """Webhook endpoint for Predis.ai"""
    data = await request.json()
    logging.info(f"Webhook hit: {data}")
    if data["status"] == "completed":
        post_id = data["post_id"]
        image_url = data["generated_media"][0]["url"]
        completed_results[post_id] = image_url
        logging.info(f"✅ Poster ready for post_id {post_id}: {image_url}")
    elif data["status"] == "error":
        completed_results[data["post_id"]] = "error"
        logging.error(f"❌ Poster generation failed for post_id {data['post_id']}")
    return {"ok": True}
def generate_poster(prompt):
    """Trigger Predis.ai API to create poster and wait for webhook result"""
    payload = {
        "brand_id": BRAND_ID,
        "text": prompt,
        "media_type": "single_image"
    }
    headers = {"Authorization": API_KEY}
    logging.info(f"📤 Sending request to Predis for text: {prompt}")
    response = requests.post(f"{BASE_URL}/create_content/", json=payload, headers=headers)
    data = response.json()
    if "post_ids" not in data:
        logging.error(f"API Error: {data}")
        return "⚠️ API error. Check your credentials or brand_id."
    post_id = data["post_ids"][0]
    logging.info(f"Predis responded with post_id: {post_id}")
    for i in range(20):  # ~60 seconds max (20 x 3s)
        if post_id in completed_results:
            result = completed_results.pop(post_id)
            if result == "error":
                return "❌ Poster generation failed!"
            return result
        logging.info(f"⏳ Waiting for webhook (attempt {i+1}/20)...")
        time.sleep(3)
    return "⏳ Poster still processing... Please try again later."
with gr.Blocks() as demo:
    gr.Markdown("## 🎨 Predis.ai Poster Generator")
    with gr.Row():
        prompt = gr.Textbox(label="Enter Poster Text", placeholder="Type your message here...")
    output = gr.Image(label="Generated Poster", type="filepath")
    btn = gr.Button("Generate Poster")
    btn.click(fn=generate_poster, inputs=prompt, outputs=output)
app = gr.mount_gradio_app(fastapi_app, demo, path="/ui")
