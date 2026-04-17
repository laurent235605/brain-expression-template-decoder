import requests
import json
import time
from datetime import datetime
import os
from pathlib import Path
import getpass
import sys

from ace_lib import set_alpha_properties


DESCRIPTION_MIN_LENGTH = 100
DEFAULT_LLM_BASE_URL = 'https://api.moonshot.cn/v1'

# Platform specific imports
if sys.platform == 'win32':
    import msvcrt
else:
    import tty
    import termios


def _credentials_file_path():
    return Path.home() / 'secrets' / 'platform-brain.json'


def load_saved_credentials():
    """Load saved credentials from env vars or the shared platform credential file."""
    env_email = (os.environ.get('BRAIN_CREDENTIAL_EMAIL') or '').strip()
    env_password = (os.environ.get('BRAIN_CREDENTIAL_PASSWORD') or '').strip()
    if env_email and env_password:
        return env_email, env_password, 'env'

    credentials_path = _credentials_file_path()
    if credentials_path.exists() and credentials_path.stat().st_size > 2:
        try:
            data = json.loads(credentials_path.read_text(encoding='utf-8'))
        except (OSError, json.JSONDecodeError):
            data = {}
        email = str(data.get('email') or '').strip()
        password = str(data.get('password') or '').strip()
        if email and password:
            return email, password, str(credentials_path)

    return '', '', ''


def save_credentials(email, password):
    """Persist credentials so the submitter can reuse them next time."""
    credentials_path = _credentials_file_path()
    credentials_path.parent.mkdir(parents=True, exist_ok=True)
    credentials_path.write_text(
        json.dumps({'email': email, 'password': password}, ensure_ascii=False, indent=2),
        encoding='utf-8',
    )


def prompt_for_credentials(default_email=''):
    """Prompt for credentials, optionally reusing the current email as default."""
    print("\n=== WorldQuant Brain Login ===")
    email_prompt = f"Enter your email [{default_email}]: " if default_email else "Enter your email: "
    email_input = input(email_prompt).strip()
    email = email_input or default_email

    try:
        password = input_with_asterisks("Enter your password: ")
        if not password:
            print("❌ Password is required.")
            return '', ''
    except Exception as e:
        print(f"❌ Error with custom password input: {e}")
        print("Trying standard getpass...")
        try:
            password = getpass.getpass("Enter your password: ")
            if not password:
                print("❌ Password is required.")
                return '', ''
        except Exception as e2:
            print(f"❌ Error reading password: {e2}")
            return '', ''

    if not email:
        print("❌ Email is required.")
        return '', ''

    return email, password

def input_with_asterisks(prompt):
    """Cross-platform password input showing asterisks"""
    print(prompt, end='', flush=True)
    password = []

    try:
        if sys.platform == 'win32':
            # Windows: Use msvcrt.getch()
            while True:
                char = msvcrt.getch()
                
                # Handle Enter key
                if char in [b'\r', b'\n']:
                    print()  # New line
                    break
                
                # Handle Backspace
                elif char == b'\x08':  # Backspace
                    if password:
                        password.pop()
                        # Move cursor back, print space, move cursor back again
                        print('\b \b', end='', flush=True)
                
                # Handle Ctrl+C
                elif char == b'\x03':  # Ctrl+C
                    print()
                    raise KeyboardInterrupt
                
                # Handle printable characters (ASCII)
                elif 32 <= ord(char) <= 126:  # Printable ASCII range
                    password.append(char.decode('ascii'))
                    print('*', end='', flush=True)
                
                # Handle extended characters
                else:
                    try:
                        decoded_char = char.decode('utf-8')
                        if decoded_char.isprintable():
                            password.append(decoded_char)
                            print('*', end='', flush=True)
                    except UnicodeDecodeError:
                        continue
        else:
            # Unix/macOS: Use tty and termios
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(fd)
                while True:
                    char = sys.stdin.read(1)
                    
                    # Handle Enter key
                    if char in ['\r', '\n']:
                        print('\r\n', end='', flush=True)
                        break
                    
                    # Handle Backspace
                    elif char in ['\x7f', '\x08']:
                        if password:
                            password.pop()
                            print('\b \b', end='', flush=True)
                    
                    # Handle Ctrl+C
                    elif char == '\x03':
                        print('\r\n', end='', flush=True)
                        raise KeyboardInterrupt
                    
                    # Handle printable characters
                    elif char.isprintable():
                        password.append(char)
                        print('*', end='', flush=True)
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
                
    except Exception as e:
        # Fallback to getpass
        print(f"\nError reading password: {e}")
        print("Falling back to getpass...")
        return getpass.getpass()

    return ''.join(password)


def prompt_required_line(prompt):
    """Prompt until the user provides a non-empty single-line value."""
    while True:
        value = input(prompt).strip()
        if value:
            return value
        print("❌ This field is required.")


def _llm_config_file_paths():
    """Return known config files that may contain LLM connection settings."""
    script_dir = Path(__file__).resolve().parent
    return [
        script_dir.parent / 'Tranformer' / 'transformer_config.json',
        script_dir.parent.parent / 'AI桌面插件' / 'config.json',
    ]


def _pick_non_empty(mapping, keys, default=''):
    """Pick the first non-empty string value from a mapping."""
    for key in keys:
        value = mapping.get(key)
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return default


def _looks_like_placeholder(value):
    """Filter out obvious sample or placeholder secrets/config values."""
    normalized = str(value or '').strip().lower()
    if not normalized:
        return True
    placeholder_markers = [
        'xxxxx',
        'your_api_key',
        'your_moonshot_key',
        'sk-xxx',
        '<your',
        'changeme',
    ]
    return any(marker in normalized for marker in placeholder_markers)


def load_llm_settings():
    """Load LLM connection settings from env vars or known config files."""
    env_settings = {
        'api_key': _pick_non_empty(os.environ, ['MOONSHOT_API_KEY', 'LLM_API_KEY', 'OPENAI_API_KEY']),
        'base_url': _pick_non_empty(os.environ, ['MOONSHOT_BASE_URL', 'LLM_BASE_URL', 'OPENAI_BASE_URL'], DEFAULT_LLM_BASE_URL),
        'model': _pick_non_empty(os.environ, ['MOONSHOT_MODEL', 'LLM_MODEL_NAME', 'OPENAI_MODEL']),
    }
    if env_settings['api_key'] and env_settings['model'] and not _looks_like_placeholder(env_settings['api_key']):
        return {**env_settings, 'source': 'env'}

    for config_path in _llm_config_file_paths():
        if not config_path.exists():
            continue
        try:
            config = json.loads(config_path.read_text(encoding='utf-8'))
        except (OSError, json.JSONDecodeError):
            continue

        settings = {
            'api_key': _pick_non_empty(config, ['moonshot_api_key', 'api_key', 'LLM_API_KEY']),
            'base_url': _pick_non_empty(config, ['moonshot_base_url', 'base_url', 'llm_base_url'], DEFAULT_LLM_BASE_URL),
            'model': _pick_non_empty(config, ['moonshot_model', 'model', 'LLM_model_name']),
        }
        if settings['api_key'] and settings['model'] and not _looks_like_placeholder(settings['api_key']):
            return {**settings, 'source': str(config_path)}

    return None


def build_description_text(idea, data_rationale, operator_rationale):
    """Build the required three-line description template."""
    return "\n".join([
        f"Idea: {idea}",
        f"Rationale for data used: {data_rationale}",
        f"Rationale for operators used: {operator_rationale}",
    ])


def _extract_llm_text(completion):
    """Extract plain text content from an OpenAI-compatible completion."""
    message = completion.choices[0].message
    content = message.content
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict) and item.get('type') == 'text' and item.get('text'):
                parts.append(str(item['text']))
        return ''.join(parts).strip()
    return str(content).strip()


def _create_llm_description_completion(client, llm_settings, expression, section_name):
    """Create a description completion for OpenAI-style providers."""
    return client.chat.completions.create(
        model=llm_settings['model'],
        messages=[
            {
                'role': 'system',
                'content': (
                    'You write WorldQuant BRAIN alpha descriptions. '
                    'Return valid JSON only with keys idea, data_rationale, operator_rationale. '
                    'Each value must be plain text without markdown. '
                    'The combined final three-line template must be at least 100 characters long.'
                ),
            },
            {
                'role': 'user',
                'content': (
                    f'Section: {section_name}\n'
                    f'Expression:\n{expression}\n\n'
                    'Generate these three fields based only on the expression:\n'
                    '1. idea\n2. data_rationale\n3. operator_rationale'
                ),
            },
        ],
        response_format={'type': 'json_object'},
    )


def _extract_required_description_fields(payload):
    """Extract and validate the three required BRAIN description fields."""
    required_keys = ['idea', 'data_rationale', 'operator_rationale']
    missing_keys = [key for key in required_keys if key not in payload]
    if missing_keys:
        raise ValueError(f"LLM response missing required keys: {', '.join(missing_keys)}")

    extracted = {}
    empty_keys = []
    for key in required_keys:
        value = str(payload.get(key) or '').strip()
        extracted[key] = value
        if not value:
            empty_keys.append(key)

    if empty_keys:
        raise ValueError(f"LLM response contains empty required fields: {', '.join(empty_keys)}")

    return extracted


def generate_description_with_llm(expression, section_name='alpha'):
    """Use configured LLM settings to generate the required three-line description."""
    llm_settings = load_llm_settings()
    if llm_settings is None:
        return None

    try:
        import openai

        client = openai.OpenAI(api_key=llm_settings['api_key'], base_url=llm_settings['base_url'])
        completion = _create_llm_description_completion(client, llm_settings, expression, section_name)
        content = _extract_llm_text(completion)
        payload = json.loads(content)
        fields = _extract_required_description_fields(payload)
        description = build_description_text(
            fields['idea'],
            fields['data_rationale'],
            fields['operator_rationale'],
        )
        if len(description) < DESCRIPTION_MIN_LENGTH:
            print(
                f"⚠️ LLM-generated description is too short: {len(description)} characters "
                f"from {llm_settings['source']}"
            )
            return None

        print(f"✅ Generated description with LLM ({llm_settings['source']})")
        print(description)
        return description
    except Exception as error:
        print(f"⚠️ LLM description generation failed: {error}")
        return None


def get_description_template(expression, section_name='alpha'):
    """Prefer LLM-generated descriptions and fall back to manual prompting."""
    generated = generate_description_with_llm(expression, section_name)
    if generated is not None:
        return generated
    return prompt_description_template(section_name)


def _extract_alpha_expression(alpha_data, field_name):
    """Extract the expression text for a specific alpha component."""
    value = alpha_data.get(field_name)
    if isinstance(value, dict):
        return str(value.get('code') or value.get('expression') or '').strip()
    return str(value or '').strip()


def prompt_description_template(section_name='alpha'):
    """Collect a description using the required three-line template."""
    print(f"\n=== Description Required for {section_name} ===")
    while True:
        print(f"Description must be at least {DESCRIPTION_MIN_LENGTH} characters in total.")
        idea = prompt_required_line("Idea: ")
        data_rationale = prompt_required_line("Rationale for data used: ")
        operator_rationale = prompt_required_line("Rationale for operators used: ")
        description = build_description_text(idea, data_rationale, operator_rationale)
        current_length = len(description)
        remaining = DESCRIPTION_MIN_LENGTH - current_length
        if remaining <= 0:
            print(f"Description length: {current_length} characters.")
            return description

        print(
            f"❌ Description is too short: {current_length} characters. "
            f"Add at least {remaining} more characters and try again."
        )


def patch_alpha_description(s, alpha_id, alpha_data):
    """Patch the alpha description before submit using the required template."""
    alpha_type = str(alpha_data.get('type') or 'REGULAR').upper()

    try:
        if alpha_type == 'SUPER':
            selection_expression = _extract_alpha_expression(alpha_data, 'selection')
            combo_expression = _extract_alpha_expression(alpha_data, 'combo')
            selection_desc = get_description_template(selection_expression, 'selection')
            combo_desc = get_description_template(combo_expression, 'combo')
            response = set_alpha_properties(
                s,
                alpha_id,
                selection_desc=selection_desc,
                combo_desc=combo_desc,
            )
        else:
            regular_expression = _extract_alpha_expression(alpha_data, 'regular')
            regular_desc = get_description_template(regular_expression, 'regular alpha')
            response = set_alpha_properties(s, alpha_id, regular_desc=regular_desc)

        print(f"Description patch response status: {response.status_code}")
        if response.text:
            try:
                print(f"Description patch response body: {json.dumps(response.json(), indent=2)}")
            except json.JSONDecodeError:
                print(f"Description patch response body (not JSON): {response.text}")

        response.raise_for_status()
        print(f"✅ Description patched for alpha {alpha_id}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to patch description for alpha {alpha_id}: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Patch error response status: {e.response.status_code}")
            print(f"Patch error response body: {e.response.text}")
        return False

def _attempt_login(email, password, source_label='manual'):
    """Attempt login with the provided credentials."""
    s = requests.Session()
    s.auth = (email, password)

    try:
        response = s.post('https://api.worldquantbrain.com/authentication')
        print(f"Login response status: {response.status_code}")
        print(f"Login response headers: {dict(response.headers)}")

        if response.text:
            try:
                response_json = response.json()
                print(f"Login response body: {json.dumps(response_json, indent=2)}")
            except json.JSONDecodeError:
                print(f"Login response body (not JSON): {response.text}")

        response.raise_for_status()
        print(f"Login successful! (source: {source_label})")
        return s
    except requests.exceptions.RequestException as e:
        print(f"Login failed using {source_label}: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Error response status: {e.response.status_code}")
            print(f"Error response body: {e.response.text}")
        return None


def login(account_choice=None, force_prompt=False):
    """Login to WorldQuant Brain API, preferring saved credentials when available."""
    del account_choice

    saved_email, saved_password, source = load_saved_credentials()
    if not force_prompt and saved_email and saved_password:
        print("\n=== WorldQuant Brain Login ===")
        print(f"Trying saved credentials for: {saved_email}")
        session = _attempt_login(saved_email, saved_password, source)
        if session is not None:
            return session
        print("Saved credentials login failed. Falling back to manual input.")

    email, password = prompt_for_credentials(saved_email if force_prompt else '')
    if not email or not password:
        return None

    print(f"Logging in with: {email}")
    session = _attempt_login(email, password, 'manual')
    if session is not None:
        try:
            save_credentials(email, password)
        except OSError as save_error:
            print(f"Warning: failed to persist credentials: {save_error}")
    return session

def check_alpha_exists(s, alpha_id):
    """Check if an alpha exists by making a GET request to /alphas/<alpha_id>"""
    try:
        response = s.get(f"https://api.worldquantbrain.com/alphas/{alpha_id}")
        print(f"Alpha check response status: {response.status_code}")
        print(f"Alpha check response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            alpha_data = response.json()
            print(f"✅ Alpha {alpha_id} exists - Type: {alpha_data.get('type', 'Unknown')}")
            print(f"Alpha data: {json.dumps(alpha_data, indent=2)}")
            return True, alpha_data
        elif response.status_code == 404:
            print(f"❌ Alpha {alpha_id} does not exist (404 Not Found)")
            if response.text:
                print(f"404 response body: {response.text}")
            return False, None
        else:
            print(f"⚠️ Unexpected response for alpha {alpha_id}: {response.status_code}")
            if response.text:
                print(f"Unexpected response body: {response.text}")
            return False, None
    except requests.exceptions.RequestException as e:
        print(f"❌ Error checking alpha {alpha_id}: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Error response status: {e.response.status_code}")
            print(f"Error response body: {e.response.text}")
        return False, None

def get_alpha_recordsets(s, alpha_id):
    """Get available record sets for an alpha"""
    try:
        response = s.get(f"https://api.worldquantbrain.com/alphas/{alpha_id}/recordsets")
        print(f"Recordsets response status: {response.status_code}")
        print(f"Recordsets response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            recordsets_data = response.json()
            print(f"📊 Alpha {alpha_id} has {recordsets_data.get('count', 0)} record sets available")
            print(f"Recordsets data: {json.dumps(recordsets_data, indent=2)}")
            return recordsets_data
        else:
            print(f"⚠️ Could not fetch record sets for alpha {alpha_id}: {response.status_code}")
            if response.text:
                print(f"Recordsets error response body: {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching record sets for alpha {alpha_id}: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Error response status: {e.response.status_code}")
            print(f"Error response body: {e.response.text}")
        return None

def submit(s, alpha_id):
    """Submit a single alpha with retry logic - keeps trying until success"""
    
    def submit_inner(s, alpha_id):
        """Inner submit function with rate limiting handling"""
        try:
            result = s.post(f"https://api.worldquantbrain.com/alphas/{alpha_id}/submit")
            print(f"Alpha submit, alpha_id={alpha_id}, status_code={result.status_code}")
            print(f"Response headers: {dict(result.headers)}")
            
            # Handle rate limiting
            while True:
                if "retry-after" in result.headers:
                    wait_time = float(result.headers["Retry-After"])
                    print(f"Rate limited, waiting {wait_time} seconds...")
                    time.sleep(wait_time)
                    result = s.get(f"https://api.worldquantbrain.com/alphas/{alpha_id}/submit")
                    print(f"Retry GET response, status_code={result.status_code}")
                    print(f"Retry headers: {dict(result.headers)}")
                else:
                    break
            
            return result
        except Exception as e:
            print(f'Connection error: {e}, attempting to re-login...')
            new_session = login()
            if new_session is None:
                return None
            return submit_inner(new_session, alpha_id)
    
    attempt_count = 1
    result = None
    
    while True:
        print(f"Submit attempt {attempt_count} for alpha {alpha_id}")
        result = submit_inner(s, alpha_id)
        
        if result is None:
            print(f"Failed to submit {alpha_id} - connection error")
            return None
        
        if result.status_code == 200:
            print(f"✅ Alpha {alpha_id} submit successful, status_code={result.status_code}")
            return result
        elif result.status_code == 403:
            print(f"❌ Alpha {alpha_id} submit forbidden, status_code={result.status_code}")
            return result
        else:
            print(f"⚠️ Alpha submit fail, status_code={result.status_code}, alpha_id={alpha_id}, attempt {attempt_count}")
            print(f"Waiting 2 minutes before retry...")
            time.sleep(120)  # 2 minutes = 120 seconds
            attempt_count += 1
            continue

def submit_alpha(alpha_id, session=None, account_choice=None):
    """Submit a single alpha with comprehensive error handling"""
    if session is None:
        s = login(account_choice)
        if s is None:
            return False
    else:
        s = session
    
    # First check if the alpha exists
    print(f"Checking if alpha {alpha_id} exists...")
    exists, alpha_data = check_alpha_exists(s, alpha_id)
    if not exists:
        print(f"❌ Cannot submit alpha {alpha_id} - it does not exist")
        return False

    if not patch_alpha_description(s, alpha_id, alpha_data):
        print(f"❌ Cannot submit alpha {alpha_id} - failed to patch description")
        return False
    
    # Submit the alpha
    res = submit(s, alpha_id)
    
    if res is None:
        print(f"Failed to submit {alpha_id} - connection error")
        return False
    
    # Parse response
    if res.text:
        try:
            res_json = res.json()
            print(f"Submit response parsed successfully")
        except json.JSONDecodeError:
            print(f"Submit response is not JSON: {res.text[:200]}...")
            return False
    else:
        print(f"Submit response has no text content")
        return False
    
    # Check for various error conditions
    if 'detail' in res_json and res_json['detail'] == 'Not found.':
        print(f"{alpha_id} - Alpha ID not found")
        return False
    
    # Check submission status
    submitted = True
    if 'is' in res_json and 'checks' in res_json['is']:
        for item in res_json['is']['checks']:
            if item['name'] == 'ALREADY_SUBMITTED':
                submitted = False
                print(f"{alpha_id} - Already submitted")
                break
            if item['result'] == 'FAIL':
                submitted = False
                print(f"{alpha_id} - {item['name']} check failed, limit = {item['limit']}, value = {item['value']}")
                break
    
    if submitted:
        print(f'{alpha_id} - Submission successful!')
        return True
    else:
        return False

def main():
    """Main function to run the alpha submission script"""
    print("=== WorldQuant Brain Alpha Submitter ===")
    print("This script will help you submit alphas with automatic retry logic.")
    print("It will first try the system-saved WorldQuant Brain credentials, then fall back to manual input if needed.\n")
    
    # Login with user credentials
    session = login()
    if session is None:
        print("Failed to login. Exiting.")
        return
    
    print("\n=== Alpha Submission Mode ===")
    print("Enter alpha IDs one by one. Type 'quit' to exit.")
    print("Type 'relogin' to login with different credentials.")
    print("Type 'info <alpha_id>' to check alpha details before submitting.")
    
    while True:
        alpha_id = input("\nEnter alpha ID (or 'quit' to exit, 'relogin' to change credentials): ").strip()
        
        if alpha_id.lower() == 'quit':
            print("Goodbye!")
            break
        
        if alpha_id.lower() == 'relogin':
            print("\nRe-logging in...")
            session = login(force_prompt=True)
            if session is None:
                print("Failed to login. Exiting.")
                return
            continue
        
        if alpha_id.lower().startswith('info '):
            info_alpha_id = alpha_id[5:].strip()
            if not info_alpha_id:
                print("Please provide an alpha ID after 'info'")
                continue
            
            print(f"\nChecking details for alpha: {info_alpha_id}")
            print("=" * 50)
            
            # Check if alpha exists
            exists, alpha_data = check_alpha_exists(session, info_alpha_id)
            if exists:
                # Get record sets
                get_alpha_recordsets(session, info_alpha_id)
                
                # Show some basic alpha info
                if alpha_data:
                    print(f"📋 Alpha Details:")
                    print(f"   ID: {alpha_data.get('id', 'N/A')}")
                    print(f"   Type: {alpha_data.get('type', 'N/A')}")
                    if 'settings' in alpha_data:
                        print(f"   Has settings: Yes")
                    if 'regular' in alpha_data:
                        print(f"   Has regular data: Yes")
                    if 'combo' in alpha_data:
                        print(f"   Has combo data: Yes")
                    if 'selection' in alpha_data:
                        print(f"   Has selection data: Yes")
            
            print("=" * 50)
            continue
        
        if not alpha_id:
            print("Please enter a valid alpha ID.")
            continue
        
        print(f"\nSubmitting alpha: {alpha_id}")
        print("=" * 50)
        
        success = submit_alpha(alpha_id, session)
        
        if success:
            print(f"✅ Alpha {alpha_id} processed successfully!")
        else:
            print(f"❌ Alpha {alpha_id} failed to submit properly.")
        
        print("=" * 50)

if __name__ == "__main__":
    main() 