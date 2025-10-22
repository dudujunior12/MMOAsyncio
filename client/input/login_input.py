import asyncio
from typing import Literal, Tuple, Any

async def get_auth_choice() -> Literal['L', 'R'] | None:
    """
    Displays the Login/Register menu and waits for the user's choice.
    Returns 'L' for Login, 'R' for Register, or None if the connection is closed.
    """
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

async def prompt_for_command() -> str:

    return await asyncio.get_event_loop().run_in_executor(None, input, "> ")

async def display_message(message: Any, is_system: bool = False):
    prefix = "[SYSTEM]" if is_system else "[CHAT]"
    print(f"\n{prefix} {message}\n> ", end='', flush=True)
