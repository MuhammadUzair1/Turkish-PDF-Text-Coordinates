import PyPDF2
import fitz
import json
import re
from PIL import Image
from langchain.text_splitter import RecursiveCharacterTextSplitter
import os
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import google.generativeai as genai
from langchain_community.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv

load_dotenv()
os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

pattern = re.compile(r'\b\d+\.\s')

def read_file_in_chunks(file_path, chunk_size=1024):
    with open(file_path, 'r') as file:
        while True:
            chunk = file.read(chunk_size)
            if not chunk:
                break
            yield chunk

file_path = 'your_file.txt'
chunk_size = 1024  # Specify the size of each chunk in bytes

def get_turkish_words(user_question):

  prompt_template = """
  Extract the exact first and last 3 letters from the question you provide. The question should be related to Turkish exercises with options (like MCQs), answers, or descriptions.
If there are no questions, provide nothing.

Here is an example scenario:
Etkinlik Sahnesi
4
1
~ Çarpan Kavramı
Örnek:
24
1
2
3
4
24
12
8
6
.
.
.
.
1, 2, 3, 4, 6, 8, 12, 24
Örnek:
1. 28
2. 60
1. 48
3. 75
2. 36
4. 100
Aşağıda verilen doğal
sayıların pozitif tam sayı
çarpanlarını örnekteki gibi
bulunuz.
A
Aşağıda verilen doğal
sayıların pozitif tam sayı
çarpanlarını örnekteki gibi
bulunuz.
Aşağıda verilen soruları cevaplayınız.
1 2 3 4 6 8 12 24
4 . 6
3 . 8
2 . 12
1 . 24
24
1. 1, , 3, 6, , 18, 27, 54
2. , 2, 4, , 22, 44
3. 1, 2, , 8,
Aşağıda bazı sayıların pozitif
tam sayı çarpanlarının
küçükten büyüğe doğru sıralanışı
verildiğine göre boş
kutulara yazılması gereken
sayıları bulunuz.
C
B D
1. 225 sayısının en büyük ve en
küçük pozitif tam sayı çarpanlarının
toplamı kaçtır?
2. 49 sayısının pozitif tam sayı çarpanlarının
toplamı kaçtır?
3. 30 sayısının iki basamaklı pozitif
tam sayı çarpanlarının toplamı
kaçtır?
4. 18 sayısının pozitif tam sayı
çarpanlarından 3’ün bir tam sayı
katı olanların toplamı kaçtır?

Response should be like the following starting words of questions, ending words of questions
1. Aşağıda verilen doğal; 4. 100
2. Aşağıda verilen doğal; 2. 36
3. Aşağıda bazı sayıların; 3. 1, 2, , 8,
4. Aşağıda verilen soruları; olanların toplamı kaçtır?

**Please note:** This model is specifically designed for Turkish text and might not work well with other languages.

  Content:

  """

  model = genai.GenerativeModel("gemini-pro")

  # Recreate the PromptTemplate object each time
  prompt = PromptTemplate(template=prompt_template, input_variables=["question"])
  try:
    response = model.generate_content(prompt_template+user_question)
    return response

  except Exception as e:
    # Handle other potential exceptions
    print(f"Unexpected error: {e}")
    return "An error occurred. Please try again."

def extract_text_with_coordinates(pdf_path, text, page):
    # Open the PDF
    pdf_document = fitz.open(pdf_path)

    # Select the page
    page = pdf_document[page]

    # Search for the text
    text_instances = page.search_for(text)

    # Iterate through each instance
    for instance in text_instances:
        # Get the bounding box coordinates
        left = instance[0]
        top = instance[1]
        right = instance[2]
        bottom = instance[3]

        # Extract text from the specific area
        text = page.get_text("text", clip=instance)

        # Print coordinates and text
        return f"Coordinates: ({left}, {top}), ({right}, {bottom})"

    # Close the PDF
    pdf_document.close()

def extract_text_from_pdf(file_path):
    results = []

    try:
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)

            for page_num in range(len(reader.pages)):
                response = []
                page = reader.pages[page_num]
                page_text = page.extract_text()
                text = page_text.encode('utf-8', errors='ignore').decode('utf-8')

                ans = get_turkish_words(str(text))
                print(ans)
                response.append(ans.text)

                final_list = []
                for i in response:
                    split_sent = i.split("\n")
                    for j in split_sent:
                        split_text = j.split(';')
                        for k in split_text:
                            cleaned_text = re.sub(pattern, '', k)
                            text = cleaned_text.replace('\t', ' ').strip()
                            if text and text not in final_list:
                                final_list.append(text)

                # Check if the final_list has an odd length
                if len(final_list) % 2 != 0:
                    # Remove the last element
                    final_list.pop()

                # Iterate over the final_list in pairs
                for i in range(0, len(final_list), 2):
                    start = extract_text_with_coordinates(pdf_content, final_list[i], page_num)
                    end = extract_text_with_coordinates(pdf_content, final_list[i+1], page_num)

                    if start is not None and end is not None:
                        result = {
                            "id": len(results) + 1,
                            "start": start,
                            "end": end,
                            "page_number": page_num + 1,
                            "text": final_list[i]
                        }
                        results.append(result)
    except Exception as e:
        # Handle exceptions appropriately, e.g., log the error
        print("Error:", e)

    return results