#from transformers import GPT2LMHeadModel, GPT2Tokenizer
import torch
# tokenizer = BartTokenizer.from_pretrained("facebook/bart-large")
# model = BartForConditionalGeneration.from_pretrained("facebook/bart-large" )
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import time

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

tokenizer = AutoTokenizer.from_pretrained("p208p2002/bart-squad-qg-hl")
model = AutoModelForSeq2SeqLM.from_pretrained("p208p2002/bart-squad-qg-hl")
# tokenizer = AutoTokenizer.from_pretrained("p208p2002/t5-squad-qg-hl")
# model = AutoModelForSeq2SeqLM.from_pretrained("p208p2002/t5-squad-qg-hl")
# model=torch.jit.script(model).to_device(device)
model.eval()



def chatbot(input_text):
    start_time=time.time()
    input_ids = tokenizer.encode(input_text, return_tensors="pt").to(device)

    with torch.no_grad():  
        output_ids = model.generate(input_ids, max_length=100, num_return_sequences=1, no_repeat_ngram_size=2, top_p=0.95, top_k=60, temperature=0.7,do_sample=True)
    generated_text = tokenizer.decode(output_ids[0], skip_special_tokens=True)

    print(generated_text)
    print(time.time()-start_time)
    return generated_text

