# AI_Summarizer

The goal of this application is to provide users with efficient summarization of long texts, such as PDFs and news articles available on the Internet. Using advanced natural language processing models, the application provides both abstractive and extractive summarization options. It also includes a question-answering feature that allows users to query the summarized content. Finally, the summarized information can be saved as a PDF, meeting users' needs for easy storage and sharing.

#### Contents:
- [Analysis](#analysis)
  - [Scenario](#scenario)
  - [User Stories](#user-stories)
- [Requirements](#requirements)  


## Analysis

### Scenario

As a group, we had decided to build a simple Python program that uses a simple and understandable GUI (which will be built using PyQt5). With the decided use cases below, we decided to provide both abstractive and extractive summarization feature for new articles and uploaded pdfs. In our code, abstractive summarization is performed using the BART and Longformer model, which generates concise summaries by rephrasing the original text. And extractive summarization is performed using the TextRank algorithm, which identifies and extracts the most important sentences from the text.

### User Stories

1. As a user, I want to be able to quickly summarize a news article/ PDF document  to see what's important without having to read the whole thing.
2. As a user, I want to summarize long news articles so that I can quickly understand the main ideas and decide whether to continue reading.
3. As a user, I want to upload and summarize papers in PDF format to get an overview of the results.
4. As a user, I want to choose between abstractive and extractive summarization so that I can get either a rephrased summary or an extraction of key sentences based on my preference.
5. As a user, I want to extract answers to specific questions from news article/PDF document summaries so that I can quickly find information without having to search through the entire text.
6. As a user, I want the application to be simple and easy to use, with clear instructions for entering article URLs, uploading PDFs, asking questions, and viewing summaries and answers.
7. As a user, I want to be able to export the generated summary as a PDF file so that I can easily share it with colleagues or refer to it later.

## Requirements

To make the application easier to use, we have prepared a requirements.txt file that lists all the libraries and their versions needed to make the application work. For convenience, I have also listed them below.

pyqt5==5.15.10

requests==2.32.3

beautifulsoup4==4.12.3

transformers==4.44.0

torch==2.3.1

reportlab==4.2.2

PyMuPDF==1.24.7

nltk==3.8.1

numpy==1.26.4

networkx==3.3

scikit-learn==1.5.1

sentence-transformers==3.0.1

sentencepiece==0.2.0