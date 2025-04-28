from django.db import models
from django.contrib.postgres.fields import ArrayField
from pgvector.django import VectorField, HnswIndex

   
class VectorDB(models.Model):
    id = models.BigAutoField(primary_key=True)
    pdf_id = models.CharField(max_length=255,default="")
    page = models.CharField(max_length=255)
    text = models.TextField()
    pdf = models.CharField(max_length=255)
    embedding = VectorField(
        dimensions=1536,
        help_text="Vector embeddings of the pdf content",
        null=True,
        blank=True,
    )
    twin_id = models.CharField(max_length=255, default="b3e93609-1f8b-4628-b34e-197581450de3")
    twin_version_id = models.CharField(max_length=255, default="")
    meta_data = models.JSONField(default=list)
    type = models.CharField(max_length=255, default="document")
    asset_id = models.CharField(max_length=255, null=True, blank=True)
    integration_entity_id = models.UUIDField(null=True, blank=True)
    
    class Meta:
        indexes = [
            HnswIndex(
                name="pdf_content_embedding_index",
                fields=["embedding"],
                m=16,
                ef_construction=64,
                opclasses=["vector_cosine_ops"],
            )
        ]

class MetaDataAttributes(models.Model):
    meta_data_name = models.CharField(max_length=255)
    meta_data_format = models.JSONField()  
    meta_data_format_prompt = models.CharField(max_length=255)

    class Meta:
        db_table = 'meta_data_attributes' 
        
class ChatInstance(models.Model):
    id = models.BigAutoField(primary_key=True)
    twin_id = models.CharField(max_length=255) 
    created_at = models.DateTimeField(auto_now_add=True)  

    class Meta:
        db_table = 'chat_instance'
        
class ChatHistory(models.Model):
    id = models.BigAutoField(primary_key=True)
    chat_instance = models.ForeignKey(ChatInstance, related_name='messages', on_delete=models.CASCADE) 
    twin_id = models.CharField(max_length=255)
    user_query = models.CharField()
    chatbot_response = models.CharField() 
    class Meta:
        db_table = 'chat_history' 
        


        
def __str__(self):
    return f"Page {self.page}: {self.text[:50]}"
