import google.generativeai as genai

genai.configure(api_key="AIzaSyDrxMRoQ-Knm7gM_6YNHAiPhXoC6HN09S4")

for model in genai.list_models():
    print(model)