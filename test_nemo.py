#!/usr/bin/env python3
"""
Simple NeMo demonstration script
This shows basic NeMo functionality and available models
"""

import torch
import nemo

def main():
    print("=" * 50)
    print("NVIDIA NeMo Framework Demo")
    print("=" * 50)
    
    # Check system info
    print(f"NeMo version: {nemo.__version__}")
    print(f"PyTorch version: {torch.__version__}")
    print(f"CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"GPU: {torch.cuda.get_device_name(0)}")
        print(f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
    
    print("\n" + "=" * 50)
    print("Available NeMo Collections:")
    print("=" * 50)
    
    # Show available collections
    print("✓ ASR (Automatic Speech Recognition)")
    print("  - Convert speech to text")
    print("  - Models: Conformer, Citrinet, QuartzNet, etc.")
    
    print("\n✓ TTS (Text-to-Speech)")  
    print("  - Convert text to natural speech")
    print("  - Models: FastPitch, Tacotron2, WaveGlow, etc.")
    
    print("\n✓ NLP (Natural Language Processing)")
    print("  - Text classification, NER, QA, etc.")
    print("  - Models: BERT, RoBERTa, T5, GPT, etc.")
    
    print("\n✓ Multimodal")
    print("  - Vision-Language models")
    print("  - Image captioning, VQA, etc.")
    
    print("\n" + "=" * 50)
    print("What you can do with NeMo:")
    print("=" * 50)
    
    examples = [
        "🎤 Build speech recognition systems",
        "🗣️  Create text-to-speech applications", 
        "📝 Train language models for text generation",
        "🔍 Build chatbots and question-answering systems",
        "🎯 Fine-tune models on your own data",
        "⚡ Deploy models for production use",
        "🚀 Scale training across multiple GPUs",
        "🔧 Customize models with adapters and LoRA"
    ]
    
    for example in examples:
        print(f"  {example}")
    
    print("\n" + "=" * 50)
    print("Next Steps:")
    print("=" * 50)
    print("1. Check out the tutorials in NeMo/tutorials/")
    print("2. Try the Jupyter notebooks for hands-on examples")
    print("3. Download pre-trained models from NGC or Hugging Face")
    print("4. Start with simple inference before training")
    
    print(f"\nTutorial directories:")
    import os
    tutorial_dirs = [d for d in os.listdir('NeMo/tutorials') if os.path.isdir(f'NeMo/tutorials/{d}')]
    for dir_name in sorted(tutorial_dirs):
        print(f"  - NeMo/tutorials/{dir_name}/")

if __name__ == "__main__":
    main()
