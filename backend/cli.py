import uuid
import json
import os
import concurrent.futures
from langchain_core.messages import HumanMessage, AIMessage

from utils.data_processing import evaluate_threshold
from utils.vector_search import find_matching_peer_group
from agents.listener import ListenerAgent
from agents.mapper import ClinicalMapperAgent

def run_cli():
    listener_agent = ListenerAgent()
    mapper_agent = ClinicalMapperAgent()
    
    session_id = str(uuid.uuid4())
    raw_history = []
    
    os.makedirs("session_logs", exist_ok=True)
    log_file = f"session_logs/{session_id}.json"
    
    with open(log_file, "w") as f:
        json.dump([], f)
        
    print("Initializing Kalpana 6.0 CLI with GPU Acceleration & Vector Search...")
    print(f"\nSession started [ID: {session_id}]")
    print("Type 'quit' or 'exit' to end the session.\n")
    print("=" * 60)
    
    while True:
        try:
            user_input = input("\nYou: ")
            if user_input.lower() in ['quit', 'exit']:
                print("\nEnding session. Goodbye!")
                break
            if not user_input.strip():
                continue

            langchain_history = []
            for msg in raw_history:
                if msg["role"] == "user":
                    langchain_history.append(HumanMessage(content=msg["content"]))
                else:
                    langchain_history.append(AIMessage(content=msg["content"]))
            
            langchain_history.append(HumanMessage(content=user_input))

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future_mapper = executor.submit(mapper_agent.analyze, user_input)
                
                print(f"\nKalpana: ", end="", flush=True)
                full_listener_response = ""
                
                for chunk in listener_agent.generate_stream(langchain_history):
                    print(chunk, end="", flush=True)
                    full_listener_response += chunk
                print("\n")

                profile = future_mapper.result()

            action = evaluate_threshold(profile, session_id)
            
            peer_group = None
            if profile.get("clinical_notes") and profile["clinical_notes"] != "Failed to parse clinical profile.":
                peer_group = find_matching_peer_group(profile["clinical_notes"])

            if action == "route_to_peer_group" and peer_group:
                group_msg = f"\n[SYSTEM ALERT]: Just so you know, I found {peer_group} that matches what you are feeling if you ever want to connect with others who understand."
                print(group_msg)
                full_listener_response += group_msg

            log_entry = {
                "user_input": user_input,
                "assistant_response": full_listener_response,
                "action": action,
                "peer_group_match": peer_group,
                "clinical_profile": profile
            }
            
            with open(log_file, "r") as f:
                logs = json.load(f)
                
            logs.append(log_entry)
            
            with open(log_file, "w") as f:
                json.dump(logs, f, indent=4)

            raw_history.append({"role": "user", "content": user_input})
            raw_history.append({"role": "assistant", "content": full_listener_response})

        except KeyboardInterrupt:
            print("\nEnding session. Goodbye!")
            break
        except Exception as e:
            print(f"\n[ERROR] An issue occurred during processing: {e}")

if __name__ == "__main__":
    run_cli()