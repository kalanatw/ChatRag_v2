from rest_framework import serializers
from core.models import ChatInstance

class ChatInstanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatInstance
        fields = ['id', 'twin_id', 'created_at']
        
class ChatHistoryItemSerializer(serializers.Serializer):
    user_query = serializers.CharField(help_text="The query sent by the user.")
    chatbot_response = serializers.CharField(help_text="The response from the chatbot.")

class ChatHistoryResponseSerializer(serializers.Serializer):
    chat_history = ChatHistoryItemSerializer(many=True, help_text="A list of chat history items.")
    
class OpenAIResponseContentSerializer(serializers.Serializer):
     content = serializers.CharField(
        help_text="The response content from OpenAI GPT-4 model.",
        default="The generated answer from RAG chatbot."
)

class OpenAIResponseSerializer(serializers.Serializer):
    openai_response = OpenAIResponseContentSerializer()
    
class DocumentSerializer(serializers.Serializer):
    pdf_id = serializers.CharField(help_text="The unique identifier for the PDF document.")
    pdf = serializers.CharField(help_text="The path or URL of the PDF document.")
    
class DocumentListResponseSerializer(serializers.Serializer):
    documents = DocumentSerializer(many=True, help_text="A list of all available documents.")

