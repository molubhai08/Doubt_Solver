# views.py
from django.shortcuts import render
from django.http import JsonResponse
from home.forms import PDFDocumentForm
from markdown import markdown
from django.http import HttpResponse
import os
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from io import StringIO
import re
from groq import Groq
from langchain_core.output_parsers import StrOutputParser
import base64
from langchain_core.messages import HumanMessage , SystemMessage

from django.shortcuts import redirect 

parser = StrOutputParser()




os.environ['GROQ_API_KEY'] = "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"

client = Groq(api_key=os.environ['GROQ_API_KEY'])

    
llm = ChatGroq(groq_api_key="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", model="llama3-70b-8192")

def home(request):

    request.session['history'] = ''

    if request.method == 'POST':
        form = PDFDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            pdf = form.save()
            request.session['file_url'] = pdf.file.url
            return redirect('process_file')  # name of your URL pattern
    return render(request, 'home/index.html', {'form': PDFDocumentForm()})

def pdf(request):
    file_url = request.session.get('file_url')
    if request.method == 'POST':
        base64_data = request.POST.get('base64')
        print("successfully received base64 string")

        # Remove common data URI prefixes
        if base64_data.startswith('data:image/png;base64,'):
            base64_data = base64_data.replace('data:image/png;base64,', '')
            mime_type = 'image/png'
        elif base64_data.startswith('data:image/jpeg;base64,'):
            base64_data = base64_data.replace('data:image/jpeg;base64,', '')
            mime_type = 'image/jpeg'
        elif base64_data.startswith('data:image/jpg;base64,'):
            base64_data = base64_data.replace('data:image/jpg;base64,', '')
            mime_type = 'image/jpg'
        else:
            # fallback or handle error
            mime_type = 'image/jpeg'  # default

        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text", 
                            "text": """Analyze this image thoroughly and provide:
                            
                            1. A summary of any text content in the image
                            2. Description of visual elements and layout of the image
                            3. Detailed transcription of any tables with their structure and data
                            4. Any charts, graphs, or diagrams with their key information
                            
                            Separate each section clearly in your response."""
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{base64_data}",
                            },
                        },
                    ],
                }
            ],
            model="meta-llama/llama-4-scout-17b-16e-instruct",
        )

    
        analysis = chat_completion.choices[0].message.content

        request.session['analysis'] = analysis

        print(analysis)
            

        

        return redirect('chat_bot')
    # Regular GET request: render template
    return render(request, 'home/pdf.html', context = {'file_url': file_url})

def chat(request):
    
    history = request.session.get('history')
    analysis = request.session.get('analysis')

    p = f"""You are a helpful assistant.

You have been provided with detailed image analysis data that includes:
1. Text summaries extracted from images
2. Descriptions of visual elements present in images
3. Transcriptions of tables from images
4. Interpretations of charts, graphs, and diagrams

image analysis = {analysis}

Be aware of the chat history and the context of the conversation.
chat history = {history}

Your primary role is to act as a doubt solver, helping users understand and utilize this information by:
- Drawing from the image analysis data to answer specific questions
- Explaining concepts related to the analyzed content
- Connecting information across different parts of the analysis
- Providing additional context when helpful
- Clarifying complex elements from the analyzed images

When responding to queries:
- Reference the relevant parts of the image analysis to support your answers
- Be precise about which elements of the analysis you're referring to
- Maintain a helpful, patient tone focused on resolving the user's doubts
- Ask clarifying questions when needed to better understand what specific information from the analysis would be most helpful

Ensure all interactions are respectful, informative, and focused on helping the user understand the content that has been analyzed from their images."""


    if request.method == 'POST':

        query = request.POST.get('query')

        

        messages = [
        SystemMessage(content=p),
        HumanMessage(content=query)
    ]
        result = llm.invoke(messages)
        result = parser.invoke(result)
        response = markdown(result)

        human_str = "human : " + str(query) + "\n"
        ai_str = "ai : " + str(response) + "\n"

        history = history + human_str + ai_str
        request.session['history'] = history

        return HttpResponse(response)




        

    

    return render(request, 'home/chat.html')

