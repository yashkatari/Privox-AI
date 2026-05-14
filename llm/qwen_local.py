import ollama
import time

class QwenLLM:
    def __init__(self, model_name):
        """
        Initializes the LLM connector with the Ollama model name.
        
        Args:
            model_name (str): The name of the model from 'ollama list',
                              e.g., "qwen2.5:3b"
        """
        
        print(f"[LLM] Initializing Ollama connector for model: {model_name}")
        self.model_name = model_name
        
        # Try a test call to see if Ollama server is running
        try:
            ollama.list()
            print("[LLM] Ollama server connection successful.")
        except Exception as e:
            print("[LLM Error] Failed to connect to Ollama server.")
            print("[LLM Error] PLEASE MAKE SURE THE OLLAMA SERVER IS RUNNING!")
            raise e

    def generate_response(self, user_text, system_prompt, stream=False):
        """
        Generates a response from the Ollama model.
        If stream=True, yields chunks of the response.
        """
        try:
            print("[LLM] Generating response...")
            start_time = time.time()
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_text}
            ]
            
            # This calls the Ollama server
            # Reduce max prediction length to improve responsiveness.
            # If you want longer answers, increase this value, but expect higher latency.
            if stream:
                response_stream = ollama.chat(
                    model=self.model_name,
                    messages=messages,
                    options={
                        'num_predict': 512
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
                print(f"[LLM] Response streamed in {end_time - start_time:.2f}s")
                return full_response  # Return full for non-streaming compatibility
            else:
                response = ollama.chat(
                    model=self.model_name,
                    messages=messages,
                    options={
                        'num_predict': 512
                    }
                )
                
                end_time = time.time()
                print(f"[LLM] Response generated in {end_time - start_time:.2f}s")
                
                # The response format from ollama is a dictionary
                return response['message']['content'].strip()
        except Exception as e:
            print(f"[LLM Error] Failed to generate response: {e}")
            print("[LLM Error] Make sure the Ollama server is running!")
            if stream:
                yield "Sorry, I'm having a bit of trouble connecting to my brain right now."
            else:
                return "Sorry, I'm having a bit of trouble connecting to my brain right now."

    def generate(self, prompt: str) -> str:
        """Compatibility alias expected by other modules: calls `generate_response` with a simple system prompt."""
        system_prompt = "You are a helpful assistant. Keep answers concise."
        return self.generate_response(prompt, system_prompt, stream=False)

# --- Example Test (if you run this file directly) ---
if __name__ == "__main__":
    
    # This is the name from your 'ollama list'
    YOUR_MODEL_NAME = "qwen2.5:3b" 
    
    try:
        test_llm = QwenLLM(YOUR_MODEL_NAME)
        
        test_prompt = "You are a helpful assistant. Keep it brief."
        test_input = "Hello, what is the capital of France?"
        
        print("\n--- TEST RUN ---")
        print(f"[USER] {test_input}")
        response = test_llm.generate_response(test_input, test_prompt)
        print(f"[LLM] {response}")
        print("--- TEST END ---")
        
    except Exception as e:
        print(f"Failed to run test. Is your Ollama server running?")