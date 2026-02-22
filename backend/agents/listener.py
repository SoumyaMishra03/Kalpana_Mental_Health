# backend/agents/listener.py
from langchain_community.chat_models import ChatOllama
from langchain_core.messages import SystemMessage

class ListenerAgent:
    def __init__(self):
        self.llm = ChatOllama(
            model="qwen3:4b-instruct", 
            temperature=0.7,
            num_gpu=-1,  
            keep_alive=-1,
            num_ctx=2048,
            num_thread=8
        )
        self.system_prompt = SystemMessage(
            content=(
                "You are the user's absolute best friend and closest confidant. "
                "Your only goal is to deeply understand their pain, offer genuine emotional support, and help them feel truly heard. "
                "CRITICAL INSTRUCTIONS: "
                "1. Speak exactly like a highly empathetic, emotionally intelligent human best friend. Use a warm, intimate, and conversational tone. "
                "2. Ask gentle, open-ended questions to dig deeper into their feelings and explore the root of their struggles. "
                "3. Validate their emotions profoundly without jumping to fix things immediately. Make them feel safe. "
                "4. Keep responses very concise (1-3 sentences). "
                "5. NEVER offer medical advice, diagnoses, or recite helpline numbers (like Tele-MANAS). Focus ONLY on the friendship and listening."
            )
        )

    def generate_stream(self, history: list):
        prompt = [self.system_prompt] + history[-5:]
        for chunk in self.llm.stream(prompt):
            yield chunk.content