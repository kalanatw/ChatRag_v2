import json
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from core.models import VectorDB


class Command(BaseCommand):
    help = 'Load paragraph chunks from a JSON file into the database'

    def handle(self, *args, **kwargs):
        json_file = os.path.join(settings.BASE_DIR, 'paragraph_chunks_update1.json')
        
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
                paragraph_chunks = data.get('paragraph_chunks', [])
                embeddings = data.get('embeddings', [])
                
                if not paragraph_chunks:
                    self.stdout.write(self.style.WARNING('No paragraph chunks found in JSON file'))
                if not embeddings:
                    self.stdout.write(self.style.WARNING('No embeddings found in JSON file'))
                
                entries = []
                for i, chunk in enumerate(paragraph_chunks):
                    # Debugging line to print chunk
                    self.stdout.write(self.style.SUCCESS(f"Processing chunk: {chunk}"))

                    # Safely extract values
                    page = chunk.get('page', 'Unknown')
                    text = chunk.get('text', 'No text')
                    pdf = chunk.get('pdf', 'No PDF')
                    
                    # Handle case where embeddings may not align with chunks
                    if i < len(embeddings) and len(embeddings[i]) == 1536:  #embedding dimension
                        vector = embeddings[i]
                    else:
                        vector = None  # Or handle it as you see fit

                    # Prepare an entry for bulk insertion
                    entry = VectorDB(
                        page=page,
                        text=text,
                        pdf=pdf,
                        embedding=vector
                    )
                    entries.append(entry)

                # Bulk create the entries
                VectorDB.objects.bulk_create(entries)

                self.stdout.write(self.style.SUCCESS('Successfully loaded paragraph chunks from JSON file'))
        
        except FileNotFoundError:
            self.stderr.write(self.style.ERROR(f'JSON file not found: {json_file}'))
        except json.JSONDecodeError:
            self.stderr.write(self.style.ERROR('Error decoding JSON file'))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Error loading paragraph chunks: {e}'))
