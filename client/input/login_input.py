import asyncio
from typing import Dict, Literal, Tuple, Any

from shared.protocol import PACKET_CHAT_MESSAGE, PACKET_DAMAGE, PACKET_MOVE

async def get_auth_choice() -> Literal['L', 'R'] | None:
    prompt = "\nSelect an option:\n[L] Login\n[R] Register\n[Q] Quit\n> "
    choice = await asyncio.get_event_loop().run_in_executor(None, input, prompt)
    
    choice = choice.upper().strip()

    if choice == 'L' or choice == 'R':
        return choice
    elif choice == 'Q':
        return None
    else:
        print("\nOpção inválida. Tente novamente.")
        return await get_auth_choice()

async def get_credentials(is_register: bool) -> Tuple[str, str] | None:
    action = "Register" if is_register else "Login"
    print(f"\n--- {action} ---")
    
    try:
        username = await asyncio.get_event_loop().run_in_executor(
            None, input, "Username: "
        )
        if not username:
            print("Username cannot be empty.")
            return await get_credentials(is_register)
            
        password = await asyncio.get_event_loop().run_in_executor(
            None, input, "Password: "
        )
        if not password:
            print("Password cannot be empty.")
            return await get_credentials(is_register)

        return username.strip(), password.strip()
        
    except EOFError:
        return None

async def prompt_for_game_action() -> Dict[str, Any] | None:

    prompt = "\n[Ação] /move x y | [Chat] Mensagem | /quit\n> "
    
    try:
        raw_input = await asyncio.get_event_loop().run_in_executor(None, input, prompt)
        raw_input = raw_input.strip()
        
        if not raw_input:
            return {} # Pacote vazio, espera por mais entrada
        
        parts = raw_input.split()
        command = parts[0].lower()

        if command == '/quit':
            return None # Sinal para fechar a conexão
        
        if command == '/stats':
            # Envia /stats como um pacote de chat para o servidor processar como comando
            return {
                "type": PACKET_CHAT_MESSAGE, 
                "content": raw_input # Envia a string '/stats'
            }
            
        if command == '/damage':
            if len(parts) == 2:
                try:
                    target_entity_id = int(parts[1])
                    
                    return {
                        "type": PACKET_DAMAGE,
                        "target_entity_id": target_entity_id,
                    }
                except ValueError:
                    print("\nComando /damage inválido. Use: /damage <entity_id> (ID deve ser número inteiro).")
                    return {}
        else:
            print("\nComando /damage inválido. Use: /damage <entity_id>.")
            return {}

        if command == '/move':
            if len(parts) == 3:
                try:

                    x = float(parts[1])
                    y = float(parts[2])
                    
                    return {
                        "type": PACKET_MOVE,
                        "x": x,
                        "y": y
                    }
                except ValueError:
                    print("\nComando /move inválido. Use: /move <x> <y> (ambos devem ser números).")
                    return {}
            else:
                print("\nComando /move inválido. Use: /move <x> <y>.")
                return {}
        
        # Se não for um comando, trata como mensagem de chat
        return {
            "type": PACKET_CHAT_MESSAGE,
            "content": raw_input
        }
        
    except EOFError:
        return None

async def display_message(message: Any, is_system: bool = False):
    prefix = "[SYSTEM]" if is_system else "[CHAT]"
    print(f"\n{prefix} {message}\n> ", end='', flush=True)
