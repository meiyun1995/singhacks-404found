import base64
import pymupdf

from groq import Groq
from dotenv import load_dotenv


load_dotenv()


client = Groq()
model = 'meta-llama/llama-4-scout-17b-16e-instruct'

system_prompt = """
You are tasked with analyzing and processing a set of images to ensure they meet quality, formatting, and authenticity standards.
Create a detailed report summarizing the findings, outlining the issues, risks, and any corrective actions needed.

You need to perform the following tasks:
- Extract the text, metadata, and structural information from the document.
- Evaluate the document for completeness and accuracy.
- Check the document structure and formatting for consistency (e.g., no double-spacing, correct font, consistent indentation).
- Check the document for the following:
    - Formatting issues: Detect double spacing, irregular fonts, or inconsistent indentation.
    - Content errors: Identify spelling mistakes, incorrect headers, or missing sections.
    - Structure issues: Verify that the document follows the correct organizational format and that all necessary sections are present.
    - Template Matching: Compare the document structure with the provided standard template and flag discrepancies.
- Risk Assessment: Calculate the risk score for each image based on factors such as formatting consistency, content accuracy, authenticity, and structural integrity.
- Provide real-time feedback to compliance officers, highlighting any issues or potential risks.
"""

zoom_matrix = pymupdf.Matrix(0.5, 0.5)
doc = pymupdf.open("data/Swiss_Home_Purchase_Agreement_Scanned_Noise_forparticipants.pdf")
for page in doc:
    pix = page.get_pixmap(matrix = zoom_matrix)  
    pix.save("data/Swiss_Home_Purchase_Agreement_Scanned_Noise_forparticipants.png") 

with open("data/Swiss_Home_Purchase_Agreement_Scanned_Noise_forparticipants.png", "rb") as f:
    image_data = base64.b64encode(f.read()).decode("utf-8")

chat_completion = client.chat.completions.create(
    messages=[
        {
            "role": "system",
            "content": system_prompt,
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{image_data}",
                    },
                },
            ],
        }
    ],
    model=model,
)

print(chat_completion.choices[0].message.content)