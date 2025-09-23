# AI_interviewer

this is an interviewr program which can be used to interviwe people i tried to manually implement this without using any tools like langchain or bigger llm models just a fine tuned bert.

## strength
- it creates question based on the answer you provided hence it sometimes comes questions that are interesting , hence can i used test all types of knwoledge
- its not high end model uses less rerouce and run very fast unless u use the 'converter.py' create which creates a vdeio that talks this task generaly take a lot of time
- fully open source and can be used your own need and there is nto rate limit


## weakness
- since used a small llm , it doesnt understand the situation or connects prevoius question to older question.. , just generate querstion even if you say 'hlo how are you'
- some times the duckduckgo api might reach the limit then you might to switch to other apis
- the question sometimes can be redundunt when the data which we get from duckduckgo is ireelveant,
- just use a sentence transformer to find the similarity hence maynot understand the context 
- the vdeio makeing is done using wav2lip which takes a large time upto 30 sec for each vedio creation hence that much lag if turned on

### notes;-
- to me this was a personal learning proejct , the aim was not to creation a high end product but the learn the inner working and behind the scenes of such large applications.

### to run this model you finst nned to setup a enviorment:-
- run ' conda env create -f requirements.yml && conda activate aspira1'
'
- if this doesnt work ( diff os has diff env files) use the requirment md file to manually install 

### after setting up enciourment 
- run 'python aspira.py' to setuyp backend 


