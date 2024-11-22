# mesop_gemini
This UI uses Cloud Run and Mesop to generate a frontend with direct connectivity to Vertex AI. 

# Deployment

For deployent, simply run gcloud cloud deploy , which will deploy fro source, install the necessary requirements, build the container, push it to Cloud Run, and run it using gunicorn for scaling. 

# Access Control

The service account used by the Cloud Run instance will require the roles/aiplatform.user as well as the roles/storage.objectCreator and roles/storage.objectViewer roles. 

# Procfile

The Procfile tells Google cloud which buildpack to use. ini the case of Python, it's a Gunicorn based build pack, which means the file serves the purpose of overriding the default gunicorn configuration with the one that links it to our Mesop app. # mesop_gemini
