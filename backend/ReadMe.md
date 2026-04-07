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
