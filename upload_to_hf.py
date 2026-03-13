import os
from datasets import load_dataset
from huggingface_hub import login

def upload_dataset():
    # 1. Get the Hugging Face token from environment variables
    hf_token = os.environ.get("HF_TOKEN")
    if not hf_token:
        raise ValueError("HF_TOKEN environment variable is missing. Please add it to your GitHub Secrets.")

    # 2. Log in to Hugging Face
    login(token=hf_token)

    # 3. Define the path to your scraped data
    data_file = "data/gujarati_corpus.jsonl"
    if not os.path.exists(data_file):
        print(f"File {data_file} does not exist. The crawler might not have found any pages.")
        return

    # 4. Load the dataset from the JSONL file
    print("Loading dataset...")
    dataset = load_dataset("json", data_files=data_file, split="train")

    # 5. Push the dataset to the Hugging Face Hub
    # REPLACE 'your-hf-username/gujarati-news-corpus' with your actual HF username and desired dataset name
    repo_id = "neetmehta/GujaratiTextDataset"
    
    print(f"Pushing dataset to Hugging Face Hub at {repo_id}...")
    dataset.push_to_hub(repo_id)
    print("Upload complete!")

if __name__ == "__main__":
    upload_dataset()