steps:

mkdir  sports-fingerprint
mkdir  backend
cd sports-fingerprint/backend    
python -m venv venv  
 venv\Scripts\Activate 
 ( New-Item requirements.txt )
 npm install    
 pip install git+https://github.com/openai/CLIP.git  
pip install -r requirements.txt    
playwright install chromium  / playwright install chromium --ignore-certificate-errors          

 to run:
   uvicorn main:app --reload --port 8000   (main)
  node node_modules/@angular/cli/bin/ng serve   


steps I followed for firebase:
------------------------------------
Step 1 — Go to [console.firebase.google.com](https://console.firebase.google.com/)
Step 2 — Click "Add project" → name it sports-fingerprint-backend → disable Google Analytics (optional) → Create
Step 3 — In your project, go to Firestore Database → Create database → Start in test mode → choose a region (e.g. us-east1) → Enable
Step 4 — Go to Project Settings (gear icon) → Service accounts tab → Click "Generate new private key" → Download the JSON file
Step 5 — Save that JSON file as:
backend/firebase-service-account.json

to enable firestore in cloud
------------------------------
Step 1 — Click this exact link:
https://console.developers.google.com/apis/api/firestore.googleapis.com/overview?project=sports-fingerprint-backend
Step 2 — Click the blue "Enable" button
Step 3 — Also check your service account has permission
Go to:
https://console.cloud.google.com/iam-admin/iam?project=sports-fingerprint-backend
create your service with name "sports-fingerprint-backend" or 
Find your service account email (it ends with @sports-fingerprint-backend.iam.gserviceaccount.com) and make sure it has the "Cloud Datastore User" or "Firebase Admin" or "Firebase Admin SDK Admisistrator service agent" role.

to enable vision api in cloud 
------------------------------
step 1 : click on 
https://console.cloud.google.com/apis/library/aiplatform.googleapis.com?project=sports-fingerprint-backend
Step 2 — Click the blue "Enable" button
Step 3 — Also check your service account has permission
