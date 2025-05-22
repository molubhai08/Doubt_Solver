# forms.py
from django import forms
from .models import PDFDocument

class PDFDocumentForm(forms.ModelForm):
    class Meta:
        model = PDFDocument
        fields = ['file']
