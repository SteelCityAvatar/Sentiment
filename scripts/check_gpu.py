import torch
from transformers import pipeline

def check_gpu_usage():
    """
    Verifies that PyTorch can see the GPU and that Hugging Face pipelines
    are correctly assigned to the GPU.
    """
    print("--- GPU Verification ---")
    
    # 1. Check if PyTorch sees the GPU
    if torch.cuda.is_available():
        print("✅ PyTorch reports CUDA is available.")
        gpu_count = torch.cuda.device_count()
        print(f"   - Found {gpu_count} GPU(s).")
        for i in range(gpu_count):
            print(f"   - GPU {i}: {torch.cuda.get_device_name(i)}")
    else:
        print("❌ PyTorch reports CUDA is NOT available. The pipeline will run on the CPU.")
        return

    # 2. Check the device used by a pipeline
    try:
        print("\n--- Pipeline Device Check ---")
        # Initialize one of the pipelines from the project
        # The device is an attribute of the pipeline object. device.type 'cuda' means GPU.
        ner_pipeline = pipeline("ner", model='dbmdz/bert-large-cased-finetuned-conll03-english')
        if ner_pipeline.device.type == 'cuda':
            print(f"✅ The NER pipeline is running on device: {ner_pipeline.device} (GPU)")
        else:
            print(f"⚠️ The NER pipeline is running on device: {ner_pipeline.device} (CPU)")

        sentiment_pipeline = pipeline("sentiment-analysis", model="mrm8488/distilroberta-finetuned-financial-news-sentiment-analysis")
        if sentiment_pipeline.device.type == 'cuda':
            print(f"✅ The Sentiment pipeline is running on device: {sentiment_pipeline.device} (GPU)")
        else:
            print(f"⚠️ The Sentiment pipeline is running on device: {sentiment_pipeline.device} (CPU)")
            
    except Exception as e:
        print(f"\nAn error occurred while checking the pipeline device: {e}")
        print("This might happen if the model weights need to be downloaded for the first time.")

if __name__ == "__main__":
    check_gpu_usage() 