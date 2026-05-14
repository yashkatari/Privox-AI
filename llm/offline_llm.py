import ollama
import time

class OfflineLLM:
    def __init__(self, model_name="tinyllama"):
        """
        Initializes the offline LLM connector with Ollama.
        
        Args:
            model_name (str): The name of the offline model from 'ollama list',
                              e.g., "tinyllama", "phi-2", "qwen2.5:3b" (local)
        """
        
        print(f"[Offline LLM] Initializing Ollama connector for model: {model_name}")
        self.model_name = model_name
        
        # Try a test call to see if Ollama server is running
        try:
            ollama.list()
            print("[Offline LLM] Ollama server connection successful.")
        except Exception as e:
            print("[Offline LLM Error] Failed to connect to Ollama server.")
            print("[Offline LLM Error] Make sure Ollama is installed and running!")
            print("[Offline LLM Error] Run: ollama pull tinyllama")
            raise e

    def generate_response(self, user_text, system_prompt, stream=False):
        """
        Generates a response from the offline Ollama model.
        If stream=True, yields chunks of the response.
        """
        try:
            print("[Offline LLM] Generating response...")
            start_time = time.time()
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_text}
            ]
            
            # This calls the Ollama server locally
            if stream:
                response_stream = ollama.chat(
                    model=self.model_name,
                    messages=messages,
                    options={
                        'num_predict': 256  # Shorter responses for offline mode
                    },
                    stream=True
                )
                full_response = ""
                for chunk in response_stream:
                    if 'message' in chunk and 'content' in chunk['message']:
                        content = chunk['message']['content']
                        full_response += content
                        yield content  # Yield each chunk
                end_time = time.time()
                print(f"[Offline LLM] Response streamed in {end_time - start_time:.2f}s")
                return full_response
            else:
                response = ollama.chat(
                    model=self.model_name,
                    messages=messages,
                    options={
                        'num_predict': 256
                    }
                )
                
                end_time = time.time()
                print(f"[Offline LLM] Response generated in {end_time - start_time:.2f}s")
                
                return response['message']['content'].strip()

        except Exception as e:
            print(f"[Offline LLM Error] Failed to generate response: {e}")
            if stream:
                yield "I'm having trouble with the offline model. Please check if it's properly loaded."
            else:
                return "I'm having trouble with the offline model. Please check if it's properly loaded."

# --- Test the offline model ---
if __name__ == "__main__":
    
    # Test with tinyllama (should be pulled first: ollama pull tinyllama)
    test_llm = OfflineLLM("tinyllama")
    
    test_prompt = "You are PriVox, a helpful AI assistant. Keep responses brief."
    test_input = "What is 2+2?"
    
    print("\n--- OFFLINE TEST RUN ---")
    print(f"[USER] {test_input}")
    
    # Test streaming
    print("[LLM] Streaming response:")
    for chunk in test_llm.generate_response(test_input, test_prompt, stream=True):
        print(chunk, end='', flush=True)
    
    print("\n--- OFFLINE TEST END ---")