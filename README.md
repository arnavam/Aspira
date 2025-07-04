```
conda create -n aspira1 python=3.11 -y
conda activate aspira1

conda install pytorch::pytorch -y
conda install SpeechRecognition -y          
conda install nltk -y                        
conda install yake -y
conda install beautifulsoup4 -y              
conda install conda-forge::transformers -y  
conda install conda-forge::gtts -y           
conda install conda-forge::pydub -y          
conda install conda-forge::opencv -y          
conda install conda-forge::librosa -y         
pip install git+https://github.com/elliottzheng/batch-face.git@master   
pip install pyMuPDF                         
conda install keybert -y
conda install spacy -y

conda install -c conda-forge textblob -y
conda install -c conda-forge textstat -y
conda install -c conda-forge wikipedia -y
conda install -c conda-forge wikipedia-api -y
conda install -c conda-forge flask-cors -y

python -m nltk.downloader -d stopwords punkt punkt_tab
python -m spacy download en_core_web_md
```

---

```
mamba create -n aspira1 python=3.11 -y
mamba activate aspira1

mamba install pytorch::pytorch -y
mamba install SpeechRecognition -y          
mamba install nltk -y                        
mamba install conda-forge::rake_nltk -y     
mamba install beautifulsoup4 -y              
mamba install conda-forge::transformers -y  
mamba install conda-forge::gtts -y           
mamba install conda-forge::pydub -y          
mamba install conda-forge::opencv -y          
mamba install conda-forge::librosa -y         

pip install git+https://github.com/elliottzheng/batch-face.git@master   
pip install pyMuPDF                         
pip install duckduckgo-search

mamba install keybert -y
mamba install spacy -y

mamba install textblob -y
mamba install textstat -y
mamba install wikipedia -y
mamba install wikipedia-api -y
mamba install flask-cors -y

python -m nltk.downloader -d stopwords punkt punkt_tab
python -m spacy download en_core_web_md
```
---
```
conda remove -n aspira1 --all
conda clean --all

```
---

conda env update --file environment.yml  --prune

""

Start-Process -FilePath "C:\Users\ARAV\miniconda3\Uninstall-Miniconda3.exe" -ArgumentList "/S", "/RemoveCaches=1", "/RemoveConfigFiles=all", "/RemoveUserData=1" -Wait


